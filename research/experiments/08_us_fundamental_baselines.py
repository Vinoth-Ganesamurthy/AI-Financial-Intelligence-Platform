"""Compare US price and SEC fundamental features on validation only."""

import hashlib
import json
from pathlib import Path
import platform
import runpy

import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
PRICE_INPUT = ROOT / "data/processed/research/price_features.csv"
SEC_INPUT = ROOT / "data/interim/research/sec_annual_features.csv"
OUTPUT = ROOT / "research/results/us_fundamental_baselines"

# Reuse the established feature list and metric definitions.
baseline = runpy.run_path(
    str(ROOT / "research/experiments/06_price_baselines.py")
)
PRICE_FEATURES = baseline["FEATURES"]
LABELS = baseline["LABELS"]
calculate_metrics = baseline["metrics"]

FUNDAMENTAL_FEATURES = [
    "profit_margin",
    "return_on_equity",
    "return_on_assets",
    "revenue_growth",
    "earnings_growth",
    "free_cash_flow_to_revenue",
]


def make_model(kind):
    steps = [
        (
            "imputer",
            SimpleImputer(strategy="median", add_indicator=True),
        ),
    ]

    if kind == "logistic_regression":
        steps.extend([
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    C=1.0,
                    class_weight="balanced",
                    max_iter=3000,
                    random_state=42,
                ),
            ),
        ])
    elif kind == "random_forest":
        steps.append((
            "model",
            RandomForestClassifier(
                n_estimators=300,
                max_depth=6,
                min_samples_leaf=20,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ),
        ))
    else:
        raise ValueError(f"Unknown model: {kind}")

    return Pipeline(steps)


def main():
    prices = pd.read_csv(PRICE_INPUT)
    sec = pd.read_csv(SEC_INPUT)
    keys = ["symbol", "observation_date"]

    for frame in (prices, sec):
        frame["observation_date"] = pd.to_datetime(
            frame["observation_date"], errors="raise"
        ).dt.strftime("%Y-%m-%d")

        if frame.duplicated(keys).any():
            raise ValueError("Duplicate symbol/date keys.")

    # Exclude holdout rows before merging or calculating features.
    prices = prices.loc[
        prices["market"].eq("United States")
        & prices["eligible"].eq(True)
        & prices["split"].isin(["train", "validation"])
    ].copy()

    sec = sec.loc[
        sec["split"].isin(["train", "validation"])
    ].copy()

    data = prices.merge(
        sec,
        on=keys,
        how="left",
        validate="one_to_one",
        suffixes=("", "_sec"),
        indicator=True,
    )

    if not data["_merge"].eq("both").all():
        raise ValueError("Some price observations have no SEC row.")

    if not data["split"].eq(data["split_sec"]).all():
        raise ValueError("Price and SEC split assignments disagree.")

    if not data["eligible"].eq(data["eligible_sec"]).all():
        raise ValueError("Price and SEC eligibility flags disagree.")

    observation_dates = pd.to_datetime(data["observation_date"])
    filing_dates = pd.to_datetime(
        data["latest_component_filing_date"], errors="raise"
    )
    period_ends = pd.to_datetime(
        data["statement_period_end"], errors="raise"
    )

    if filing_dates.isna().any() or period_ends.isna().any():
        raise ValueError("Missing SEC availability dates.")

    if not filing_dates.lt(observation_dates).all():
        raise ValueError("SEC filing is not before observation.")

    if not period_ends.lt(observation_dates).all():
        raise ValueError("Statement period is not before observation.")

    # Normalize cash flow instead of using company-size dollar amounts.
    revenue = pd.to_numeric(data["total_revenue"], errors="raise")
    cash_flow = pd.to_numeric(data["free_cash_flow"], errors="raise")
    data["free_cash_flow_to_revenue"] = (
        cash_flow / revenue.where(revenue > 0)
    )

    train = data.loc[data["split"].eq("train")].copy()
    validation = data.loc[data["split"].eq("validation")].copy()

    if train.empty or validation.empty:
        raise ValueError("Training and validation rows are required.")

    if not data["target_class"].isin(LABELS).all():
        raise ValueError("Invalid target classes.")

    y_train = train["target_class"]
    y_validation = validation["target_class"]

    feature_sets = {
        "price_only": PRICE_FEATURES,
        "price_plus_fundamentals": (
            PRICE_FEATURES + FUNDAMENTAL_FEATURES
        ),
    }

    results = []
    prediction_frames = []
    model_settings = {}

    def record_result(name, predicted):
        results.append({
            "model": name,
            "split": "validation",
            "market": "United States",
            "rows": len(validation),
            "prediction_coverage": 1.0,
            **calculate_metrics(y_validation, predicted),
        })

        rows = validation[
            ["symbol", "market", "observation_date", "target_class"]
        ].copy()
        rows["model"] = name
        rows["prediction"] = predicted
        prediction_frames.append(rows)

    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(np.zeros((len(train), 1)), y_train)
    record_result(
        "majority_class",
        dummy.predict(np.zeros((len(validation), 1))),
    )

    for feature_set, columns in feature_sets.items():
        x_train = train[columns].apply(
            pd.to_numeric, errors="raise"
        ).replace([np.inf, -np.inf], np.nan)

        x_validation = validation[columns].apply(
            pd.to_numeric, errors="raise"
        ).replace([np.inf, -np.inf], np.nan)

        missing = x_train.columns[x_train.isna().all()].tolist()
        if missing:
            raise ValueError(
                f"Entirely missing training features: {missing}"
            )

        for kind in ("logistic_regression", "random_forest"):
            name = f"{kind}_{feature_set}"
            model = make_model(kind)
            model.fit(x_train, y_train)
            record_result(name, model.predict(x_validation))
            model_settings[name] = repr(model)

    OUTPUT.mkdir(parents=True, exist_ok=True)

    report = pd.DataFrame(results)
    report.to_csv(OUTPUT / "validation_metrics.csv", index=False)

    pd.concat(prediction_frames, ignore_index=True).to_csv(
        OUTPUT / "validation_predictions.csv", index=False
    )

    metadata = {
        "purpose": "US SEC fundamentals validation comparison",
        "training_rows": len(train),
        "validation_rows": len(validation),
        "test_evaluated": False,
        "feature_sets": feature_sets,
        "seed": 42,
        "python": platform.python_version(),
        "sklearn": sklearn.__version__,
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "price_input_sha256": hashlib.sha256(
            PRICE_INPUT.read_bytes()
        ).hexdigest(),
        "sec_input_sha256": hashlib.sha256(
            SEC_INPUT.read_bytes()
        ).hexdigest(),
        "baseline_script_sha256": hashlib.sha256(
            (ROOT / "research/experiments/06_price_baselines.py")
            .read_bytes()
        ).hexdigest(),
        "models": model_settings,
    }

    (OUTPUT / "experiment_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print(f"US training rows: {len(train)}")
    print(f"US validation rows: {len(validation)}")
    print("\nValidation results")
    print(
        report.sort_values("macro_f1", ascending=False)
        .to_string(index=False)
    )
    print("\n2025 test predictions have not been evaluated.")
    print(f"Reports saved to: {OUTPUT}")


if __name__ == "__main__":
    main()