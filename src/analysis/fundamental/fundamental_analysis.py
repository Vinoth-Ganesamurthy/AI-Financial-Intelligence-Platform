"""
Fundamental Analysis Module.

Retrieves and normalizes current fundamental metrics.
Yahoo Finance is the primary source and Finnhub is the
fallback when Yahoo is unavailable or rate-limited.
"""

import math
import os

import requests
import yfinance as yf
from dotenv import load_dotenv


load_dotenv()

FINNHUB_PROFILE_URL = (
    "https://finnhub.io/api/v1/stock/profile2"
)

FINNHUB_METRIC_URL = (
    "https://finnhub.io/api/v1/stock/metric"
)


def _as_float(value):
    """
    Safely convert a value to a finite float.
    """

    if value is None:
        return None

    try:
        result = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(result):
        return None

    return result


def _percentage(value):
    """
    Convert a decimal ratio to a percentage.

    Example:
        0.255 -> 25.5
    """

    numeric_value = _as_float(value)

    if numeric_value is None:
        return None

    return round(
        numeric_value * 100,
        2,
    )


def _number(value):
    """
    Safely convert and round a numeric value.
    """

    numeric_value = _as_float(value)

    if numeric_value is None:
        return None

    return round(
        numeric_value,
        2,
    )


def _metric_number(
    metrics,
    *metric_names,
):
    """
    Return the first available Finnhub metric.
    """

    for metric_name in metric_names:
        value = _number(
            metrics.get(metric_name)
        )

        if value is not None:
            return value

    return None


def _millions_to_units(value):
    """
    Convert a value expressed in millions into units.
    """

    numeric_value = _as_float(value)

    if numeric_value is None:
        return None

    return round(
        numeric_value * 1_000_000,
        2,
    )


def _per_share_to_total(
    per_share_value,
    shares_outstanding_millions,
):
    """
    Estimate a total value from a per-share value.
    """

    per_share = _as_float(
        per_share_value
    )

    shares_millions = _as_float(
        shares_outstanding_millions
    )

    if (
        per_share is None
        or shares_millions is None
    ):
        return None

    return round(
        per_share
        * shares_millions
        * 1_000_000,
        2,
    )


def _get_finnhub_json(
    url,
    params,
    request_name,
):
    """
    Fetch Finnhub JSON without exposing the API key
    in application error messages.
    """

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15,
        )
    except requests.RequestException as error:
        raise RuntimeError(
            f"Finnhub {request_name} request failed."
        ) from error

    if response.status_code != 200:
        raise RuntimeError(
            f"Finnhub {request_name} request failed "
            f"with HTTP {response.status_code}."
        )

    try:
        payload = response.json()
    except ValueError as error:
        raise RuntimeError(
            f"Finnhub {request_name} returned "
            "invalid JSON."
        ) from error

    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Finnhub {request_name} returned "
            "an invalid response."
        )

    return payload


def _fetch_finnhub_fundamental_data(
    symbol: str,
):
    """
    Fetch fallback company profile and financial
    metrics from Finnhub.
    """

    api_key = os.getenv(
        "FINNHUB_API_KEY"
    )

    if not api_key:
        raise ValueError(
            "FINNHUB_API_KEY is missing."
        )

    profile = _get_finnhub_json(
        FINNHUB_PROFILE_URL,
        {
            "symbol": symbol,
            "token": api_key,
        },
        "company-profile",
    )

    metric_payload = _get_finnhub_json(
        FINNHUB_METRIC_URL,
        {
            "symbol": symbol,
            "metric": "all",
            "token": api_key,
        },
        "financial-metrics",
    )

    metrics = metric_payload.get(
        "metric",
        {},
    )

    if (
        not profile.get("name")
        or not isinstance(metrics, dict)
        or not metrics
    ):
        raise ValueError(
            f"No Finnhub fundamental data found "
            f"for {symbol}."
        )

    shares_outstanding = profile.get(
        "shareOutstanding"
    )

    total_revenue = (
        _per_share_to_total(
            metrics.get(
                "revenuePerShareTTM"
            ),
            shares_outstanding,
        )
    )

    free_cash_flow = (
        _per_share_to_total(
            metrics.get(
                "freeCashFlowPerShareTTM"
            ),
            shares_outstanding,
        )
    )

    industry = profile.get(
        "finnhubIndustry"
    )

    return {
        "symbol": symbol,
        "company_name": profile.get("name"),
        "sector": industry,
        "industry": industry,
        "currency": profile.get("currency"),
        "market_cap": _millions_to_units(
            profile.get(
                "marketCapitalization"
            )
        ),
        "total_revenue": total_revenue,
        "trailing_pe": _metric_number(
            metrics,
            "peBasicExclExtraTTM",
            "peExclExtraTTM",
            "peTTM",
        ),
        "forward_pe": None,
        "price_to_book": _metric_number(
            metrics,
            "pbQuarterly",
            "pbAnnual",
        ),
        "profit_margin": _metric_number(
            metrics,
            "netProfitMarginTTM",
            "netProfitMarginAnnual",
        ),
        "return_on_equity": _metric_number(
            metrics,
            "roeTTM",
            "roeRfy",
        ),
        "return_on_assets": _metric_number(
            metrics,
            "roaTTM",
            "roaRfy",
        ),
        "revenue_growth": _metric_number(
            metrics,
            "revenueGrowthTTMYoy",
            "revenueGrowthQuarterlyYoy",
        ),
        "earnings_growth": _metric_number(
            metrics,
            "epsGrowthTTMYoy",
            "epsGrowthQuarterlyYoy",
        ),
        "debt_to_equity": _metric_number(
            metrics,
            "totalDebt/totalEquityQuarterly",
            "totalDebt/totalEquityAnnual",
        ),
        "free_cash_flow": free_cash_flow,
        "data_source": "Finnhub",
        "is_fallback": True,
    }


def fetch_fundamental_data(
    symbol: str,
):
    """
    Fetch the latest available fundamental data.

    Priority:
    1. Yahoo Finance
    2. Finnhub fallback
    """

    if not symbol or not symbol.strip():
        raise ValueError(
            "Stock symbol is required."
        )

    normalized_symbol = (
        symbol.strip().upper()
    )

    yahoo_error = None

    try:
        ticker = yf.Ticker(
            normalized_symbol
        )

        info = ticker.info

        company_name = (
            info.get("longName")
            or info.get("shortName")
            if info
            else None
        )

        if not info or not company_name:
            raise ValueError(
                "Yahoo Finance returned no "
                "company information."
            )

        return {
            "symbol": normalized_symbol,
            "company_name": company_name,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "currency": info.get("currency"),
            "market_cap": info.get("marketCap"),
            "total_revenue": info.get(
                "totalRevenue"
            ),
            "trailing_pe": _number(
                info.get("trailingPE")
            ),
            "forward_pe": _number(
                info.get("forwardPE")
            ),
            "price_to_book": _number(
                info.get("priceToBook")
            ),
            "profit_margin": _percentage(
                info.get("profitMargins")
            ),
            "return_on_equity": _percentage(
                info.get("returnOnEquity")
            ),
            "return_on_assets": _percentage(
                info.get("returnOnAssets")
            ),
            "revenue_growth": _percentage(
                info.get("revenueGrowth")
            ),
            "earnings_growth": _percentage(
                info.get("earningsGrowth")
            ),
            "debt_to_equity": _number(
                info.get("debtToEquity")
            ),
            "free_cash_flow": info.get(
                "freeCashflow"
            ),
            "data_source": "Yahoo Finance",
            "is_fallback": False,
        }

    except Exception as error:
        yahoo_error = error

    try:
        return _fetch_finnhub_fundamental_data(
            normalized_symbol
        )

    except Exception as finnhub_error:
        raise ValueError(
            f"No fundamental data found for "
            f"{normalized_symbol}. "
            f"Yahoo Finance: {yahoo_error}. "
            f"Finnhub fallback: {finnhub_error}"
        ) from finnhub_error