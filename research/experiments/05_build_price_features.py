"""Generate audited technical and historical research features."""

from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research.price_collector import price_file_name
from src.research.price_features import build_price_features


def main():
    targets = pd.read_csv(
        PROJECT_ROOT / "data/interim/research/targets.csv",
        parse_dates=["observation_date", "target_date"],
    )

    records = []
    failures = []

    for symbol, observations in targets.groupby("symbol", sort=False):
        prices = pd.read_csv(
            PROJECT_ROOT
            / "data/raw/research/prices"
            / price_file_name(symbol),
            index_col="Date",
            parse_dates=["Date"],
        )

        successful = 0

        for row in observations.itertuples(index=False):
            try:
                features = build_price_features(
                    prices, row.observation_date
                )
                features["symbol"] = symbol
                records.append(features)
                successful += 1
            except Exception as error:
                failures.append(
                    {
                        "symbol": symbol,
                        "observation_date": row.observation_date,
                        "error": str(error),
                    }
                )

        print(
            f"{symbol:<15} features={successful}/{len(observations)}"
        )

    report_directory = PROJECT_ROOT / "research/results"
    report_directory.mkdir(parents=True, exist_ok=True)

    failure_report = pd.DataFrame(
        failures,
        columns=["symbol", "observation_date", "error"],
    )
    failure_report.to_csv(
        report_directory / "price_feature_failures.csv",
        index=False,
        date_format="%Y-%m-%d",
        lineterminator="\n",
    )

    if failures:
        raise RuntimeError(
            f"{len(failures)} feature rows failed. "
            "Inspect research/results/price_feature_failures.csv."
        )

    features = pd.DataFrame(records)

    if features.duplicated(["symbol", "observation_date"]).any():
        raise ValueError("Duplicate feature rows.")

    dataset = targets.merge(
        features,
        on=["symbol", "observation_date"],
        how="left",
        validate="one_to_one",
    )

    if dataset["feature_window_end"].isna().any():
        raise ValueError("Some observations have no features.")

    if not (
        dataset["feature_window_end"] == dataset["observation_date"]
    ).all():
        raise ValueError("Feature cutoff mismatch.")

    destination = PROJECT_ROOT / "data/processed/research"
    destination.mkdir(parents=True, exist_ok=True)

    dataset.to_csv(
        destination / "price_features.csv",
        index=False,
        date_format="%Y-%m-%d",
        lineterminator="\n",
    )

    summary = (
        dataset.groupby(["market", "split"], sort=False)
        .agg(
            observations=("symbol", "size"),
            eligible=("eligible", "sum"),
            technical_available=("technical_is_available", "sum"),
            minimum_history_rows=("history_rows", "min"),
        )
        .reset_index()
    )

    summary.to_csv(
        report_directory / "price_feature_summary.csv",
        index=False,
        lineterminator="\n",
    )

    print("\nFeature summary")
    print(summary.to_string(index=False))
    print(f"\nTotal feature rows: {len(dataset)}")
    print("Failed rows: 0")
    print(f"Saved to: {destination / 'price_features.csv'}")


if __name__ == "__main__":
    main()