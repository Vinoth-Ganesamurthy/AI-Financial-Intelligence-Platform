"""
Country / Market Configuration

Defines the market-specific context used
for macroeconomic and market analysis.
"""


MARKET_CONFIG = {
    # ==================================================
    # United States
    # ==================================================
    "US": {
        "country": "United States",
        "currency": "USD",

        "stock_suffixes": [
            "",
        ],

        "market_indices": {
            "broad_market": "^GSPC",   # S&P 500
            "technology": "^IXIC",     # NASDAQ Composite
        },

        "currency_pairs": {
            "dollar_index": "DX-Y.NYB",
        },

        "volatility_index": "^VIX",

        "bond_yield_symbol": "^TNX",

        "commodities": {
            "crude_oil": "CL=F",
            "gold": "GC=F",
        },

        "macro_sources": {
            "policy_rate": "FRED",
            "inflation": "FRED",
            "gdp": "FRED",
            "unemployment": "FRED",
        },
    },

    # ==================================================
    # India
    # ==================================================
    "IN": {
        "country": "India",
        "currency": "INR",

        "stock_suffixes": [
            ".NS",
            ".BO",
        ],

        "market_indices": {
            "broad_market": "^NSEI",   # NIFTY 50
            "banking": "^NSEBANK",
        },

        "currency_pairs": {
            "usd_local": "INR=X",
        },

        "volatility_index": "^INDIAVIX",

        "bond_yield_symbol": None,

        "commodities": {
            "crude_oil": "CL=F",
            "gold": "GC=F",
        },

        "macro_sources": {
            "policy_rate": "RBI",
            "inflation": "MOSPI",
            "gdp": "MOSPI",
            "unemployment": "WORLD_BANK",
        },
    },

    # ==================================================
    # Singapore
    # ==================================================
    "SG": {
        "country": "Singapore",
        "currency": "SGD",

        "stock_suffixes": [
            ".SI",
        ],

        "market_indices": {
            "broad_market": "^STI",
        },

        "currency_pairs": {
            "usd_local": "SGD=X",
        },

        "volatility_index": None,

        "bond_yield_symbol": None,

        "commodities": {
            "crude_oil": "CL=F",
            "gold": "GC=F",
        },

        "macro_sources": {
            "policy_rate": "MAS",
            "inflation": "SINGSTAT",
            "gdp": "SINGSTAT",
            "unemployment": "SINGSTAT",
        },
    },

    # ==================================================
    # Australia
    # ==================================================
    "AU": {
        "country": "Australia",
        "currency": "AUD",

        "stock_suffixes": [
            ".AX",
        ],

        "market_indices": {
            "broad_market": "^AXJO",   # S&P/ASX 200
        },

        "currency_pairs": {
            "usd_local": "AUDUSD=X",
        },

        "volatility_index": None,

        "bond_yield_symbol": None,

        "commodities": {
            "crude_oil": "CL=F",
            "gold": "GC=F",
        },

        "macro_sources": {
            "policy_rate": "RBA",
            "inflation": "ABS",
            "gdp": "ABS",
            "unemployment": "ABS",
        },
    },
}


def detect_market(symbol: str):
    """
    Detect market from a Yahoo Finance symbol.
    """

    if not symbol:
        return None

    symbol = symbol.upper().strip()

    if symbol.endswith(".NS") or symbol.endswith(".BO"):
        return "IN"

    if symbol.endswith(".SI"):
        return "SG"

    if symbol.endswith(".AX"):
        return "AU"

    # Default unsupported suffixes to US
    # for Version 1.
    return "US"


def get_market_config(symbol: str):
    """
    Return market configuration for a stock symbol.
    """

    market = detect_market(symbol)

    if market is None:
        raise ValueError(
            "Unable to determine stock market."
        )

    config = MARKET_CONFIG.get(market)

    if config is None:
        raise ValueError(
            f"Unsupported market: {market}"
        )

    return {
        "market_code": market,
        **config,
    }