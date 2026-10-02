"""Calculate price features using only observation-date history."""

import numpy as np
import pandas as pd

from src.analysis.historical.historical_analysis import (
    historical_analysis,
)
from src.analysis.technical.technical_analysis import (
    technical_analysis,
)
from src.analysis.intelligence.intelligence_engine import (
    score_historical_analysis,
    score_technical_analysis,
)
from src.research.config import MINIMUM_HISTORICAL_HISTORY


def safe_ratio(numerator, denominator):
    """Return a finite ratio or NaN when undefined."""
    if numerator is None or denominator is None:
        return np.nan

    numerator = float(numerator)
    denominator = float(denominator)

    if (
        not np.isfinite(numerator)
        or not np.isfinite(denominator)
        or denominator == 0
    ):
        return np.nan

    return numerator / denominator


def build_price_features(
    prices: pd.DataFrame,
    observation_date,
) -> dict:
    """
    Reuse production formulas on a trailing two-calendar-year window.

    Future rows are excluded before any indicator is calculated.
    """
    date = pd.Timestamp(observation_date)

    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("Prices must have a DatetimeIndex.")

    if prices.index.tz is not None or date.tzinfo is not None:
        raise ValueError("Use timezone-naive local trading dates.")

    if (
        prices.index.hasnans
        or not prices.index.is_unique
        or not prices.index.is_monotonic_increasing
    ):
        raise ValueError("Price dates must be valid, unique and sorted.")

    if date not in prices.index:
        raise ValueError("Observation date is not a trading row.")

    window_start = date - pd.DateOffset(years=2)
    history = prices.loc[
        (prices.index >= window_start)
        & (prices.index <= date)
    ].copy()

    # A 252-day return requires 253 closing-price observations.
    if len(history) < MINIMUM_HISTORICAL_HISTORY + 1:
        raise ValueError("Insufficient historical warm-up.")

    required = ["Open", "High", "Low", "Close", "Volume"]
    if any(column not in history for column in required):
        raise ValueError("Missing required OHLCV columns.")

    values = history[required].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Historical OHLCV values must be finite.")

    if (history[["Open", "High", "Low", "Close"]] <= 0).any().any():
        raise ValueError("Historical prices must be positive.")

    if (history["Volume"] < 0).any():
        raise ValueError("Historical volume must be nonnegative.")

    technical = technical_analysis(history)
    historical = historical_analysis(history)

    # Undefined indicators must remain missing, rather than becoming
    # false bearish comparisons inside the production signal logic.
    signal_fields = [
        "sma_20",
        "sma_50",
        "sma_200",
        "rsi",
        "macd",
        "macd_signal",
        "bollinger_upper",
        "bollinger_lower",
    ]
    technical_available = all(
        technical.get(field) is not None
        and np.isfinite(float(technical[field]))
        for field in signal_fields
    )

    technical_score = score_technical_analysis(
        technical if technical_available else None
    )
    historical_score = score_historical_analysis(historical)

    close = float(history["Close"].iloc[-1])
    upper = technical["bollinger_upper"]
    lower = technical["bollinger_lower"]

    features = {
        "observation_date": date,
        "feature_window_start": history.index[0],
        "feature_window_end": history.index[-1],
        "history_rows": len(history),
        "technical_module_score": (
            technical_score["score"]
            if technical_available
            else np.nan
        ),
        "technical_is_available": technical_available,
        "technical_quality_factor": technical_score["quality_factor"],
        "historical_module_score": historical_score["score"],
        "historical_quality_factor": historical_score["quality_factor"],
        "historical_risk_penalty": historical_score["risk_penalty"],
    }

    features.update(
        {f"technical_{key}": value for key, value in technical.items()}
    )
    features.update(
        {f"historical_{key}": value for key, value in historical.items()}
    )

    for period in (20, 50, 200):
        ratio = safe_ratio(close, technical[f"sma_{period}"])
        features[f"price_to_sma_{period}"] = ratio - 1

    features["ema_spread"] = (
        safe_ratio(technical["ema_12"], technical["ema_26"]) - 1
    )
    features["macd_pct"] = safe_ratio(technical["macd"], close) * 100
    features["macd_histogram_pct"] = (
        safe_ratio(technical["macd_histogram"], close) * 100
    )
    features["bollinger_position"] = safe_ratio(
        close - lower, upper - lower
    )
    features["atr_pct"] = safe_ratio(technical["atr"], close) * 100
    features["price_range_position"] = safe_ratio(
        close - historical["period_low"],
        historical["period_high"] - historical["period_low"],
    )

    return features