"""
Historical Analysis Module

Calculates historical performance and risk metrics
from stock-market price data.
"""

import numpy as np
import pandas as pd


def calculate_returns(data: pd.DataFrame):
    """
    Calculate historical stock returns.
    """

    if data.empty:
        raise ValueError("Market data is empty.")

    close = data["Close"]

    daily_returns = close.pct_change().dropna()

    latest_price = float(close.iloc[-1])

    def period_return(days: int):
        if len(close) <= days:
            return None

        old_price = float(close.iloc[-days - 1])

        return round(
            ((latest_price - old_price) / old_price) * 100,
            2,
        )

    return {
        "current_price": round(latest_price, 2),
        "one_week_return": period_return(5),
        "one_month_return": period_return(21),
        "three_month_return": period_return(63),
        "six_month_return": period_return(126),
        "one_year_return": (
            period_return(252)
            if len(close) > 252
            else None
        ),
        "daily_returns": daily_returns,
    }


def calculate_volatility(
    daily_returns: pd.Series,
):
    """
    Calculate annualized historical volatility.
    """

    if daily_returns.empty:
        return None

    volatility = (
        daily_returns.std()
        * np.sqrt(252)
        * 100
    )

    return round(
        float(volatility),
        2,
    )


def calculate_max_drawdown(
    data: pd.DataFrame,
):
    """
    Calculate maximum historical drawdown.
    """

    close = data["Close"]

    running_max = close.cummax()

    drawdown = (
        (close - running_max)
        / running_max
    )

    max_drawdown = (
        drawdown.min()
        * 100
    )

    return round(
        float(max_drawdown),
        2,
    )


def calculate_price_range(
    data: pd.DataFrame,
):
    """
    Calculate historical high and low.
    """

    return {
        "period_high": round(
            float(data["High"].max()),
            2,
        ),
        "period_low": round(
            float(data["Low"].min()),
            2,
        ),
    }


def historical_analysis(
    data: pd.DataFrame,
):
    """
    Run complete historical analysis.
    """

    returns = calculate_returns(data)

    daily_returns = returns.pop(
        "daily_returns"
    )

    volatility = calculate_volatility(
        daily_returns
    )

    max_drawdown = calculate_max_drawdown(
        data
    )

    price_range = calculate_price_range(
        data
    )

    return {
        **returns,
        "annualized_volatility": volatility,
        "maximum_drawdown": max_drawdown,
        **price_range,
    }