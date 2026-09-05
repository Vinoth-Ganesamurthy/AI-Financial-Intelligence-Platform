"""
Leakage-safe historical price collection utilities.

Research prices use frozen calendar dates and adjusted
OHLC data so stock splits and dividends are handled
consistently across companies and markets.
"""

from collections.abc import Callable
from pathlib import Path
import re
import time

import numpy as np
import pandas as pd
import yfinance as yf

from src.research.config import (
    PRICE_DOWNLOAD_END,
    PRICE_DOWNLOAD_START,
)


REQUIRED_PRICE_COLUMNS = (
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
)


def price_file_name(
    symbol: str,
) -> str:
    """Return a filesystem-safe CSV filename."""

    if not symbol or not symbol.strip():
        raise ValueError(
            "Stock symbol is required."
        )

    normalized_symbol = (
        symbol.strip().upper()
    )

    safe_symbol = re.sub(
        r"[^A-Z0-9_-]+",
        "_",
        normalized_symbol,
    ).strip("_")

    if not safe_symbol:
        raise ValueError(
            "Stock symbol contains no valid "
            "filename characters."
        )

    return f"{safe_symbol}.csv"


def _flatten_price_columns(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Flatten yfinance single-symbol MultiIndex columns."""

    if not isinstance(
        data.columns,
        pd.MultiIndex,
    ):
        return data

    required = set(
        REQUIRED_PRICE_COLUMNS
    )

    for level in range(
        data.columns.nlevels
    ):
        level_values = {
            str(value)
            for value in (
                data.columns
                .get_level_values(level)
            )
        }

        if required.issubset(
            level_values
        ):
            flattened = data.copy()
            flattened.columns = (
                flattened.columns
                .get_level_values(level)
            )
            return flattened

    raise ValueError(
        "Unable to identify OHLCV fields "
        "in multi-level price columns."
    )


def clean_price_data(
    data: pd.DataFrame,
    symbol: str,
) -> pd.DataFrame:
    """
    Validate, sort, deduplicate, and normalise prices.
    """

    if not symbol or not symbol.strip():
        raise ValueError(
            "Stock symbol is required."
        )

    if data is None or data.empty:
        raise ValueError(
            f"Price data is empty for {symbol}."
        )

    flattened = _flatten_price_columns(
        data
    )

    missing_columns = [
        column
        for column in REQUIRED_PRICE_COLUMNS
        if column not in flattened.columns
    ]

    if missing_columns:
        raise ValueError(
            "Price data is missing columns: "
            + ", ".join(missing_columns)
        )

    cleaned = flattened[
        list(REQUIRED_PRICE_COLUMNS)
    ].copy()

    cleaned.index = pd.to_datetime(
        cleaned.index,
        errors="coerce",
    )

    cleaned = cleaned[
        ~cleaned.index.isna()
    ]

    if cleaned.index.tz is not None:
        cleaned.index = (
            cleaned.index.tz_localize(None)
        )

    for column in REQUIRED_PRICE_COLUMNS:
        cleaned[column] = pd.to_numeric(
            cleaned[column],
            errors="coerce",
        )

    cleaned = cleaned.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    cleaned = cleaned.dropna(
        subset=["Close"]
    )

    cleaned = cleaned.sort_index()

    cleaned = cleaned[
        ~cleaned.index.duplicated(
            keep="last"
        )
    ]

    if cleaned.empty:
        raise ValueError(
            f"No valid closing prices for {symbol}."
        )

    cleaned.index.name = "Date"

    cleaned.attrs["symbol"] = (
        symbol.strip().upper()
    )
    cleaned.attrs["adjusted_prices"] = True

    return cleaned


def download_price_history(
    symbol: str,
    *,
    download_function: Callable | None = None,
    attempts: int = 3,
) -> pd.DataFrame:
    """
    Download one symbol using the frozen date range.

    A custom download function can be supplied for
    deterministic tests.
    """

    if not symbol or not symbol.strip():
        raise ValueError(
            "Stock symbol is required."
        )

    if attempts < 1:
        raise ValueError(
            "Attempts must be at least one."
        )

    normalized_symbol = (
        symbol.strip().upper()
    )

    downloader = (
        download_function
        if download_function is not None
        else yf.download
    )

    last_error = None

    for attempt in range(
        1,
        attempts + 1,
    ):
        try:
            downloaded = downloader(
                tickers=normalized_symbol,
                start=(
                    PRICE_DOWNLOAD_START
                    .isoformat()
                ),
                end=(
                    PRICE_DOWNLOAD_END
                    .isoformat()
                ),
                interval="1d",
                auto_adjust=True,
                actions=False,
                progress=False,
                threads=False,
                timeout=30,
            )

            cleaned = clean_price_data(
                downloaded,
                normalized_symbol,
            )

            cleaned.attrs[
                "data_source"
            ] = "Yahoo Finance via yfinance"

            return cleaned

        except Exception as error:
            last_error = error

            if attempt < attempts:
                time.sleep(attempt * 2)

    raise RuntimeError(
        f"Unable to download prices for "
        f"{normalized_symbol} after "
        f"{attempts} attempts: {last_error}"
    ) from last_error


def save_price_data(
    data: pd.DataFrame,
    destination: Path,
    *,
    overwrite: bool = False,
) -> Path:
    """
    Save cleaned prices as a deterministic CSV file.

    Existing raw files are protected unless overwrite
    is explicitly requested.
    """

    output_path = Path(destination)

    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Raw price file already exists: "
            f"{output_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    data.to_csv(
        temporary_path,
        index=True,
        index_label="Date",
        date_format="%Y-%m-%d",
        float_format="%.10f",
        lineterminator="\n",
    )

    temporary_path.replace(
        output_path
    )

    return output_path