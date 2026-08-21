"""
Fundamental Analysis Module.

Retrieves and normalizes current fundamental metrics.
Yahoo Finance is the primary source. Finnhub and the
direct Yahoo Finance endpoints provide resilient fallbacks.
"""

import math
import os
import time

import requests
import yfinance as yf
from curl_cffi import requests as browser_requests
from dotenv import load_dotenv


load_dotenv()

FINNHUB_PROFILE_URL = (
    "https://finnhub.io/api/v1/stock/profile2"
)

FINNHUB_METRIC_URL = (
    "https://finnhub.io/api/v1/stock/metric"
)

YAHOO_SEARCH_URL = (
    "https://query2.finance.yahoo.com/"
    "v1/finance/search"
)

YAHOO_FUNDAMENTALS_URL = (
    "https://query2.finance.yahoo.com/"
    "ws/fundamentals-timeseries/v1/finance/"
    "timeseries/{symbol}"
)

YAHOO_CHART_URL = (
    "https://query2.finance.yahoo.com/"
    "v8/finance/chart/{symbol}"
)

YAHOO_FUNDAMENTAL_TYPES = (
    "annualTotalRevenue",
    "annualNetIncome",
    "annualStockholdersEquity",
    "annualTotalAssets",
    "annualTotalDebt",
    "annualFreeCashFlow",
    "annualDilutedAverageShares",
    "annualOrdinarySharesNumber",
)


def _as_float(value):
    """Safely convert a value to a finite float."""

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
    """Convert a decimal ratio to a percentage."""

    numeric_value = _as_float(value)

    if numeric_value is None:
        return None

    return round(
        numeric_value * 100,
        2,
    )


def _number(value):
    """Safely convert and round a numeric value."""

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
    """Return the first available Finnhub metric."""

    for metric_name in metric_names:
        value = _number(
            metrics.get(metric_name)
        )

        if value is not None:
            return value

    return None


def _millions_to_units(value):
    """Convert a value expressed in millions into units."""

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
    """Estimate a total value from a per-share value."""

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


def _safe_ratio(
    numerator,
    denominator,
    *,
    as_percentage=False,
):
    """Safely divide two values."""

    numerator_value = _as_float(
        numerator
    )
    denominator_value = _as_float(
        denominator
    )

    if (
        numerator_value is None
        or denominator_value in (None, 0)
    ):
        return None

    result = (
        numerator_value
        / denominator_value
    )

    if as_percentage:
        result *= 100

    return round(result, 2)


def _growth_percentage(
    latest,
    previous,
):
    """Calculate percentage growth between two values."""

    latest_value = _as_float(latest)
    previous_value = _as_float(previous)

    if (
        latest_value is None
        or previous_value is None
        or previous_value <= 0
    ):
        return None

    return round(
        (
            latest_value
            / abs(previous_value)
            - 1
        )
        * 100,
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

    total_revenue = _per_share_to_total(
        metrics.get("revenuePerShareTTM"),
        shares_outstanding,
    )

    free_cash_flow = _per_share_to_total(
        metrics.get("freeCashFlowPerShareTTM"),
        shares_outstanding,
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
            profile.get("marketCapitalization")
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


def _get_yahoo_browser_json(
    url,
    params,
    request_name,
):
    """Fetch Yahoo JSON using browser impersonation."""

    try:
        response = browser_requests.get(
            url,
            params=params,
            impersonate="chrome",
            timeout=20,
        )
    except Exception as error:
        raise RuntimeError(
            f"Yahoo direct {request_name} request failed."
        ) from error

    if response.status_code != 200:
        raise RuntimeError(
            f"Yahoo direct {request_name} request "
            f"failed with HTTP {response.status_code}."
        )

    try:
        payload = response.json()
    except ValueError as error:
        raise RuntimeError(
            f"Yahoo direct {request_name} returned "
            "invalid JSON."
        ) from error

    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Yahoo direct {request_name} returned "
            "an invalid response."
        )

    return payload


def _extract_timeseries_values(
    series_results,
    series_name,
):
    """Return chronological raw values for one series."""

    observations = []

    for series in series_results:
        values = series.get(series_name)

        if not isinstance(values, list):
            continue

        for observation in values:
            reported_value = observation.get(
                "reportedValue",
                {},
            )

            raw_value = _as_float(
                reported_value.get("raw")
                if isinstance(reported_value, dict)
                else reported_value
            )

            if raw_value is None:
                continue

            observations.append(
                (
                    observation.get("asOfDate") or "",
                    raw_value,
                )
            )

    observations.sort(
        key=lambda item: item[0]
    )

    return [
        value
        for _, value in observations
    ]


def _extract_timeseries_currency(
    series_results,
):
    """Return the first reported statement currency."""

    for series in series_results:
        for series_name in YAHOO_FUNDAMENTAL_TYPES:
            observations = series.get(series_name)

            if not isinstance(observations, list):
                continue

            for observation in observations:
                currency = observation.get(
                    "currencyCode"
                )

                if currency:
                    return currency

    return None


def _latest_chart_price(chart_payload):
    """Extract the latest price from a Yahoo chart response."""

    chart_results = (
        chart_payload
        .get("chart", {})
        .get("result", [])
    )

    if not chart_results:
        return None

    chart_result = chart_results[0]
    chart_meta = chart_result.get("meta", {})

    regular_market_price = _as_float(
        chart_meta.get("regularMarketPrice")
    )

    if regular_market_price is not None:
        return regular_market_price

    quote_blocks = (
        chart_result
        .get("indicators", {})
        .get("quote", [])
    )

    for quote_block in reversed(quote_blocks):
        close_values = quote_block.get(
            "close",
            [],
        )

        for close_value in reversed(close_values):
            numeric_close = _as_float(
                close_value
            )

            if numeric_close is not None:
                return numeric_close

    return None


def _get_yahoo_exchange_rate(
    source_currency,
    target_currency,
):
    """Return the Yahoo FX rate between two currencies."""

    if (
        not source_currency
        or not target_currency
        or source_currency == target_currency
    ):
        return 1.0

    if source_currency == "USD":
        direct_symbol = (
            f"{target_currency}=X"
        )
    else:
        direct_symbol = (
            f"{source_currency}"
            f"{target_currency}=X"
        )

    try:
        direct_payload = _get_yahoo_browser_json(
            YAHOO_CHART_URL.format(
                symbol=direct_symbol
            ),
            {
                "range": "5d",
                "interval": "1d",
            },
            "currency-conversion",
        )

        direct_rate = _latest_chart_price(
            direct_payload
        )

        if direct_rate not in (None, 0):
            return direct_rate

    except Exception:
        pass

    if target_currency == "USD":
        inverse_symbol = (
            f"{source_currency}=X"
        )
    else:
        inverse_symbol = (
            f"{target_currency}"
            f"{source_currency}=X"
        )

    inverse_payload = _get_yahoo_browser_json(
        YAHOO_CHART_URL.format(
            symbol=inverse_symbol
        ),
        {
            "range": "5d",
            "interval": "1d",
        },
        "inverse-currency-conversion",
    )

    inverse_rate = _latest_chart_price(
        inverse_payload
    )

    if inverse_rate in (None, 0):
        raise ValueError(
            "Yahoo direct currency conversion "
            "returned no usable exchange rate."
        )

    return 1 / inverse_rate


def _convert_currency_value(
    value,
    exchange_rate,
):
    """Convert and round one monetary value."""

    numeric_value = _as_float(value)
    numeric_rate = _as_float(exchange_rate)

    if (
        numeric_value is None
        or numeric_rate is None
    ):
        return None

    return round(
        numeric_value * numeric_rate,
        2,
    )


def _fetch_yahoo_direct_fundamental_data(
    symbol: str,
):
    """
    Fetch company identity and annual fundamentals
    from Yahoo's direct JSON endpoints.
    """

    search_payload = _get_yahoo_browser_json(
        YAHOO_SEARCH_URL,
        {
            "q": symbol,
            "quotesCount": 10,
            "newsCount": 0,
        },
        "company-search",
    )

    quote = next(
        (
            item
            for item in search_payload.get(
                "quotes",
                [],
            )
            if (
                item.get("symbol", "").upper()
                == symbol
            )
        ),
        None,
    )

    if not quote:
        raise ValueError(
            f"No Yahoo direct company data found "
            f"for {symbol}."
        )

    chart_payload = _get_yahoo_browser_json(
        YAHOO_CHART_URL.format(
            symbol=symbol
        ),
        {
            "range": "5d",
            "interval": "1d",
            "events": "div,splits",
        },
        "chart-metadata",
    )

    chart_results = (
        chart_payload
        .get("chart", {})
        .get("result", [])
    )

    chart_meta = (
        chart_results[0].get("meta", {})
        if chart_results
        else {}
    )

    current_timestamp = int(time.time())

    fundamentals_payload = (
        _get_yahoo_browser_json(
            YAHOO_FUNDAMENTALS_URL.format(
                symbol=symbol
            ),
            {
                "symbol": symbol,
                "type": ",".join(
                    YAHOO_FUNDAMENTAL_TYPES
                ),
                "period1": (
                    current_timestamp
                    - 10 * 365 * 24 * 60 * 60
                ),
                "period2": (
                    current_timestamp
                    + 24 * 60 * 60
                ),
            },
            "fundamentals-timeseries",
        )
    )

    timeseries = fundamentals_payload.get(
        "timeseries",
        {},
    )

    series_results = timeseries.get(
        "result",
        [],
    )

    if not isinstance(series_results, list):
        raise ValueError(
            f"No Yahoo direct fundamentals found "
            f"for {symbol}."
        )

    revenue_values = _extract_timeseries_values(
        series_results,
        "annualTotalRevenue",
    )
    net_income_values = _extract_timeseries_values(
        series_results,
        "annualNetIncome",
    )
    equity_values = _extract_timeseries_values(
        series_results,
        "annualStockholdersEquity",
    )
    asset_values = _extract_timeseries_values(
        series_results,
        "annualTotalAssets",
    )
    debt_values = _extract_timeseries_values(
        series_results,
        "annualTotalDebt",
    )
    cash_flow_values = _extract_timeseries_values(
        series_results,
        "annualFreeCashFlow",
    )
    diluted_share_values = (
        _extract_timeseries_values(
            series_results,
            "annualDilutedAverageShares",
        )
    )
    ordinary_share_values = (
        _extract_timeseries_values(
            series_results,
            "annualOrdinarySharesNumber",
        )
    )

    latest_revenue = (
        revenue_values[-1]
        if revenue_values
        else None
    )
    latest_net_income = (
        net_income_values[-1]
        if net_income_values
        else None
    )
    latest_equity = (
        equity_values[-1]
        if equity_values
        else None
    )
    latest_assets = (
        asset_values[-1]
        if asset_values
        else None
    )
    latest_debt = (
        debt_values[-1]
        if debt_values
        else None
    )
    latest_free_cash_flow = (
        cash_flow_values[-1]
        if cash_flow_values
        else None
    )
    latest_shares = (
        diluted_share_values[-1]
        if diluted_share_values
        else (
            ordinary_share_values[-1]
            if ordinary_share_values
            else None
        )
    )

    statement_currency = (
        _extract_timeseries_currency(
            series_results
        )
    )

    trading_currency = (
        quote.get("currency")
        or chart_meta.get("currency")
        or statement_currency
    )

    exchange_rate = _get_yahoo_exchange_rate(
        statement_currency,
        trading_currency,
    )

    converted_revenue = _convert_currency_value(
        latest_revenue,
        exchange_rate,
    )
    converted_net_income = (
        _convert_currency_value(
            latest_net_income,
            exchange_rate,
        )
    )
    converted_equity = _convert_currency_value(
        latest_equity,
        exchange_rate,
    )
    converted_free_cash_flow = (
        _convert_currency_value(
            latest_free_cash_flow,
            exchange_rate,
        )
    )

    if not any(
        value is not None
        for value in (
            latest_revenue,
            latest_net_income,
            latest_equity,
            latest_assets,
            latest_debt,
            latest_free_cash_flow,
        )
    ):
        raise ValueError(
            f"No Yahoo direct financial metrics found "
            f"for {symbol}."
        )

    market_cap = _number(
        quote.get("marketCap")
    )

    if market_cap is None:
        market_cap = _number(
            (
                _as_float(
                    chart_meta.get(
                        "regularMarketPrice"
                    )
                )
                or 0
            )
            * (
                _as_float(latest_shares)
                or 0
            )
        )

        if market_cap == 0:
            market_cap = None

    trailing_pe = _number(
        quote.get("trailingPE")
    )

    if trailing_pe is None:
        trailing_pe = _safe_ratio(
            market_cap,
            converted_net_income,
        )

    price_to_book = _number(
        quote.get("priceToBook")
    )

    if price_to_book is None:
        price_to_book = _safe_ratio(
            market_cap,
            converted_equity,
        )

    return {
        "symbol": symbol,
        "company_name": (
            quote.get("longname")
            or quote.get("shortname")
        ),
        "sector": (
            quote.get("sector")
            or quote.get("sectorDisp")
        ),
        "industry": (
            quote.get("industry")
            or quote.get("industryDisp")
        ),
        "currency": trading_currency,
        "market_cap": market_cap,
        "total_revenue": _number(
            converted_revenue
        ),
        "trailing_pe": trailing_pe,
        "forward_pe": _number(
            quote.get("forwardPE")
        ),
        "price_to_book": price_to_book,
        "profit_margin": _safe_ratio(
            latest_net_income,
            latest_revenue,
            as_percentage=True,
        ),
        "return_on_equity": _safe_ratio(
            latest_net_income,
            latest_equity,
            as_percentage=True,
        ),
        "return_on_assets": _safe_ratio(
            latest_net_income,
            latest_assets,
            as_percentage=True,
        ),
        "revenue_growth": (
            _growth_percentage(
                revenue_values[-1],
                revenue_values[-2],
            )
            if len(revenue_values) >= 2
            else None
        ),
        "earnings_growth": (
            _growth_percentage(
                net_income_values[-1],
                net_income_values[-2],
            )
            if len(net_income_values) >= 2
            else None
        ),
        "debt_to_equity": _safe_ratio(
            latest_debt,
            latest_equity,
        ),
        "free_cash_flow": _number(
            converted_free_cash_flow
        ),
        "data_source": "Yahoo Finance Direct",
        "is_fallback": True,
    }


def fetch_fundamental_data(
    symbol: str,
):
    """
    Fetch the latest available fundamental data.

    Priority:
    1. Yahoo Finance through yfinance
    2. Finnhub fallback
    3. Direct Yahoo Finance fallback
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
            "total_revenue": info.get("totalRevenue"),
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

    finnhub_error = None

    try:
        return _fetch_finnhub_fundamental_data(
            normalized_symbol
        )

    except Exception as error:
        finnhub_error = error

    try:
        return _fetch_yahoo_direct_fundamental_data(
            normalized_symbol
        )

    except Exception as yahoo_direct_error:
        raise ValueError(
            f"No fundamental data found for "
            f"{normalized_symbol}. "
            f"Yahoo Finance: {yahoo_error}. "
            f"Finnhub fallback: {finnhub_error}. "
            "Yahoo direct fallback: "
            f"{yahoo_direct_error}"
        ) from yahoo_direct_error