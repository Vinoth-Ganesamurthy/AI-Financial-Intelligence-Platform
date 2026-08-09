"""
Market Data Service

Fetches the latest available market data
for a resolved stock symbol.
"""

import yfinance as yf


def fetch_market_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
):
    """
    Fetch historical OHLCV market data.

    Parameters
    ----------
    symbol:
        Yahoo Finance ticker symbol.

    period:
        Amount of historical data to retrieve.

    interval:
        Market-data interval.

    Returns
    -------
    pandas.DataFrame
        Clean OHLCV market data.
    """

    if not symbol:
        raise ValueError("Stock symbol is required.")

    ticker = yf.Ticker(symbol)

    data = ticker.history(
        period=period,
        interval=interval,
        auto_adjust=False,
    )

    if data.empty:
        raise ValueError(
            f"No market data found for {symbol}."
        )

    # Keep only required market columns
    required_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    available_columns = [
        column
        for column in required_columns
        if column in data.columns
    ]

    data = data[available_columns].copy()

    # Remove rows without a closing price
    data = data.dropna(
        subset=["Close"]
    )

    return data


def get_latest_market_snapshot(symbol: str):
    """
    Return the latest available trading-day snapshot.
    """

    data = fetch_market_data(
        symbol=symbol,
        period="10d",
        interval="1d",
    )

    latest = data.iloc[-1]

    return {
        "symbol": symbol,
        "date": data.index[-1].strftime(
            "%Y-%m-%d"
        ),
        "open": round(
            float(latest["Open"]),
            2,
        ),
        "high": round(
            float(latest["High"]),
            2,
        ),
        "low": round(
            float(latest["Low"]),
            2,
        ),
        "close": round(
            float(latest["Close"]),
            2,
        ),
        "volume": int(
            latest["Volume"]
        ),
    }