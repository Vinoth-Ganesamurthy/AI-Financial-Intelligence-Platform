"""Check historical feature timing and data validation."""

import numpy as np
import pandas as pd
import pytest

from src.research.price_features import build_price_features


def sample_prices():
    dates = pd.bdate_range("2019-01-01", "2022-03-01")
    close = 100 + np.arange(len(dates)) * 0.05
    close += np.sin(np.arange(len(dates)) / 5)

    return pd.DataFrame(
        {
            "Open": close - 0.2,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": 1000,
        },
        index=dates,
    )


def test_future_prices_cannot_change_features():
    prices = sample_prices()
    date = pd.Timestamp("2021-06-01")

    original = build_price_features(prices, date)

    changed = prices.copy()
    changed.loc[changed.index > date, :] *= 100
    updated = build_price_features(changed, date)

    pd.testing.assert_series_equal(
        pd.Series(original),
        pd.Series(updated),
    )


def test_feature_window_ends_at_observation():
    prices = sample_prices()
    date = pd.Timestamp("2021-06-01")
    result = build_price_features(prices, date)

    assert result["feature_window_end"] == date
    assert result["feature_window_start"] >= (
        date - pd.DateOffset(years=2)
    )
    assert result["historical_current_price"] == pytest.approx(
        round(prices.loc[date, "Close"], 2)
    )
    assert result["technical_is_available"]
    assert np.isfinite(result["atr_pct"])


def test_insufficient_warmup_is_rejected():
    with pytest.raises(ValueError, match="warm-up"):
        build_price_features(
            sample_prices().iloc[:100],
            pd.Timestamp("2019-05-01"),
        )


def test_nontrading_observation_is_rejected():
    with pytest.raises(ValueError, match="trading row"):
        build_price_features(
            sample_prices(),
            pd.Timestamp("2021-06-05"),
        )


def test_missing_historical_value_is_rejected():
    prices = sample_prices()
    prices.loc["2021-05-31", "High"] = np.nan

    with pytest.raises(ValueError, match="finite"):
        build_price_features(prices, "2021-06-01")


def test_missing_future_value_does_not_affect_features():
    prices = sample_prices()
    prices.loc["2022-02-01", "High"] = np.nan

    result = build_price_features(prices, "2021-06-01")
    assert result["technical_is_available"]


def test_flat_prices_make_undefined_rsi_unavailable():
    prices = sample_prices()
    prices[["Open", "High", "Low", "Close"]] = 100.0

    result = build_price_features(prices, "2021-06-01")

    assert not result["technical_is_available"]
    assert np.isnan(result["technical_module_score"])
    assert result["technical_quality_factor"] == 0


def test_zero_volume_produces_missing_relative_volume():
    prices = sample_prices()
    prices["Volume"] = 0

    result = build_price_features(prices, "2021-06-01")

    assert result["technical_relative_volume"] is None
    assert result["technical_is_available"]