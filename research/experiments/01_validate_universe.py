"""
Validate historical price-data availability for the fixed research universe.

This script checks whether every selected company has sufficient adjusted
daily closing-price history for the 2021-2025 research period.
"""

from pathlib import Path
import time

import pandas as pd
import yfinance as yf


PROJECT_ROOT = Path(__file__).resolve().parents[2]

UNIVERSE_PATH = (
    PROJECT_ROOT
    / "research"
    / "company_universe.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "research"
    / "results"
    / "universe_validation.csv"
)

START_DATE = "2021-01-01"
END_DATE = "2026-01-01"

EARLIEST_ACCEPTABLE_DATE = pd.Timestamp(
    "2021-02-01"
)
LATEST_ACCEPTABLE_DATE = pd.Timestamp(
    "2025-12-01"
)
MINIMUM_TRADING_DAYS = 1100


def extract_close_prices(
    data: pd.DataFrame,
) -> pd.Series:
    """Return a clean adjusted closing-price series."""

    if data.empty or "Close" not in data:
        return pd.Series(dtype="float64")

    close_prices = data["Close"]

    if isinstance(close_prices, pd.DataFrame):
        close_prices = close_prices.iloc[:, 0]

    return pd.to_numeric(
        close_prices,
        errors="coerce",
    ).dropna()


def download_prices(
    symbol: str,
    attempts: int = 3,
) -> pd.Series:
    """Download prices with a small retry policy."""

    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            data = yf.download(
                symbol,
                start=START_DATE,
                end=END_DATE,
                auto_adjust=True,
                progress=False,
                threads=False,
                timeout=20,
            )

            prices = extract_close_prices(data)

            if not prices.empty:
                return prices

            last_error = ValueError(
                "Yahoo Finance returned no prices."
            )

        except Exception as error:
            last_error = error

        if attempt < attempts:
            time.sleep(attempt * 2)

    raise RuntimeError(
        f"Download failed after {attempts} "
        f"attempts: {last_error}"
    )


def validate_universe() -> pd.DataFrame:
    """Validate every company in the universe."""

    universe = pd.read_csv(UNIVERSE_PATH)

    required_columns = {
        "market",
        "symbol",
        "company",
        "sector",
    }

    missing_columns = (
        required_columns - set(universe.columns)
    )

    if missing_columns:
        raise ValueError(
            "Universe file is missing columns: "
            f"{sorted(missing_columns)}"
        )

    if len(universe) != 40:
        raise ValueError(
            "The research universe must contain "
            f"40 companies, but found {len(universe)}."
        )

    market_counts = universe.groupby(
        "market"
    ).size()

    if (
        len(market_counts) != 4
        or not (market_counts == 10).all()
    ):
        raise ValueError(
            "The universe must contain exactly "
            "10 companies from each of 4 markets."
        )

    validation_rows = []

    for row in universe.itertuples(index=False):
        try:
            prices = download_prices(row.symbol)

            first_date = pd.Timestamp(
                prices.index.min()
            ).tz_localize(None)

            last_date = pd.Timestamp(
                prices.index.max()
            ).tz_localize(None)

            trading_days = len(prices)

            sufficient_start = (
                first_date
                <= EARLIEST_ACCEPTABLE_DATE
            )
            sufficient_end = (
                last_date
                >= LATEST_ACCEPTABLE_DATE
            )
            sufficient_days = (
                trading_days
                >= MINIMUM_TRADING_DAYS
            )

            status = (
                "PASS"
                if (
                    sufficient_start
                    and sufficient_end
                    and sufficient_days
                )
                else "REVIEW"
            )

            error_message = ""

        except Exception as error:
            first_date = pd.NaT
            last_date = pd.NaT
            trading_days = 0
            status = "FAIL"
            error_message = str(error)

        validation_rows.append(
            {
                "market": row.market,
                "symbol": row.symbol,
                "company": row.company,
                "sector": row.sector,
                "first_date": (
                    first_date.date().isoformat()
                    if pd.notna(first_date)
                    else ""
                ),
                "last_date": (
                    last_date.date().isoformat()
                    if pd.notna(last_date)
                    else ""
                ),
                "trading_days": trading_days,
                "status": status,
                "error": error_message,
            }
        )

        print(
            f"[{status}] "
            f"{row.symbol:<15} "
            f"days={trading_days:<5} "
            f"{first_date} -> {last_date}"
        )

    results = pd.DataFrame(validation_rows)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    results.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    return results


def main() -> None:
    """Run validation and print the summary."""

    results = validate_universe()

    print("\nValidation summary")
    print(
        results["status"]
        .value_counts()
        .to_string()
    )

    print(
        "\nResults saved to: "
        f"{OUTPUT_PATH}"
    )

    unresolved = results[
        results["status"] != "PASS"
    ]

    if not unresolved.empty:
        print(
            "\nSymbols requiring review:"
        )
        print(
            unresolved[
                [
                    "market",
                    "symbol",
                    "status",
                    "error",
                ]
            ].to_string(index=False)
        )
        raise SystemExit(1)

    print(
        "\nAll 40 symbols passed "
        "historical-data validation."
    )


if __name__ == "__main__":
    main()