"""Build audited observations and targets for all research companies."""

from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research.config import EXPECTED_COMPANY_COUNT
from src.research.price_collector import price_file_name
from src.research.targets import build_targets


def main():
    universe = pd.read_csv(
        PROJECT_ROOT / "research/company_universe.csv"
    )

    if (
        len(universe) != EXPECTED_COMPANY_COUNT
        or universe["symbol"].duplicated().any()
    ):
        raise ValueError("Expected 40 unique company symbols.")

    frames = []

    for row in universe.itertuples(index=False):
        path = (
            PROJECT_ROOT
            / "data/raw/research/prices"
            / price_file_name(row.symbol)
        )

        prices = pd.read_csv(
            path,
            index_col="Date",
            parse_dates=["Date"],
        )

        targets = build_targets(
            prices,
            symbol=row.symbol,
            market=row.market,
        )

        if targets.empty:
            raise ValueError(f"No observations for {row.symbol}.")

        frames.append(targets)

        print(
            f"{row.symbol:<15} "
            f"observations={len(targets)} "
            f"eligible={int(targets['eligible'].sum())}"
        )

    dataset = pd.concat(frames, ignore_index=True)

    if dataset.duplicated(["symbol", "observation_date"]).any():
        raise ValueError("Duplicate company-date observations.")

    output_directory = (
        PROJECT_ROOT / "data/interim/research"
    )
    output_directory.mkdir(parents=True, exist_ok=True)

    dataset.to_csv(
        output_directory / "targets.csv",
        index=False,
        date_format="%Y-%m-%d",
        lineterminator="\n",
    )

    summary = (
        dataset.groupby(["market", "split"], sort=False)
        .agg(
            observations=("symbol", "size"),
            eligible=("eligible", "sum"),
            complete_targets=("target_available", "sum"),
        )
        .reset_index()
    )

    summary["excluded"] = (
        summary["observations"] - summary["eligible"]
    )

    report_directory = PROJECT_ROOT / "research/results"
    report_directory.mkdir(parents=True, exist_ok=True)

    summary.to_csv(
        report_directory / "target_generation_summary.csv",
        index=False,
        lineterminator="\n",
    )

    print("\nGeneration summary")
    print(summary.to_string(index=False))
    print(f"\nTotal observations: {len(dataset)}")
    print(f"Eligible observations: {int(dataset['eligible'].sum())}")
    print(
        "Incomplete horizons: "
        f"{int((~dataset['target_available']).sum())}"
    )
    print(f"\nDataset saved to: {output_directory / 'targets.csv'}")


if __name__ == "__main__":
    main()