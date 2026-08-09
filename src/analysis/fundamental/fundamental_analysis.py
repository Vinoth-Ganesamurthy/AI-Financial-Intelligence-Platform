"""
Fundamental Analysis Module.

Retrieves and normalizes current fundamental metrics
for a company using Yahoo Finance data.
"""

import yfinance as yf


def _percentage(value):
    """
    Convert decimal ratio to percentage.
    Example: 0.255 -> 25.5
    """
    if value is None:
        return None

    return round(float(value) * 100, 2)


def _number(value):
    """
    Safely convert a numeric value.
    """
    if value is None:
        return None

    return round(float(value), 2)


def fetch_fundamental_data(symbol: str):
    """
    Fetch latest available fundamental information.
    """

    if not symbol:
        raise ValueError("Stock symbol is required.")

    ticker = yf.Ticker(symbol)

    info = ticker.info

    if not info:
        raise ValueError(
            f"No fundamental data found for {symbol}."
        )

    return {
        "symbol": symbol,

        # Company information
        "company_name": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "currency": info.get("currency"),

        # Size
        "market_cap": info.get("marketCap"),
        "total_revenue": info.get("totalRevenue"),

        # Valuation
        "trailing_pe": _number(
            info.get("trailingPE")
        ),
        "forward_pe": _number(
            info.get("forwardPE")
        ),
        "price_to_book": _number(
            info.get("priceToBook")
        ),

        # Profitability
        "profit_margin": _percentage(
            info.get("profitMargins")
        ),
        "return_on_equity": _percentage(
            info.get("returnOnEquity")
        ),
        "return_on_assets": _percentage(
            info.get("returnOnAssets")
        ),

        # Growth
        "revenue_growth": _percentage(
            info.get("revenueGrowth")
        ),
        "earnings_growth": _percentage(
            info.get("earningsGrowth")
        ),

        # Financial position
        "debt_to_equity": _number(
            info.get("debtToEquity")
        ),

        # Cash generation
        "free_cash_flow": info.get(
            "freeCashflow"
        ),
    }