"""
Market Data Service.

Fetches historical OHLCV data using yfinance as the
primary source and Yahoo's direct chart endpoint as
a browser-compatible fallback.
"""

import re
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from urllib.parse import quote

import pandas as pd
import yfinance as yf
from curl_cffi import requests as browser_requests


YAHOO_CHART_URL = (
    "https://query1.finance.yahoo.com/"
    "v8/finance/chart/{symbol}"
)

REQUIRED_COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
]


def _clean_market_data(
    data: pd.DataFrame,
):
    """
    Validate and normalize an OHLCV DataFrame.
    """

    if data is None or data.empty:
        raise ValueError(
            "Market data is empty."
        )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "Market data is missing columns: "
            + ", ".join(missing_columns)
        )

    cleaned = data[
        REQUIRED_COLUMNS
    ].copy()

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
            "Market data contains no valid "
            "closing prices."
        )

    return cleaned


def _period_timestamps(
    period: str,
):
    """
    Convert a yfinance-style period into Unix
    timestamps for Yahoo's chart endpoint.
    """

    normalized_period = (
        period.strip().lower()
    )

    end_time = datetime.now(
        timezone.utc
    )

    if normalized_period == "max":
        start_time = datetime(
            1970,
            1,
            1,
            tzinfo=timezone.utc,
        )

    elif normalized_period == "ytd":
        start_time = datetime(
            end_time.year,
            1,
            1,
            tzinfo=timezone.utc,
        )

    else:
        match = re.fullmatch(
            r"(\d+)(d|wk|mo|y)",
            normalized_period,
        )

        if not match:
            raise ValueError(
                f"Unsupported market-data period: "
                f"{period}"
            )

        amount = int(
            match.group(1)
        )

        unit = match.group(2)

        day_multipliers = {
            "d": 1,
            "wk": 7,
            "mo": 31,
            "y": 366,
        }

        start_time = (
            end_time
            - timedelta(
                days=(
                    amount
                    * day_multipliers[unit]
                )
            )
        )

    return (
        int(start_time.timestamp()),
        int(end_time.timestamp()),
    )


def _fetch_yahoo_chart_data(
    symbol: str,
    period: str,
    interval: str,
):
    """
    Fetch OHLCV data directly from Yahoo's chart
    endpoint using a browser-like HTTP client.
    """

    period_start, period_end = (
        _period_timestamps(period)
    )

    encoded_symbol = quote(
        symbol,
        safe="",
    )

    url = YAHOO_CHART_URL.format(
        symbol=encoded_symbol
    )

    response = browser_requests.get(
        url,
        params={
            "period1": period_start,
            "period2": period_end,
            "interval": interval,
            "events": "history",
        },
        impersonate="chrome",
        timeout=20,
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Yahoo chart request failed with "
            f"HTTP {response.status_code}."
        )

    try:
        payload = response.json()
    except ValueError as error:
        raise RuntimeError(
            "Yahoo chart endpoint returned "
            "invalid JSON."
        ) from error

    chart = payload.get(
        "chart",
        {},
    )

    chart_error = chart.get(
        "error"
    )

    if chart_error:
        description = (
            chart_error.get("description")
            if isinstance(
                chart_error,
                dict,
            )
            else str(chart_error)
        )

        raise RuntimeError(
            "Yahoo chart request failed: "
            f"{description}"
        )

    results = chart.get(
        "result"
    ) or []

    if not results:
        raise ValueError(
            f"No Yahoo chart data found for "
            f"{symbol}."
        )

    result = results[0]

    timestamps = result.get(
        "timestamp"
    ) or []

    quote_data = (
        result
        .get("indicators", {})
        .get("quote", [{}])[0]
    )

    if not timestamps:
        raise ValueError(
            f"No Yahoo chart timestamps found "
            f"for {symbol}."
        )

    row_count = len(timestamps)

    def values_for(field_name):
        values = quote_data.get(
            field_name
        )

        if (
            not isinstance(values, list)
            or len(values) != row_count
        ):
            return [None] * row_count

        return values

    data = pd.DataFrame(
        {
            "Open": values_for("open"),
            "High": values_for("high"),
            "Low": values_for("low"),
            "Close": values_for("close"),
            "Volume": values_for("volume"),
        },
        index=pd.to_datetime(
            timestamps,
            unit="s",
            utc=True,
        ),
    )

    data.index.name = "Date"

    cleaned = _clean_market_data(
        data
    )

    cleaned.attrs[
        "data_source"
    ] = "Yahoo Finance Chart API"

    cleaned.attrs[
        "is_fallback"
    ] = True

    return cleaned


def fetch_market_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
):
    """
    Fetch historical OHLCV market data.

    Priority:
    1. yfinance
    2. Yahoo chart endpoint
    """

    if not symbol or not symbol.strip():
        raise ValueError(
            "Stock symbol is required."
        )

    normalized_symbol = (
        symbol.strip().upper()
    )

    primary_error = None

    try:
        ticker = yf.Ticker(
            normalized_symbol
        )

        data = ticker.history(
            period=period,
            interval=interval,
            auto_adjust=False,
        )

        cleaned = _clean_market_data(
            data
        )

        cleaned.attrs[
            "data_source"
        ] = "yfinance"

        cleaned.attrs[
            "is_fallback"
        ] = False

        return cleaned

    except Exception as error:
        primary_error = error

    try:
        return _fetch_yahoo_chart_data(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
        )

    except Exception as fallback_error:
        raise ValueError(
            f"No market data found for "
            f"{normalized_symbol}. "
            f"Primary source: {primary_error}. "
            f"Fallback source: {fallback_error}"
        ) from fallback_error


def get_latest_market_snapshot(
    symbol: str,
):
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
        "symbol": symbol.strip().upper(),
        "date": (
            data.index[-1]
            .strftime("%Y-%m-%d")
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
        "data_source": data.attrs.get(
            "data_source"
        ),
        "is_fallback": data.attrs.get(
            "is_fallback",
            False,
        ),
    }