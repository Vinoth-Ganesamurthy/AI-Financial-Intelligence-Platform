"""Verify target horizons, thresholds, and chronological boundaries."""

import numpy as np
import pandas as pd
import pytest

from src.research.targets import (
    build_targets,
    classify_forward_return,
)


def make_prices(start, periods=61):
    dates = pd.bdate_range(start, periods=periods)
    return pd.DataFrame(
        {"Close": 100.0 + np.arange(periods)},
        index=dates,
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.03, "favourable"),
        (0.02, "neutral"),
        (0.0, "neutral"),
        (-0.02, "neutral"),
        (-0.03, "unfavourable"),
    ],
)
def test_return_class_boundaries(value, expected):
    assert classify_forward_return(value) == expected


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_nonfinite_return_is_rejected(value):
    with pytest.raises(ValueError, match="finite"):
        classify_forward_return(value)


def test_observations_and_targets_use_trading_rows():
    prices = make_prices("2021-01-04")
    result = build_targets(
        prices, symbol="TEST", market="United States"
    )

    assert result["observation_date"].tolist() == [
        prices.index[0],
        prices.index[20],
        prices.index[40],
        prices.index[60],
    ]
    assert result.iloc[0]["target_date"] == prices.index[20]
    assert result.iloc[0]["forward_return_20d"] == pytest.approx(20.0)
    assert result.iloc[0]["eligible"]
    assert not result.iloc[-1]["target_available"]
    assert not result.iloc[-1]["eligible"]


@pytest.mark.parametrize(
    ("start", "expected_split"),
    [
        ("2023-12-15", "train"),
        ("2024-12-16", "validation"),
    ],
)
def test_crossing_split_boundary_is_excluded(start, expected_split):
    result = build_targets(
        make_prices(start),
        symbol="TEST",
        market="United States",
    )

    first = result.iloc[0]
    assert first["split"] == expected_split
    assert first["target_available"]
    assert not first["eligible"]
    assert first["exclusion_reason"] == "target_crosses_split_boundary"


def test_test_horizon_can_end_in_2026():
    result = build_targets(
        make_prices("2025-12-15"),
        symbol="TEST",
        market="United States",
    )

    first = result.iloc[0]
    assert first["split"] == "test"
    assert first["target_date"].year == 2026
    assert first["eligible"]


def test_warmup_dates_are_not_observations():
    prices = make_prices("2020-12-01")
    result = build_targets(
        prices, symbol="TEST", market="United States"
    )

    assert (
        result["observation_date"] >= pd.Timestamp("2021-01-01")
    ).all()


def test_future_price_change_does_not_change_earlier_target():
    prices = make_prices("2021-01-04")
    original = build_targets(
        prices, symbol="TEST", market="United States"
    )

    changed = prices.copy()
    changed.iloc[21:, 0] *= 10
    updated = build_targets(
        changed, symbol="TEST", market="United States"
    )

    assert original.iloc[0]["forward_return_20d"] == (
        updated.iloc[0]["forward_return_20d"]
    )


@pytest.mark.parametrize("invalid_close", [0, -1, np.nan, np.inf])
def test_invalid_prices_are_rejected(invalid_close):
    prices = make_prices("2021-01-04")
    prices.iloc[0, 0] = invalid_close

    with pytest.raises(ValueError, match="finite and positive"):
        build_targets(
            prices, symbol="TEST", market="United States"
        )


def test_duplicate_dates_are_rejected():
    prices = make_prices("2021-01-04")
    prices = pd.concat([prices.iloc[:1], prices])

    with pytest.raises(ValueError, match="unique and sorted"):
        build_targets(
            prices, symbol="TEST", market="United States"
        )


def test_unsorted_dates_are_rejected():
    prices = make_prices("2021-01-04").iloc[::-1]

    with pytest.raises(ValueError, match="unique and sorted"):
        build_targets(
            prices, symbol="TEST", market="United States"
        )