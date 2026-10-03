"""Compare fixed price baselines on training and test data only."""

import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data/processed/research/price_features.csv"
OUTPUT = ROOT / "research/results/final_holdout/price"

FEATURES = [
    "technical_rsi",
    "technical_relative_volume",
    "price_to_sma_20",
    "price_to_sma_50",
    "price_to_sma_200",
    "ema_spread",
    "macd_pct",
    "macd_histogram_pct",
    "bollinger_position",
    "atr_pct",
    "price_range_position",
    "historical_one_week_return",
    "historical_one_month_return",
    "historical_three_month_return",
    "historical_six_month_return",
    "historical_one_year_return",
    "historical_annualized_volatility",
    "historical_maximum_drawdown",
]

LABELS = ["favourable", "neutral", "unfavourable"]


def classify_scores(scores):
    scores = np.asarray(scores, dtype=float)
    return np.where(
        scores >= 0.2,
        "favourable",
        np.where(scores <= -0.2, "unfavourable", "neutral"),
    )


def metrics(actual, predicted):
    return {
        "macro_f1": f1_score(
            actual,
            predicted,
            labels=LABELS,
            average="macro",
            zero_division=0,
        ),
        "balanced_accuracy": balanced_accuracy_score(actual, predicted),
        "accuracy": accuracy_score(actual, predicted),
    }


def main():
    data = pd.read_csv(INPUT)

    required = FEATURES + [
        "split", "eligible", "target_class",
        "technical_module_score", "historical_module_score",
    ]
    missing = sorted(set(required) - set(data.columns))
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Validation rows are excluded from the holdout evaluation.
    development = data.loc[
        data["eligible"].eq(True)
        & data["split"].isin(["train", "test"])
    ].copy()

    train = development.loc[development["split"].eq("train")]
    test = development.loc[
        development["split"].eq("test")
    ]

    if train.empty or test.empty:
        raise ValueError("Training and test rows are required.")

    if not development["target_class"].isin(LABELS).all():
        raise ValueError("Invalid or missing target classes.")

    x_train = train[FEATURES].replace([np.inf, -np.inf], np.nan)
    x_test = test[FEATURES].replace(
        [np.inf, -np.inf], np.nan
    )
    y_train = train["target_class"]
    y_test = test["target_class"]

    if x_train.isna().all().any():
        raise ValueError("A selected feature is entirely missing in training.")

    models = {
        "majority_class": DummyClassifier(strategy="most_frequent"),
        "logistic_regression": Pipeline(
            [
                ("imputer", SimpleImputer(
                    strategy="median", add_indicator=True
                )),
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(
                    C=1.0,
                    class_weight="balanced",
                    max_iter=3000,
                    random_state=42,
                )),
            ]
        ),
        "random_forest": Pipeline(
            [
                ("imputer", SimpleImputer(
                    strategy="median", add_indicator=True
                )),
                ("model", RandomForestClassifier(
                    n_estimators=300,
                    max_depth=6,
                    min_samples_leaf=20,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=-1,
                )),
            ]
        ),
    }

    predictions = {}

    # Score availability is respected. If all inputs are unavailable,
    # the prediction defaults to neutral and its coverage is reported.
    score_columns = {
        "technical_only": ["technical_module_score"],
        "historical_only": ["historical_module_score"],
        "equal_weight_price": [
            "technical_module_score", "historical_module_score"
        ],
    }

    coverage = {}
    for name, columns in score_columns.items():
        scores = test[columns].mean(axis=1, skipna=True)
        coverage[name] = float(scores.notna().mean())
        predictions[name] = classify_scores(scores.fillna(0))

    for name, model in models.items():
        model.fit(x_train, y_train)
        predictions[name] = model.predict(x_test)
        coverage[name] = 1.0

    results = []
    prediction_rows = []

    for name, predicted in predictions.items():
        results.append(
            {
                "model": name,
                "split": "test",
                "rows": len(test),
                "prediction_coverage": coverage[name],
                **metrics(y_test, predicted),
            }
        )

        for market in test["market"].unique():
            mask = test["market"].eq(market).to_numpy()
            results.append(
                {
                    "model": name,
                    "split": f"test:{market}",
                    "rows": int(mask.sum()),
                    "prediction_coverage": (
                        float(
                            test.loc[mask, score_columns[name]]
                            .notna().any(axis=1).mean()
                        )
                        if name in score_columns else 1.0
                    ),
                    **metrics(y_test.iloc[np.flatnonzero(mask)],
                              np.asarray(predicted)[mask]),
                }
            )

        rows = test[
            ["symbol", "market", "observation_date", "target_class"]
        ].copy()
        rows["model"] = name
        rows["prediction"] = predicted
        prediction_rows.append(rows)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = pd.DataFrame(results)
    report.to_csv(OUTPUT / "test_metrics.csv", index=False)

    pd.concat(prediction_rows, ignore_index=True).to_csv(
        OUTPUT / "test_predictions.csv", index=False
    )

    metadata = {
        "purpose": "Price-only development benchmark; not the full model",
        "training_rows": len(train),
        "test_rows": len(test),
        "test_evaluated": True,
        "features": FEATURES,
        "score_thresholds": [-0.2, 0.2],
        "seed": 42,
        "python": platform.python_version(),
        "sklearn": sklearn.__version__,
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "models": {
            name: repr(model) for name, model in models.items()
        },
    }
    (OUTPUT / "experiment_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    overall = report.loc[report["split"].eq("test")]
    print("\nValidation results")
    print(overall.sort_values("macro_f1", ascending=False).to_string(
        index=False
    ))
    print("\n2025 holdout results evaluated with frozen settings.")
    print(f"Reports saved to: {OUTPUT}")


if __name__ == "__main__":
    main()