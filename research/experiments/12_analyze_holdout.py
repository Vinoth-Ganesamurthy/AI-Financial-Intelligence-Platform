"""Analyze saved holdout predictions without retraining any model."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research.evaluation import (
    LABELS,
    classification_metrics,
    paired_block_bootstrap,
)


INPUT = ROOT / "research/results/final_holdout"
OUTPUT = ROOT / "research/results/holdout_analysis"

COMPARISONS = {
    "price": [
        ("random_forest", "majority_class"),
    ],
    "us": [
        (
            "random_forest_price_plus_fundamentals",
            "random_forest_price_only",
        ),
        (
            "random_forest_price_plus_fundamentals_plus_macro",
            "random_forest_price_plus_fundamentals",
        ),
    ],
}


def load_predictions(experiment):
    path = INPUT / experiment / "test_predictions.csv"
    data = pd.read_csv(path)

    required = [
        "symbol", "market", "observation_date",
        "target_class", "model", "prediction",
    ]
    if not set(required).issubset(data.columns):
        raise ValueError(f"Missing prediction columns: {experiment}")

    data["observation_date"] = pd.to_datetime(
        data["observation_date"], errors="raise"
    ).dt.strftime("%Y-%m-%d")

    dates = pd.to_datetime(data["observation_date"])
    if not dates.dt.year.eq(2025).all():
        raise ValueError("Predictions contain observations outside 2025.")

    keys = ["symbol", "observation_date"]
    if data.duplicated(keys + ["model"]).any():
        raise ValueError("Duplicate model predictions.")

    consistency = data.groupby(keys)[
        ["market", "target_class"]
    ].nunique(dropna=False)

    if not consistency.eq(1).all().all():
        raise ValueError("Models disagree on row metadata.")

    base = (
        data[keys + ["market", "target_class"]]
        .drop_duplicates(keys)
        .sort_values(keys)
        .reset_index(drop=True)
    )

    # Chronological ordinal within each company's holdout observations.
    base["round"] = base.groupby("symbol").cumcount()

    wide = data.pivot(
        index=keys,
        columns="model",
        values="prediction",
    )
    index = pd.MultiIndex.from_frame(base[keys])
    wide = wide.reindex(index)

    if wide.isna().any().any():
        raise ValueError("Models do not cover identical observations.")

    predictions = {
        name: wide[name].to_numpy()
        for name in wide.columns
    }

    for values in predictions.values():
        classification_metrics(base["target_class"], values)

    return path, base, predictions


def main():
    metrics_rows = []
    confusion_rows = []
    count_rows = []
    interval_rows = []
    input_hashes = {}

    for experiment in ("price", "us"):
        path, base, predictions = load_predictions(experiment)
        input_hashes[experiment] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()

        expected = 490 if experiment == "price" else 120
        if len(base) != expected:
            raise ValueError(
                f"{experiment}: expected {expected} observations, "
                f"found {len(base)}."
            )

        scopes = [("overall", np.ones(len(base), dtype=bool))]
        scopes.extend(
            (market, base["market"].eq(market).to_numpy())
            for market in sorted(base["market"].unique())
        )

        for scope, mask in scopes:
            actual = base.loc[mask, "target_class"].to_numpy()

            for label in LABELS:
                count_rows.append({
                    "experiment": experiment,
                    "scope": scope,
                    "target_class": label,
                    "count": int((actual == label).sum()),
                    "rows": len(actual),
                })

            for name, predicted in predictions.items():
                result = classification_metrics(
                    actual, predicted[mask]
                )
                matrix = result.pop("confusion_matrix")

                metrics_rows.append({
                    "experiment": experiment,
                    "scope": scope,
                    "model": name,
                    "rows": len(actual),
                    **result,
                })

                for i, actual_label in enumerate(LABELS):
                    for j, predicted_label in enumerate(LABELS):
                        confusion_rows.append({
                            "experiment": experiment,
                            "scope": scope,
                            "model": name,
                            "actual": actual_label,
                            "predicted": predicted_label,
                            "count": matrix[i][j],
                        })

        print(
            f"Bootstrapping {experiment}: "
            f"{len(base)} rows, "
            f"{base['round'].nunique()} rounds...",
            flush=True,
        )

        intervals = paired_block_bootstrap(
            base["target_class"].to_numpy(),
            predictions,
            base["round"].to_numpy(),
            comparisons=COMPARISONS[experiment],
            replicates=2000,
            block_length=3,
            seed=42,
        )

        interval_rows.extend(
            {"experiment": experiment, **row}
            for row in intervals
        )

    OUTPUT.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(metrics_rows).to_csv(
        OUTPUT / "metrics.csv", index=False
    )
    pd.DataFrame(confusion_rows).to_csv(
        OUTPUT / "confusion_matrices.csv", index=False
    )
    pd.DataFrame(count_rows).to_csv(
        OUTPUT / "class_counts.csv", index=False
    )

    intervals = pd.DataFrame(interval_rows)
    intervals.to_csv(
        OUTPUT / "bootstrap_intervals.csv", index=False
    )

    metadata = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "prediction_input_hashes": input_hashes,
        "analysis_script_sha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        "evaluation_module_sha256": hashlib.sha256(
            (ROOT / "src/research/evaluation.py").read_bytes()
        ).hexdigest(),
        "protocol_sha256": hashlib.sha256(
            (ROOT / "research/FINAL_EVALUATION_PROTOCOL.md")
            .read_bytes()
        ).hexdigest(),
        "replicates": 2000,
        "block_length": 3,
        "seed": 42,
        "retrained_models": False,
        "interval_method": (
            "Paired moving-block bootstrap over company "
            "observation ordinals; percentile 95% intervals"
        ),
        "limitations": (
            "Few holdout rounds and differing market calendars; "
            "intervals are approximate and descriptive."
        ),
    }

    (OUTPUT / "analysis_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    differences = intervals.loc[
        intervals["kind"].eq("macro_f1_difference")
    ]

    print("\nPaired macro-F1 differences and 95% intervals")
    print(differences[
        ["experiment", "name", "estimate", "lower_95", "upper_95"]
    ].to_string(index=False))
    print(f"\nReports saved to: {OUTPUT}")


if __name__ == "__main__":
    main()