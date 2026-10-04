"""Compare US price and SEC fundamental features on test only."""

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
OUTPUT = ROOT / "research/results/final_holdout/us"
MACRO_INPUT = ROOT / "data/interim/research/us_macro_features.csv"

MACRO_FEATURES = [
    "inflation_rate",
    "monetary_rate",
    "gdp_growth_rate",
    "unemployment_rate",
]

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
        & prices["split"].isin(["train", "test"])
    ].copy()

    sec = sec.loc[
        sec["split"].isin(["train", "test"])
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

    # Join only development rows; validation rows are excluded.
    macro = pd.read_csv(MACRO_INPUT)
    macro["observation_date"] = pd.to_datetime(
        macro["observation_date"], errors="raise"
    ).dt.strftime("%Y-%m-%d")

    if macro.duplicated(keys).any():
        raise ValueError("Duplicate macro symbol/date keys.")

    macro = macro.loc[
        macro["split"].isin(["train", "test"])
    ].copy()

    macro = macro[
        keys + [
            "split", "eligible", "macro_vintage_date",
            "macro_source",
        ] + MACRO_FEATURES
    ].rename(columns={
        "split": "macro_split",
        "eligible": "macro_eligible",
    })

    data = data.drop(columns="_merge").merge(
        macro,
        on=keys,
        how="left",
        validate="one_to_one",
        indicator="_macro_merge",
    )

    if not data["_macro_merge"].eq("both").all():
        raise ValueError("Some observations have no macro row.")

    if not data["split"].eq(data["macro_split"]).all():
        raise ValueError("Macro split assignments disagree.")

    if not data["eligible"].eq(data["macro_eligible"]).all():
        raise ValueError("Macro eligibility flags disagree.")

    expected_vintage = (
        pd.to_datetime(data["observation_date"])
        - pd.Timedelta(days=1)
    )
    actual_vintage = pd.to_datetime(
        data["macro_vintage_date"], errors="raise"
    )

    if not actual_vintage.eq(expected_vintage).all():
        raise ValueError("Macro vintage is not the preceding day.")

    train = data.loc[data["split"].eq("train")].copy()
    test = data.loc[data["split"].eq("test")].copy()

    if train.empty or test.empty:
        raise ValueError("Training and test rows are required.")

    if not data["target_class"].isin(LABELS).all():
        raise ValueError("Invalid target classes.")

    y_train = train["target_class"]
    y_test = test["target_class"]

    feature_sets = {
        "price_only": PRICE_FEATURES,
        "price_plus_fundamentals": (
            PRICE_FEATURES + FUNDAMENTAL_FEATURES
        ),
        "price_plus_fundamentals_plus_macro": (
            PRICE_FEATURES + FUNDAMENTAL_FEATURES + MACRO_FEATURES
        ),
    }

    results = []
    prediction_frames = []
    model_settings = {}

    def record_result(name, predicted):
        results.append({
            "model": name,
            "split": "test",
            "market": "United States",
            "rows": len(test),
            "prediction_coverage": 1.0,
            **calculate_metrics(y_test, predicted),
        })

        rows = test[
            ["symbol", "market", "observation_date", "target_class"]
        ].copy()
        rows["model"] = name
        rows["prediction"] = predicted
        prediction_frames.append(rows)

    dummy = DummyClassifier(strategy="most_frequent")
    dummy.fit(np.zeros((len(train), 1)), y_train)
    record_result(
        "majority_class",
        dummy.predict(np.zeros((len(test), 1))),
    )

    for feature_set, columns in feature_sets.items():
        x_train = train[columns].apply(
            pd.to_numeric, errors="raise"
        ).replace([np.inf, -np.inf], np.nan)

        x_test = test[columns].apply(
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
            record_result(name, model.predict(x_test))
            model_settings[name] = repr(model)

    OUTPUT.mkdir(parents=True, exist_ok=True)

    report = pd.DataFrame(results)
    report.to_csv(OUTPUT / "test_metrics.csv", index=False)

    pd.concat(prediction_frames, ignore_index=True).to_csv(
        OUTPUT / "test_predictions.csv", index=False
    )

    metadata = {
        "purpose": "US price, fundamentals, and macro test comparison",
        "macro_input_sha256": hashlib.sha256(
            MACRO_INPUT.read_bytes()
        ).hexdigest(),
        "training_rows": len(train),
        "test_rows": len(test),
        "test_evaluated": True,
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
    print(f"US test rows: {len(test)}")
    print("\nValidation results")
    print(
        report.sort_values("macro_f1", ascending=False)
        .to_string(index=False)
    )
    print("\n2025 holdout predictions evaluated with frozen settings.")
    print(f"Reports saved to: {OUTPUT}")


if __name__ == "__main__":
    main()