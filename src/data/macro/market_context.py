"""
Market Context Service

Fetches market-based macro context such as
stock indices, currencies, volatility,
bond-yield proxies, and commodities.
"""

from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from src.data.macro.country_config import (
    get_market_config,
)


# ======================================================
# Historical Series
# ======================================================

def fetch_series(
    symbol: str,
    period: str = "6mo",
):
    """
    Fetch daily closing-price history.
    """

    if not symbol:
        return None

    data = yf.Ticker(symbol).history(
        period=period,
        interval="1d",
        auto_adjust=False,
    )

    if data.empty:
        return None

    if "Close" not in data.columns:
        return None

    close = (
        data["Close"]
        .dropna()
        .copy()
    )

    if close.empty:
        return None

    return close


# ======================================================
# Return Calculations
# ======================================================

def calculate_period_return(
    series: pd.Series,
    trading_days: int,
):
    """
    Calculate percentage return over
    approximately N trading days.
    """

    if series is None:
        return None

    if len(series) <= trading_days:
        return None

    current = float(
        series.iloc[-1]
    )

    previous = float(
        series.iloc[
            -trading_days - 1
        ]
    )

    if previous == 0:
        return None

    return round(
        (
            (current - previous)
            / previous
        )
        * 100,
        2,
    )


def create_series_snapshot(
    symbol: str,
):
    """
    Return current market value and
    recent percentage movements.
    """

    series = fetch_series(
        symbol,
        period="1y",
    )

    if series is None:
        return None

    return {
        "symbol": symbol,

        "latest_value": round(
            float(series.iloc[-1]),
            4,
        ),

        "data_date": (
            series.index[-1]
            .strftime("%Y-%m-%d")
        ),

        "one_week_return": (
            calculate_period_return(
                series,
                5,
            )
        ),

        "one_month_return": (
            calculate_period_return(
                series,
                21,
            )
        ),

        "three_month_return": (
            calculate_period_return(
                series,
                63,
            )
        ),
    }


# ======================================================
# Main Market Context
# ======================================================

def fetch_market_context(
    stock_symbol: str,
):
    """
    Fetch market-specific context for
    a company symbol.
    """

    config = get_market_config(
        stock_symbol
    )

    # ----------------------------------------------
    # Market indices
    # ----------------------------------------------

    indices = {}

    for (
        name,
        symbol,
    ) in config[
        "market_indices"
    ].items():

        indices[name] = (
            create_series_snapshot(
                symbol
            )
        )

    # ----------------------------------------------
    # Currencies
    # ----------------------------------------------

    currencies = {}

    for (
        name,
        symbol,
    ) in config[
        "currency_pairs"
    ].items():

        currencies[name] = (
            create_series_snapshot(
                symbol
            )
        )

    # ----------------------------------------------
    # Commodities
    # ----------------------------------------------

    commodities = {}

    for (
        name,
        symbol,
    ) in config[
        "commodities"
    ].items():

        commodities[name] = (
            create_series_snapshot(
                symbol
            )
        )

    # ----------------------------------------------
    # Volatility
    # ----------------------------------------------

    volatility = None

    volatility_symbol = config.get(
        "volatility_index"
    )

    if volatility_symbol:

        volatility = (
            create_series_snapshot(
                volatility_symbol
            )
        )

    # ----------------------------------------------
    # Bond yield proxy
    # ----------------------------------------------

    bond_yield = None

    bond_symbol = config.get(
        "bond_yield_symbol"
    )

    if bond_symbol:

        bond_yield = (
            create_series_snapshot(
                bond_symbol
            )
        )

    # ----------------------------------------------
    # Response
    # ----------------------------------------------

    return {
        "stock_symbol": stock_symbol,

        "market_code": config[
            "market_code"
        ],

        "country": config[
            "country"
        ],

        "currency": config[
            "currency"
        ],

        "indices": indices,

        "currencies": currencies,

        "volatility": volatility,

        "bond_yield": bond_yield,

        "commodities": commodities,

        "retrieved_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }