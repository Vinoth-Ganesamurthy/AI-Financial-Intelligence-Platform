"""
Collect adjusted historical OHLCV data for the frozen
40-company research universe.

Raw files are immutable by default. Use --overwrite only
when intentionally rebuilding the complete raw dataset.
"""

import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sys
import time

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from src.research.config import (  # noqa: E402
    DATASET_VERSION,
    PRICE_DOWNLOAD_END,
    PRICE_DOWNLOAD_START,
)
from src.research.price_collector import (  # noqa: E402
    clean_price_data,
    download_price_history,
    price_file_name,
    save_price_data,
)


UNIVERSE_PATH = (
    PROJECT_ROOT
    / "research"
    / "company_universe.csv"
)

PRICE_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "research"
    / "prices"
)

MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "research"
    / "price_manifest.csv"
)


def calculate_file_hash(
    file_path: Path,
) -> str:
    """Calculate a SHA-256 hash for one raw file."""

    digest = hashlib.sha256()

    with file_path.open("rb") as price_file:
        for block in iter(
            lambda: price_file.read(65_536),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def load_existing_prices(
    file_path: Path,
    symbol: str,
) -> pd.DataFrame:
    """Load and validate an existing immutable file."""

    existing = pd.read_csv(
        file_path,
        index_col="Date",
        parse_dates=["Date"],
    )

    return clean_price_data(
        existing,
        symbol,
    )


def build_manifest_row(
    universe_row,
    prices: pd.DataFrame,
    file_path: Path,
    status: str,
    retrieved_at: str,
) -> dict:
    """Build traceability metadata for one symbol."""

    return {
        "dataset_version": DATASET_VERSION,
        "market": universe_row.market,
        "symbol": universe_row.symbol,
        "company": universe_row.company,
        "research_sector": universe_row.sector,
        "download_start": (
            PRICE_DOWNLOAD_START.isoformat()
        ),
        "download_end_exclusive": (
            PRICE_DOWNLOAD_END.isoformat()
        ),
        "first_price_date": (
            prices.index.min()
            .date()
            .isoformat()
        ),
        "last_price_date": (
            prices.index.max()
            .date()
            .isoformat()
        ),
        "row_count": len(prices),
        "file_name": file_path.name,
        "file_size_bytes": (
            file_path.stat().st_size
        ),
        "sha256": calculate_file_hash(
            file_path
        ),
        "adjusted_prices": True,
        "source": (
            "Yahoo Finance via yfinance"
        ),
        "collection_status": status,
        "retrieved_at_utc": retrieved_at,
        "error": "",
    }


def collect_prices(
    universe: pd.DataFrame,
    *,
    overwrite: bool,
) -> pd.DataFrame:
    """Collect every selected universe row."""

    PRICE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    retrieved_at = datetime.now(
        timezone.utc
    ).isoformat()

    manifest_rows = []

    total = len(universe)

    for position, row in enumerate(
        universe.itertuples(index=False),
        start=1,
    ):
        file_path = (
            PRICE_DIRECTORY
            / price_file_name(row.symbol)
        )

        try:
            if (
                file_path.exists()
                and not overwrite
            ):
                prices = load_existing_prices(
                    file_path,
                    row.symbol,
                )
                status = "existing"
            else:
                prices = download_price_history(
                    row.symbol
                )

                save_price_data(
                    prices,
                    file_path,
                    overwrite=overwrite,
                )

                status = "collected"

                time.sleep(0.25)

            manifest_rows.append(
                build_manifest_row(
                    row,
                    prices,
                    file_path,
                    status,
                    retrieved_at,
                )
            )

            print(
                f"[{position:02d}/{total:02d}] "
                f"{row.symbol:<15} "
                f"{status:<10} "
                f"rows={len(prices)} "
                f"{prices.index.min().date()} "
                f"to {prices.index.max().date()}"
            )

        except Exception as error:
            manifest_rows.append(
                {
                    "dataset_version": (
                        DATASET_VERSION
                    ),
                    "market": row.market,
                    "symbol": row.symbol,
                    "company": row.company,
                    "research_sector": row.sector,
                    "download_start": (
                        PRICE_DOWNLOAD_START
                        .isoformat()
                    ),
                    "download_end_exclusive": (
                        PRICE_DOWNLOAD_END
                        .isoformat()
                    ),
                    "first_price_date": "",
                    "last_price_date": "",
                    "row_count": 0,
                    "file_name": file_path.name,
                    "file_size_bytes": 0,
                    "sha256": "",
                    "adjusted_prices": True,
                    "source": (
                        "Yahoo Finance via yfinance"
                    ),
                    "collection_status": "failed",
                    "retrieved_at_utc": (
                        retrieved_at
                    ),
                    "error": str(error),
                }
            )

            print(
                f"[{position:02d}/{total:02d}] "
                f"{row.symbol:<15} FAILED: "
                f"{error}"
            )

    manifest = pd.DataFrame(
        manifest_rows
    )

    MANIFEST_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest.to_csv(
        MANIFEST_PATH,
        index=False,
        lineterminator="\n",
    )

    return manifest


def parse_arguments():
    """Parse command-line options."""

    parser = argparse.ArgumentParser(
        description=(
            "Collect frozen historical research "
            "price data."
        )
    )

    parser.add_argument(
        "--symbol",
        help=(
            "Collect one symbol for a smoke test. "
            "The symbol must exist in the universe."
        ),
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Intentionally replace existing raw "
            "price files."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Run price collection."""

    arguments = parse_arguments()

    universe = pd.read_csv(
        UNIVERSE_PATH
    )

    required_columns = {
        "market",
        "symbol",
        "company",
        "sector",
    }

    missing_columns = (
        required_columns
        - set(universe.columns)
    )

    if missing_columns:
        raise ValueError(
            "Universe is missing columns: "
            f"{sorted(missing_columns)}"
        )

    if arguments.symbol:
        requested_symbol = (
            arguments.symbol
            .strip()
            .upper()
        )

        universe = universe[
            universe["symbol"]
            .str.upper()
            .eq(requested_symbol)
        ]

        if universe.empty:
            raise ValueError(
                f"{requested_symbol} is not in "
                "the frozen research universe."
            )

    manifest = collect_prices(
        universe,
        overwrite=arguments.overwrite,
    )

    print(
        "\nCollection summary"
    )
    print(
        manifest[
            "collection_status"
        ]
        .value_counts()
        .to_string()
    )

    print(
        "\nManifest saved to: "
        f"{MANIFEST_PATH}"
    )

    failed = manifest[
        manifest["collection_status"]
        == "failed"
    ]

    if not failed.empty:
        print(
            "\nFailed symbols:"
        )
        print(
            failed[
                ["symbol", "error"]
            ].to_string(index=False)
        )
        raise SystemExit(1)

    print(
        "\nPrice collection completed "
        "without failures."
    )


if __name__ == "__main__":
    main()