"""
Validate raw research price files and publish a
version-controlled integrity report and manifest.
"""

from datetime import timedelta
import hashlib
from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from src.research.config import (  # noqa: E402
    EXPECTED_COMPANY_COUNT,
    MINIMUM_HISTORICAL_HISTORY,
    PRICE_DOWNLOAD_START,
    RESEARCH_END,
    RESEARCH_START,
    TARGET_HORIZON_TRADING_DAYS,
)
from src.research.price_collector import (  # noqa: E402
    price_file_name,
)


UNIVERSE_PATH = (
    PROJECT_ROOT
    / "research"
    / "company_universe.csv"
)

RAW_PRICE_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "research"
    / "prices"
)

RAW_MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "research"
    / "price_manifest.csv"
)

REPORT_PATH = (
    PROJECT_ROOT
    / "research"
    / "results"
    / "price_data_validation.csv"
)

TRACKED_MANIFEST_PATH = (
    PROJECT_ROOT
    / "research"
    / "results"
    / "price_data_manifest.csv"
)

REQUIRED_COLUMNS = (
    "Date",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
)


def calculate_file_hash(
    file_path: Path,
) -> str:
    """Calculate a SHA-256 file hash."""

    digest = hashlib.sha256()

    with file_path.open("rb") as data_file:
        for block in iter(
            lambda: data_file.read(65_536),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def validate_symbol(
    universe_row,
    manifest: pd.DataFrame,
) -> dict:
    """Validate one symbol and return its QA record."""

    symbol = universe_row.symbol

    file_path = (
        RAW_PRICE_DIRECTORY
        / price_file_name(symbol)
    )

    issues = []
    warnings = []

    result = {
        "market": universe_row.market,
        "symbol": symbol,
        "company": universe_row.company,
        "file_name": file_path.name,
        "row_count": 0,
        "first_date": "",
        "last_date": "",
        "warmup_rows": 0,
        "research_rows": 0,
        "forward_coverage_rows": 0,
        "duplicate_dates": 0,
        "missing_ohlcv_values": 0,
        "nonpositive_price_values": 0,
        "negative_volume_values": 0,
        "price_relationship_errors": 0,
        "hash_matches_manifest": False,
        "status": "FAIL",
        "issues": "",
        "warnings": "",
    } 

    matching_manifest = manifest[
        manifest["symbol"].eq(symbol)
    ]

    if len(matching_manifest) != 1:
        issues.append(
            "Expected exactly one manifest row"
        )

    if not file_path.exists():
        issues.append(
            "Raw price file is missing"
        )
        result["issues"] = "; ".join(issues)
        return result

    try:
        raw = pd.read_csv(
            file_path
        )
    except Exception as error:
        issues.append(
            f"CSV cannot be read: {error}"
        )
        result["issues"] = "; ".join(issues)
        return result

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in raw.columns
    ]

    if missing_columns:
        issues.append(
            "Missing columns: "
            + ", ".join(missing_columns)
        )
        result["issues"] = "; ".join(issues)
        return result

    raw["Date"] = pd.to_datetime(
        raw["Date"],
        errors="coerce",
    )

    invalid_dates = int(
        raw["Date"].isna().sum()
    )

    if invalid_dates:
        issues.append(
            f"{invalid_dates} invalid dates"
        )

    raw = raw.dropna(
        subset=["Date"]
    )

    numeric_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    for column in numeric_columns:
        raw[column] = pd.to_numeric(
            raw[column],
            errors="coerce",
        )

    result["row_count"] = len(raw)

    if not raw.empty:
        result["first_date"] = (
            raw["Date"].min()
            .date()
            .isoformat()
        )
        result["last_date"] = (
            raw["Date"].max()
            .date()
            .isoformat()
        )

    duplicate_dates = int(
        raw["Date"].duplicated().sum()
    )
    result["duplicate_dates"] = (
        duplicate_dates
    )

    if duplicate_dates:
        issues.append(
            f"{duplicate_dates} duplicate dates"
        )

    if not raw["Date"].is_monotonic_increasing:
        issues.append(
            "Dates are not increasing"
        )

    missing_values = int(
        raw[numeric_columns]
        .isna()
        .sum()
        .sum()
    )
    result["missing_ohlcv_values"] = (
        missing_values
    )

    if missing_values:
        issues.append(
            f"{missing_values} missing OHLCV values"
        )

    price_columns = [
        "Open",
        "High",
        "Low",
        "Close",
    ]

    nonpositive_prices = int(
        raw[price_columns]
        .le(0)
        .sum()
        .sum()
    )
    result["nonpositive_price_values"] = (
        nonpositive_prices
    )

    if nonpositive_prices:
        issues.append(
            f"{nonpositive_prices} "
            "non-positive prices"
        )

    negative_volume = int(
        raw["Volume"].lt(0).sum()
    )
    result["negative_volume_values"] = (
        negative_volume
    )

    if negative_volume:
        issues.append(
            f"{negative_volume} negative volumes"
        )

    complete_prices = raw.dropna(
        subset=price_columns
    )

    invalid_high = (
        complete_prices["High"]
        < complete_prices[
            ["Open", "Low", "Close"]
        ].max(axis=1)
    )

    invalid_low = (
        complete_prices["Low"]
        > complete_prices[
            ["Open", "High", "Close"]
        ].min(axis=1)
    )

    relationship_errors = int(
        invalid_high.sum()
        + invalid_low.sum()
    )

    result[
        "price_relationship_errors"
    ] = relationship_errors

    if relationship_errors == 1:
        warnings.append(
            "One provider OHLC relationship "
            "anomaly; raw value preserved"
        )
    elif relationship_errors > 1:
        issues.append(
            f"{relationship_errors} invalid "
            "high/low relationships"
        )

    warmup_rows = int(
        (
            raw["Date"]
            < pd.Timestamp(RESEARCH_START)
        ).sum()
    )

    research_rows = int(
        raw["Date"].between(
            pd.Timestamp(RESEARCH_START),
            pd.Timestamp(RESEARCH_END),
            inclusive="both",
        ).sum()
    )

    forward_rows = int(
        (
            raw["Date"]
            > pd.Timestamp(RESEARCH_END)
        ).sum()
    )

    result["warmup_rows"] = warmup_rows
    result["research_rows"] = research_rows
    result[
        "forward_coverage_rows"
    ] = forward_rows

    if (
        raw.empty
        or raw["Date"].min()
        > pd.Timestamp(
            PRICE_DOWNLOAD_START
            + timedelta(days=45)
        )
    ):
        issues.append(
            "Insufficient early price coverage"
        )

    if (
        warmup_rows
        < MINIMUM_HISTORICAL_HISTORY
    ):
        issues.append(
            "Insufficient warm-up history"
        )

    if research_rows < 1_000:
        issues.append(
            "Insufficient research-period history"
        )

    if (
        forward_rows
        < TARGET_HORIZON_TRADING_DAYS
    ):
        issues.append(
            "Insufficient forward-target coverage"
        )

    if len(matching_manifest) == 1:
        manifest_row = (
            matching_manifest.iloc[0]
        )

        actual_hash = calculate_file_hash(
            file_path
        )

        expected_hash = str(
            manifest_row["sha256"]
        )

        hash_matches = (
            actual_hash == expected_hash
        )

        result[
            "hash_matches_manifest"
        ] = hash_matches

        if not hash_matches:
            issues.append(
                "SHA-256 hash does not match"
            )

        expected_rows = int(
            manifest_row["row_count"]
        )

        if len(raw) != expected_rows:
            issues.append(
                "Row count does not match manifest"
            )

    if issues:
        result["status"] = "FAIL"
    elif warnings:
        result["status"] = "WARN"
    else:
        result["status"] = "PASS"

    result["issues"] = "; ".join(
        issues
    )
    result["warnings"] = "; ".join(
        warnings
    )

    return result

def main() -> None:
    """Run complete raw-price validation."""

    universe = pd.read_csv(
        UNIVERSE_PATH
    )

    manifest = pd.read_csv(
        RAW_MANIFEST_PATH
    )

    raw_files = list(
        RAW_PRICE_DIRECTORY.glob("*.csv")
    )

    if len(universe) != EXPECTED_COMPANY_COUNT:
        raise ValueError(
            "The universe does not contain "
            f"{EXPECTED_COMPANY_COUNT} companies."
        )

    if len(manifest) != EXPECTED_COMPANY_COUNT:
        raise ValueError(
            "The manifest does not contain "
            f"{EXPECTED_COMPANY_COUNT} rows."
        )

    if len(raw_files) != EXPECTED_COMPANY_COUNT:
        raise ValueError(
            "The raw directory does not contain "
            f"{EXPECTED_COMPANY_COUNT} CSV files."
        )

    validation_rows = [
        validate_symbol(
            row,
            manifest,
        )
        for row in universe.itertuples(
            index=False
        )
    ]

    report = pd.DataFrame(
        validation_rows
    )

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report.to_csv(
        REPORT_PATH,
        index=False,
        lineterminator="\n",
    )

    manifest.to_csv(
        TRACKED_MANIFEST_PATH,
        index=False,
        lineterminator="\n",
    )

    for row in report.itertuples(
        index=False
    ):
        print(
            f"[{row.status}] "
            f"{row.symbol:<15} "
            f"rows={row.row_count:<5} "
            f"warmup={row.warmup_rows:<4} "
            f"research={row.research_rows:<4} "
            f"forward={row.forward_coverage_rows:<3}"
        )

        if row.issues:
            print(
                f"       {row.issues}"
            )
        if row.warnings:
            print(
                f"       WARNING: {row.warnings}"
            )
    print(
        "\nValidation summary"
    )
    print(
        report["status"]
        .value_counts()
        .to_string()
    )

    print(
        "\nValidation report saved to: "
        f"{REPORT_PATH}"
    )
    print(
        "Tracked manifest saved to: "
        f"{TRACKED_MANIFEST_PATH}"
    )

    failed = report[
        report["status"] == "FAIL"
    ]

    if not failed.empty:
        raise SystemExit(1)

    print(
        "\nNo critical raw-price integrity "
        "failures were found."
    )


if __name__ == "__main__":
    main()