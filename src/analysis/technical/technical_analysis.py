"""
Technical Analysis Module

Calculates common technical indicators from OHLCV data
and produces a rule-based technical market signal.
"""

import numpy as np
import pandas as pd


# ======================================================
# Moving Averages
# ======================================================

def calculate_moving_averages(data: pd.DataFrame):
    close = data["Close"].copy()

    sma_20 = close.rolling(window=20).mean()
    sma_50 = close.rolling(window=50).mean()
    sma_200 = close.rolling(window=200).mean()

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()

    return {
        "sma_20": round(float(sma_20.iloc[-1]), 2),
        "sma_50": round(float(sma_50.iloc[-1]), 2),
        "sma_200": (
            round(float(sma_200.iloc[-1]), 2)
            if not np.isnan(sma_200.iloc[-1])
            else None
        ),
        "ema_12": round(float(ema_12.iloc[-1]), 2),
        "ema_26": round(float(ema_26.iloc[-1]), 2),
    }


# ======================================================
# RSI
# ======================================================

def calculate_rsi(
    data: pd.DataFrame,
    period: int = 14,
):
    close = data["Close"]

    delta = close.diff()

    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = gains.rolling(
        window=period
    ).mean()

    avg_loss = losses.rolling(
        window=period
    ).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (
        100 / (1 + rs)
    )

    return round(
        float(rsi.iloc[-1]),
        2,
    )


# ======================================================
# MACD
# ======================================================

def calculate_macd(data: pd.DataFrame):
    close = data["Close"]

    ema_12 = close.ewm(
        span=12,
        adjust=False,
    ).mean()

    ema_26 = close.ewm(
        span=26,
        adjust=False,
    ).mean()

    macd = ema_12 - ema_26

    signal = macd.ewm(
        span=9,
        adjust=False,
    ).mean()

    histogram = macd - signal

    return {
        "macd": round(
            float(macd.iloc[-1]),
            2,
        ),
        "macd_signal": round(
            float(signal.iloc[-1]),
            2,
        ),
        "macd_histogram": round(
            float(histogram.iloc[-1]),
            2,
        ),
    }


# ======================================================
# Bollinger Bands
# ======================================================

def calculate_bollinger_bands(
    data: pd.DataFrame,
    period: int = 20,
):
    close = data["Close"]

    middle = close.rolling(
        window=period
    ).mean()

    std = close.rolling(
        window=period
    ).std()

    upper = middle + (2 * std)
    lower = middle - (2 * std)

    return {
        "bollinger_upper": round(
            float(upper.iloc[-1]),
            2,
        ),
        "bollinger_middle": round(
            float(middle.iloc[-1]),
            2,
        ),
        "bollinger_lower": round(
            float(lower.iloc[-1]),
            2,
        ),
    }


# ======================================================
# ATR
# ======================================================

def calculate_atr(
    data: pd.DataFrame,
    period: int = 14,
):
    high = data["High"]
    low = data["Low"]
    close = data["Close"]

    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = true_range.rolling(
        window=period
    ).mean()

    return round(
        float(atr.iloc[-1]),
        2,
    )


# ======================================================
# Volume Analysis
# ======================================================

def calculate_volume_analysis(
    data: pd.DataFrame,
):
    volume = data["Volume"]

    current_volume = float(
        volume.iloc[-1]
    )

    volume_ma_20 = volume.rolling(
        window=20
    ).mean()

    average_volume = float(
        volume_ma_20.iloc[-1]
    )

    if average_volume == 0:
        relative_volume = None
    else:
        relative_volume = (
            current_volume
            / average_volume
        )

    return {
        "current_volume": int(
            current_volume
        ),
        "volume_ma_20": int(
            average_volume
        ),
        "relative_volume": (
            round(
                float(relative_volume),
                2,
            )
            if relative_volume is not None
            else None
        ),
    }


# ======================================================
# Technical Signal
# ======================================================

def generate_technical_signal(
    current_price: float,
    indicators: dict,
):
    """
    Generate a transparent rule-based technical signal.
    """

    bullish_points = 0
    bearish_points = 0

    # ----------------------------------------------
    # Moving-average trend
    # ----------------------------------------------

    if current_price > indicators["sma_20"]:
        bullish_points += 1
    else:
        bearish_points += 1

    if current_price > indicators["sma_50"]:
        bullish_points += 1
    else:
        bearish_points += 1

    if (
        indicators["sma_200"] is not None
    ):
        if current_price > indicators["sma_200"]:
            bullish_points += 1
        else:
            bearish_points += 1

    # ----------------------------------------------
    # RSI
    # ----------------------------------------------

    rsi = indicators["rsi"]

    if rsi < 30:
        bullish_points += 1

    elif rsi > 70:
        bearish_points += 1

    # ----------------------------------------------
    # MACD
    # ----------------------------------------------

    if (
        indicators["macd"]
        > indicators["macd_signal"]
    ):
        bullish_points += 1

    else:
        bearish_points += 1

    # ----------------------------------------------
    # Bollinger position
    # ----------------------------------------------

    if (
        current_price
        < indicators["bollinger_lower"]
    ):
        bullish_points += 1

    elif (
        current_price
        > indicators["bollinger_upper"]
    ):
        bearish_points += 1

    # ----------------------------------------------
    # Final classification
    # ----------------------------------------------

    score = (
        bullish_points
        - bearish_points
    )

    if score >= 2:
        signal = "BULLISH"

    elif score <= -2:
        signal = "BEARISH"

    else:
        signal = "NEUTRAL"

    return {
        "signal": signal,
        "bullish_points": bullish_points,
        "bearish_points": bearish_points,
        "net_score": score,
    }


# ======================================================
# Complete Technical Analysis
# ======================================================

def technical_analysis(
    data: pd.DataFrame,
):
    """
    Run the complete technical-analysis pipeline.
    """

    if data.empty:
        raise ValueError(
            "Market data is empty."
        )

    if len(data) < 50:
        raise ValueError(
            "At least 50 trading days "
            "are required for technical analysis."
        )

    current_price = round(
        float(
            data["Close"].iloc[-1]
        ),
        2,
    )

    moving_averages = (
        calculate_moving_averages(data)
    )

    rsi = calculate_rsi(data)

    macd = calculate_macd(data)

    bollinger = (
        calculate_bollinger_bands(data)
    )

    atr = calculate_atr(data)

    volume = calculate_volume_analysis(
        data
    )

    indicators = {
        **moving_averages,
        "rsi": rsi,
        **macd,
        **bollinger,
        "atr": atr,
        **volume,
    }

    signal = generate_technical_signal(
        current_price,
        indicators,
    )

    return {
        "current_price": current_price,
        **indicators,
        **signal,
    }