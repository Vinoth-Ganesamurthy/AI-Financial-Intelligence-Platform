"""Tests for leakage-safe research price collection."""

from pathlib import Path

import pandas as pd
import pytest

from src.research.config import (
    PRICE_DOWNLOAD_END,
    PRICE_DOWNLOAD_START,
)
from src.research.price_collector import (
    clean_price_data,
    download_price_history,
    price_file_name,
    save_price_data,
)


def _sample_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [10.0, 9.0, 11.0, 12.0],
            "High": [11.0, 10.0, 12.0, 13.0],
            "Low": [9.0, 8.0, 10.0, 11.0],
            "Close": [10.5, 9.5, 11.5, None],
            "Volume": [100, 90, 120, 130],
        },
        index=pd.to_datetime(
            [
                "2021-01-04",
                "2021-01-01",
                "2021-01-04",
                "2021-01-05",
            ]
        ),
    )


def test_clean_price_data_sorts_deduplicates_and_drops_missing():
    cleaned = clean_price_data(
        _sample_prices(),
        "TEST",
    )

    assert list(cleaned.columns) == [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]
    assert list(
        cleaned.index.strftime("%Y-%m-%d")
    ) == [
        "2021-01-01",
        "2021-01-04",
    ]
    assert cleaned.loc[
        "2021-01-04",
        "Close",
    ] == 11.5
    assert cleaned.index.name == "Date"


def test_clean_price_data_flattens_single_symbol_columns():
    columns = pd.MultiIndex.from_product(
        [
            [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
            ],
            ["TEST"],
        ]
    )

    data = pd.DataFrame(
        [[10, 11, 9, 10.5, 100]],
        index=pd.to_datetime(["2021-01-04"]),
        columns=columns,
    )

    cleaned = clean_price_data(
        data,
        "TEST",
    )

    assert list(cleaned.columns) == [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]
    assert cleaned.iloc[0]["Close"] == 10.5


def test_clean_price_data_requires_ohlcv_columns():
    incomplete = pd.DataFrame(
        {
            "Close": [10.0],
        },
        index=pd.to_datetime(["2021-01-04"]),
    )

    with pytest.raises(
        ValueError,
        match="missing columns",
    ):
        clean_price_data(
            incomplete,
            "TEST",
        )


@pytest.mark.parametrize(
    ("symbol", "expected"),
    [
        ("RELIANCE.NS", "RELIANCE_NS.csv"),
        ("D05.SI", "D05_SI.csv"),
        ("^GSPC", "GSPC.csv"),
        (" TEST/ABC ", "TEST_ABC.csv"),
    ],
)
def test_price_file_name_is_filesystem_safe(
    symbol,
    expected,
):
    assert price_file_name(symbol) == expected


def test_download_uses_frozen_dates_and_adjusted_prices():
    captured_arguments = {}

    def fake_download(**kwargs):
        captured_arguments.update(kwargs)

        return pd.DataFrame(
            {
                "Open": [10.0],
                "High": [11.0],
                "Low": [9.0],
                "Close": [10.5],
                "Volume": [100],
            },
            index=pd.to_datetime(
                ["2021-01-04"]
            ),
        )

    result = download_price_history(
        " msft ",
        download_function=fake_download,
    )

    assert not result.empty
    assert captured_arguments["tickers"] == "MSFT"
    assert captured_arguments["start"] == (
        PRICE_DOWNLOAD_START.isoformat()
    )
    assert captured_arguments["end"] == (
        PRICE_DOWNLOAD_END.isoformat()
    )
    assert captured_arguments["auto_adjust"] is True
    assert captured_arguments["actions"] is False


def test_save_price_data_creates_reproducible_csv(
    tmp_path: Path,
):
    cleaned = clean_price_data(
        _sample_prices(),
        "TEST",
    )

    destination = (
        tmp_path / "prices" / "TEST.csv"
    )

    saved_path = save_price_data(
        cleaned,
        destination,
    )

    assert saved_path == destination
    assert destination.exists()

    loaded = pd.read_csv(
        destination,
        parse_dates=["Date"],
    )

    assert list(loaded.columns) == [
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]
    assert len(loaded) == 2