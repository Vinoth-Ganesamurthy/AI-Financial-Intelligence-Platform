"""
Macroeconomic Analysis Module

Converts country-specific macroeconomic snapshots into
normalized numerical features and economic interpretations.
"""

from src.data.macro.macro_sources import (
    fetch_macro_snapshot_for_symbol,
)


# ======================================================
# Safe Numeric Extraction
# ======================================================

def _extract_numeric_value(indicator):
    """
    Safely extract the primary numerical value from
    a macroeconomic indicator.
    """

    if not indicator:
        return None

    value = indicator.get("value")

    if value is None:
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


# ======================================================
# Raw ML Features
# ======================================================

def build_macro_features(
    stock_symbol: str,
):
    """
    Build normalized raw numerical macroeconomic features.

    These values can later be supplied to scoring models,
    machine-learning pipelines, and investment analysis.
    """

    snapshot = (
        fetch_macro_snapshot_for_symbol(
            stock_symbol
        )
    )

    inflation = snapshot.get(
        "inflation"
    )

    policy_rate = snapshot.get(
        "policy_rate"
    )

    gdp_growth = snapshot.get(
        "gdp_growth"
    )

    unemployment = snapshot.get(
        "unemployment"
    )

    return {
        "stock_symbol": snapshot.get(
            "stock_symbol"
        ),

        "market_code": snapshot.get(
            "market_code"
        ),

        "country": snapshot.get(
            "country"
        ),

        # Raw numerical ML features
        "inflation_rate": (
            _extract_numeric_value(
                inflation
            )
        ),

        "monetary_rate": (
            _extract_numeric_value(
                policy_rate
            )
        ),

        "gdp_growth_rate": (
            _extract_numeric_value(
                gdp_growth
            )
        ),

        "unemployment_rate": (
            _extract_numeric_value(
                unemployment
            )
        ),

        # Identifies whether monetary_rate is an
        # actual policy rate or a market-rate proxy.
        "monetary_rate_is_policy_rate": (
            int(
                policy_rate.get(
                    "is_policy_rate",
                    True,
                )
            )
            if policy_rate
            else None
        ),

        # Data-quality flags
        "inflation_is_cached": (
            int(
                inflation.get(
                    "is_cached",
                    False,
                )
            )
            if inflation
            else None
        ),

        "policy_rate_is_cached": (
            int(
                policy_rate.get(
                    "is_cached",
                    False,
                )
            )
            if policy_rate
            else None
        ),

        "gdp_is_fallback": (
            int(
                gdp_growth.get(
                    "is_fallback",
                    False,
                )
            )
            if gdp_growth
            else None
        ),

        "unemployment_is_cached": (
            int(
                unemployment.get(
                    "is_cached",
                    False,
                )
            )
            if unemployment
            else None
        ),
    }

# --------------------------------------------------
# Inflation Framework Configuration
# --------------------------------------------------

INFLATION_FRAMEWORKS = {
    "US": {
        "framework_name": "Federal Reserve price stability goal",
        "target_rate": 2.0,
        "lower_bound": None,
        "upper_bound": None,
        "target_measure": "PCE Inflation",
        "input_measure": "CPI Inflation",
        "explicit_target_range": False,
        "comparison_is_approximate": True,
    },
    "IN": {
        "framework_name": "RBI flexible inflation targeting framework",
        "target_rate": 4.0,
        "lower_bound": 2.0,
        "upper_bound": 6.0,
        "target_measure": "CPI Inflation",
        "input_measure": "CPI Inflation",
        "explicit_target_range": True,
        "comparison_is_approximate": False,
    },
    "SG": {
        "framework_name": "MAS exchange-rate-centred monetary policy",
        "target_rate": None,
        "lower_bound": None,
        "upper_bound": None,
        "reference_rate": 2.0,
        "target_measure": "CPI Inflation",
        "input_measure": "CPI Inflation",
        "explicit_target_range": False,
        "comparison_is_approximate": False,
    },
    "AU": {
        "framework_name": "RBA flexible inflation targeting framework",
        "target_rate": 2.5,
        "lower_bound": 2.0,
        "upper_bound": 3.0,
        "target_measure": "CPI Inflation",
        "input_measure": "CPI Inflation",
        "explicit_target_range": True,
        "comparison_is_approximate": False,
    },
}


# --------------------------------------------------
# Country-Specific Inflation Interpretation
# --------------------------------------------------

def interpret_inflation(
    market_code: str,
    inflation_rate,
):
    """
    Interpret inflation according to the country's
    monetary-policy framework.

    Inflation score:
         1 = favourable or price-stable
         0 = neutral or unavailable
        -1 = moderately unfavourable
        -2 = strongly unfavourable
    """

    normalized_market = (
        market_code.strip().upper()
        if market_code
        else None
    )

    framework = INFLATION_FRAMEWORKS.get(
        normalized_market
    )

    if framework is None:
        return {
            "status": "unsupported_market",
            "score": 0,
            "summary": (
                "Inflation framework is unavailable "
                f"for market {normalized_market}."
            ),
        }

    try:
        rate = float(inflation_rate)

    except (TypeError, ValueError):
        return {
            "status": "unavailable",
            "score": 0,
            "inflation_rate": None,
            "framework_name": framework[
                "framework_name"
            ],
            "summary": (
                "Inflation data is unavailable."
            ),
        }

    if normalized_market == "SG":
        interpretation = (
            _interpret_singapore_inflation(rate)
        )

    elif framework["explicit_target_range"]:
        interpretation = (
            _interpret_inflation_target_range(
                rate=rate,
                target_rate=framework[
                    "target_rate"
                ],
                lower_bound=framework[
                    "lower_bound"
                ],
                upper_bound=framework[
                    "upper_bound"
                ],
            )
        )

    else:
        interpretation = (
            _interpret_us_inflation(rate)
        )

    result = {
        "inflation_rate": rate,
        "framework_name": framework[
            "framework_name"
        ],
        "target_rate": framework.get(
            "target_rate"
        ),
        "lower_bound": framework.get(
            "lower_bound"
        ),
        "upper_bound": framework.get(
            "upper_bound"
        ),
        "target_measure": framework[
            "target_measure"
        ],
        "input_measure": framework[
            "input_measure"
        ],
        "explicit_target_range": framework[
            "explicit_target_range"
        ],
        **interpretation,
    }

    if framework.get(
        "comparison_is_approximate"
    ):
        result["comparison_note"] = (
            "The Federal Reserve's 2% goal applies "
            "to PCE inflation. This platform currently "
            "uses CPI inflation, so the comparison is "
            "approximate."
        )

    if normalized_market == "SG":
        result["reference_rate"] = framework[
            "reference_rate"
        ]
        result["comparison_note"] = (
            "MAS does not use a formal numerical "
            "inflation target. The classification is "
            "an analytical price-stability heuristic."
        )

    return result


def _interpret_inflation_target_range(
    rate: float,
    target_rate: float,
    lower_bound: float,
    upper_bound: float,
):
    """
    Interpret inflation for countries with an explicit
    target or tolerance range.
    """

    deviation = round(
        rate - target_rate,
        2,
    )

    if rate < 0:
        return {
            "status": "deflation",
            "score": -2,
            "deviation_from_target": deviation,
            "summary": (
                "Inflation is negative, indicating "
                "deflation risk."
            ),
        }

    if rate < lower_bound:
        return {
            "status": "below_target_range",
            "score": -1,
            "deviation_from_target": deviation,
            "summary": (
                "Inflation is below the official "
                "target range, which may indicate "
                "weak price pressure or demand."
            ),
        }

    if rate <= upper_bound:
        return {
            "status": "within_target_range",
            "score": 1,
            "deviation_from_target": deviation,
            "summary": (
                "Inflation is within the official "
                "target or tolerance range."
            ),
        }

    if rate <= upper_bound + 2:
        return {
            "status": "above_target_range",
            "score": -1,
            "deviation_from_target": deviation,
            "summary": (
                "Inflation is moderately above the "
                "official target range."
            ),
        }

    return {
        "status": "high_inflation",
        "score": -2,
        "deviation_from_target": deviation,
        "summary": (
            "Inflation is substantially above the "
            "official target range."
        ),
    }


def _interpret_us_inflation(
    rate: float,
):
    """
    Interpret US CPI relative to the Federal Reserve's
    2% PCE inflation goal.

    This is an approximate comparison because CPI and
    PCE are different inflation measures.
    """

    deviation = round(
        rate - 2.0,
        2,
    )

    if rate < 0:
        return {
            "status": "deflation",
            "score": -2,
            "deviation_from_target": deviation,
            "summary": (
                "US CPI is negative, indicating "
                "deflation risk."
            ),
        }

    if rate < 1.5:
        return {
            "status": "low_inflation",
            "score": -1,
            "deviation_from_target": deviation,
            "summary": (
                "US CPI is relatively low compared "
                "with the Federal Reserve's price "
                "stability goal."
            ),
        }

    if rate <= 2.5:
        return {
            "status": "near_target",
            "score": 1,
            "deviation_from_target": deviation,
            "summary": (
                "US CPI is broadly near the Federal "
                "Reserve's inflation goal."
            ),
        }

    if rate <= 3.5:
        return {
            "status": "elevated_inflation",
            "score": -1,
            "deviation_from_target": deviation,
            "summary": (
                "US CPI is moderately elevated "
                "relative to the Federal Reserve's "
                "inflation goal."
            ),
        }

    return {
        "status": "high_inflation",
        "score": -2,
        "deviation_from_target": deviation,
        "summary": (
            "US CPI is substantially elevated "
            "relative to the Federal Reserve's "
            "inflation goal."
        ),
    }


def _interpret_singapore_inflation(
    rate: float,
):
    """
    Interpret Singapore inflation without treating the
    analytical thresholds as an official MAS target.
    """

    deviation = round(
        rate - 2.0,
        2,
    )

    if rate < 0:
        return {
            "status": "deflation",
            "score": -2,
            "deviation_from_reference": deviation,
            "summary": (
                "Singapore inflation is negative, "
                "indicating deflation risk."
            ),
        }

    if rate < 1.0:
        return {
            "status": "low_inflation",
            "score": 0,
            "deviation_from_reference": deviation,
            "summary": (
                "Singapore inflation is low, with "
                "limited domestic price pressure."
            ),
        }

    if rate <= 3.0:
        return {
            "status": "price_stable",
            "score": 1,
            "deviation_from_reference": deviation,
            "summary": (
                "Singapore inflation is consistent "
                "with a broadly price-stable "
                "environment."
            ),
        }

    if rate <= 5.0:
        return {
            "status": "elevated_inflation",
            "score": -1,
            "deviation_from_reference": deviation,
            "summary": (
                "Singapore inflation is elevated, "
                "indicating increased price pressure."
            ),
        }

    return {
        "status": "high_inflation",
        "score": -2,
        "deviation_from_reference": deviation,
        "summary": (
            "Singapore inflation is high, indicating "
            "substantial price pressure."
        ),
    }

def analyze_macro_inflation(
    stock_symbol: str,
):
    """
    Fetch macroeconomic features and return the
    country-aware inflation interpretation.
    """

    features = build_macro_features(
        stock_symbol
    )

    interpretation = interpret_inflation(
        market_code=features["market_code"],
        inflation_rate=features["inflation_rate"],
    )

    return {
        "stock_symbol": features["stock_symbol"],
        "market_code": features["market_code"],
        "country": features["country"],
        "inflation": interpretation,
    }