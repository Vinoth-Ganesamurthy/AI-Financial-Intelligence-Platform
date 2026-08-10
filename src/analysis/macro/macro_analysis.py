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


# --------------------------------------------------
# GDP Growth Framework Configuration
# --------------------------------------------------

GDP_GROWTH_FRAMEWORKS = {
    "US": {
        "framework_name": (
            "US annualized quarterly GDP growth"
        ),
        "growth_basis": (
            "Quarter-on-quarter annualized"
        ),
        "frequency": "quarterly",
    },
    "IN": {
        "framework_name": (
            "India annual real GDP growth"
        ),
        "growth_basis": "Annual growth",
        "frequency": "annual",
    },
    "SG": {
        "framework_name": (
            "Singapore quarterly real GDP growth"
        ),
        "growth_basis": "Quarter-on-quarter",
        "frequency": "quarterly",
    },
    "AU": {
        "framework_name": (
            "Australia quarterly real GDP growth"
        ),
        "growth_basis": "Quarter-on-quarter",
        "frequency": "quarterly",
    },
}


# --------------------------------------------------
# GDP Growth Interpretation
# --------------------------------------------------

def interpret_gdp_growth(
    market_code: str,
    gdp_growth_rate,
    is_fallback=False,
):
    """
    Interpret GDP growth using country-specific
    analytical thresholds.

    GDP score:
         2 = strong growth
         1 = stable or moderate growth
         0 = weak or flat growth
        -1 = mild contraction
        -2 = significant contraction
    """

    normalized_market = (
        market_code.strip().upper()
        if market_code
        else None
    )

    framework = GDP_GROWTH_FRAMEWORKS.get(
        normalized_market
    )

    if framework is None:
        return {
            "status": "unsupported_market",
            "score": 0,
            "summary": (
                "GDP growth framework is unavailable "
                f"for market {normalized_market}."
            ),
        }

    try:
        rate = float(gdp_growth_rate)

    except (TypeError, ValueError):
        return {
            "status": "unavailable",
            "score": 0,
            "gdp_growth_rate": None,
            "framework_name": framework[
                "framework_name"
            ],
            "growth_basis": framework[
                "growth_basis"
            ],
            "summary": (
                "GDP growth data is unavailable."
            ),
        }

    interpreters = {
        "US": _interpret_us_gdp_growth,
        "IN": _interpret_india_gdp_growth,
        "SG": _interpret_singapore_gdp_growth,
        "AU": _interpret_australia_gdp_growth,
    }

    interpretation = interpreters[
        normalized_market
    ](rate)

    fallback_flag = bool(is_fallback)

    result = {
        "gdp_growth_rate": rate,
        "framework_name": framework[
            "framework_name"
        ],
        "growth_basis": framework[
            "growth_basis"
        ],
        "frequency": framework["frequency"],
        "is_fallback": fallback_flag,
        **interpretation,
    }

    if fallback_flag:
        result["data_quality"] = "fallback_source"
        result["data_quality_note"] = (
            "GDP growth was obtained from a fallback "
            "source and may have a different frequency "
            "or publication schedule from the preferred "
            "official domestic source."
        )
    else:
        result["data_quality"] = "official_source"

    result["threshold_note"] = (
        "GDP classifications use analytical thresholds "
        "for investment analysis and are not official "
        "government classifications."
    )

    return result


def _interpret_us_gdp_growth(
    rate: float,
):
    """
    Interpret US annualized quarterly GDP growth.
    """

    if rate < -1.0:
        return {
            "status": "significant_contraction",
            "score": -2,
            "summary": (
                "US real GDP is contracting at a "
                "significant annualized rate."
            ),
        }

    if rate < 0:
        return {
            "status": "mild_contraction",
            "score": -1,
            "summary": (
                "US real GDP is experiencing a mild "
                "annualized contraction."
            ),
        }

    if rate < 1.0:
        return {
            "status": "weak_growth",
            "score": 0,
            "summary": (
                "US real GDP growth is positive but "
                "relatively weak."
            ),
        }

    if rate <= 3.0:
        return {
            "status": "moderate_growth",
            "score": 1,
            "summary": (
                "US real GDP is growing at a moderate "
                "annualized rate."
            ),
        }

    return {
        "status": "strong_growth",
        "score": 2,
        "summary": (
            "US real GDP is growing at a strong "
            "annualized rate."
        ),
    }


def _interpret_india_gdp_growth(
    rate: float,
):
    """
    Interpret India's annual real GDP growth.
    """

    if rate < -2.0:
        return {
            "status": "significant_contraction",
            "score": -2,
            "summary": (
                "India's real GDP is experiencing a "
                "significant annual contraction."
            ),
        }

    if rate < 0:
        return {
            "status": "mild_contraction",
            "score": -1,
            "summary": (
                "India's real GDP is experiencing an "
                "annual contraction."
            ),
        }

    if rate < 4.0:
        return {
            "status": "weak_growth",
            "score": 0,
            "summary": (
                "India's real GDP growth is positive "
                "but relatively weak."
            ),
        }

    if rate < 6.0:
        return {
            "status": "moderate_growth",
            "score": 1,
            "summary": (
                "India's real GDP is growing at a "
                "moderate annual rate."
            ),
        }

    return {
        "status": "strong_growth",
        "score": 2,
        "summary": (
            "India's real GDP is growing at a strong "
            "annual rate."
        ),
    }


def _interpret_singapore_gdp_growth(
    rate: float,
):
    """
    Interpret Singapore quarter-on-quarter GDP growth.
    """

    if rate < -1.0:
        return {
            "status": "significant_contraction",
            "score": -2,
            "summary": (
                "Singapore's real GDP is experiencing "
                "a significant quarterly contraction."
            ),
        }

    if rate < 0:
        return {
            "status": "mild_contraction",
            "score": -1,
            "summary": (
                "Singapore's real GDP is experiencing "
                "a quarterly contraction."
            ),
        }

    if rate < 0.3:
        return {
            "status": "weak_growth",
            "score": 0,
            "summary": (
                "Singapore's quarterly GDP growth is "
                "positive but relatively weak."
            ),
        }

    if rate <= 1.0:
        return {
            "status": "moderate_growth",
            "score": 1,
            "summary": (
                "Singapore's real GDP is growing at a "
                "moderate quarterly rate."
            ),
        }

    return {
        "status": "strong_growth",
        "score": 2,
        "summary": (
            "Singapore's real GDP is growing at a "
            "strong quarterly rate."
        ),
    }


def _interpret_australia_gdp_growth(
    rate: float,
):
    """
    Interpret Australia quarter-on-quarter GDP growth.
    """

    if rate < -1.0:
        return {
            "status": "significant_contraction",
            "score": -2,
            "summary": (
                "Australia's real GDP is experiencing "
                "a significant quarterly contraction."
            ),
        }

    if rate < 0:
        return {
            "status": "mild_contraction",
            "score": -1,
            "summary": (
                "Australia's real GDP is experiencing "
                "a quarterly contraction."
            ),
        }

    if rate < 0.3:
        return {
            "status": "weak_growth",
            "score": 0,
            "summary": (
                "Australia's quarterly GDP growth is "
                "positive but relatively weak."
            ),
        }

    if rate <= 0.8:
        return {
            "status": "moderate_growth",
            "score": 1,
            "summary": (
                "Australia's real GDP is growing at a "
                "moderate quarterly rate."
            ),
        }

    return {
        "status": "strong_growth",
        "score": 2,
        "summary": (
            "Australia's real GDP is growing at a "
            "strong quarterly rate."
        ),
    }


def analyze_macro_gdp(
    stock_symbol: str,
):
    """
    Fetch macroeconomic features and return the
    country-aware GDP growth interpretation.
    """

    features = build_macro_features(
        stock_symbol
    )

    interpretation = interpret_gdp_growth(
        market_code=features["market_code"],
        gdp_growth_rate=features[
            "gdp_growth_rate"
        ],
        is_fallback=features[
            "gdp_is_fallback"
        ],
    )

    return {
        "stock_symbol": features["stock_symbol"],
        "market_code": features["market_code"],
        "country": features["country"],
        "gdp_growth": interpretation,
    }

# --------------------------------------------------
# Unemployment Framework Configuration
# --------------------------------------------------

UNEMPLOYMENT_FRAMEWORKS = {
    "US": {
        "framework_name": (
            "United States labour-market conditions"
        ),
        "population_context": (
            "Civilian labour force"
        ),
    },
    "IN": {
        "framework_name": (
            "India labour-market conditions"
        ),
        "population_context": (
            "Persons aged 15 years and above"
        ),
    },
    "SG": {
        "framework_name": (
            "Singapore labour-market conditions"
        ),
        "population_context": (
            "Total labour force"
        ),
    },
    "AU": {
        "framework_name": (
            "Australia labour-market conditions"
        ),
        "population_context": (
            "Civilian labour force"
        ),
    },
}


# --------------------------------------------------
# Unemployment Interpretation
# --------------------------------------------------

def interpret_unemployment(
    market_code: str,
    unemployment_rate,
):
    """
    Interpret unemployment using country-specific
    analytical thresholds.

    Unemployment score:
         1 = strong or healthy labour market
         0 = moderate labour-market conditions
        -1 = elevated unemployment
        -2 = high unemployment
    """

    normalized_market = (
        market_code.strip().upper()
        if market_code
        else None
    )

    framework = UNEMPLOYMENT_FRAMEWORKS.get(
        normalized_market
    )

    if framework is None:
        return {
            "status": "unsupported_market",
            "score": 0,
            "summary": (
                "Unemployment framework is unavailable "
                f"for market {normalized_market}."
            ),
        }

    try:
        rate = float(unemployment_rate)

    except (TypeError, ValueError):
        return {
            "status": "unavailable",
            "score": 0,
            "unemployment_rate": None,
            "framework_name": framework[
                "framework_name"
            ],
            "summary": (
                "Unemployment data is unavailable."
            ),
        }

    if rate < 0:
        return {
            "status": "invalid_value",
            "score": 0,
            "unemployment_rate": rate,
            "framework_name": framework[
                "framework_name"
            ],
            "summary": (
                "Unemployment cannot be negative."
            ),
        }

    interpreters = {
        "US": _interpret_us_unemployment,
        "IN": _interpret_india_unemployment,
        "SG": _interpret_singapore_unemployment,
        "AU": _interpret_australia_unemployment,
    }

    interpretation = interpreters[
        normalized_market
    ](rate)

    return {
        "unemployment_rate": rate,
        "framework_name": framework[
            "framework_name"
        ],
        "population_context": framework[
            "population_context"
        ],
        **interpretation,
        "threshold_note": (
            "Unemployment classifications use "
            "country-specific analytical thresholds "
            "and are not official government targets."
        ),
    }


def _interpret_us_unemployment(
    rate: float,
):
    """
    Interpret the US unemployment rate.
    """

    if rate <= 4.5:
        return {
            "status": "healthy_labour_market",
            "score": 1,
            "summary": (
                "US unemployment is consistent with "
                "a relatively healthy labour market."
            ),
        }

    if rate <= 5.5:
        return {
            "status": "moderate_unemployment",
            "score": 0,
            "summary": (
                "US unemployment indicates moderate "
                "labour-market conditions."
            ),
        }

    if rate <= 7.0:
        return {
            "status": "elevated_unemployment",
            "score": -1,
            "summary": (
                "US unemployment is elevated, "
                "indicating labour-market weakness."
            ),
        }

    return {
        "status": "high_unemployment",
        "score": -2,
        "summary": (
            "US unemployment is high, indicating "
            "significant labour-market weakness."
        ),
    }


def _interpret_india_unemployment(
    rate: float,
):
    """
    Interpret India's unemployment rate.
    """

    if rate <= 4.0:
        return {
            "status": "healthy_labour_market",
            "score": 1,
            "summary": (
                "India's unemployment rate is "
                "relatively low."
            ),
        }

    if rate <= 6.0:
        return {
            "status": "moderate_unemployment",
            "score": 0,
            "summary": (
                "India's unemployment rate indicates "
                "moderate labour-market conditions."
            ),
        }

    if rate <= 8.0:
        return {
            "status": "elevated_unemployment",
            "score": -1,
            "summary": (
                "India's unemployment rate is "
                "elevated, indicating labour-market "
                "pressure."
            ),
        }

    return {
        "status": "high_unemployment",
        "score": -2,
        "summary": (
            "India's unemployment rate is high, "
            "indicating significant labour-market "
            "weakness."
        ),
    }


def _interpret_singapore_unemployment(
    rate: float,
):
    """
    Interpret Singapore's unemployment rate.
    """

    if rate <= 2.5:
        return {
            "status": "healthy_labour_market",
            "score": 1,
            "summary": (
                "Singapore's unemployment rate is "
                "consistent with a healthy labour "
                "market."
            ),
        }

    if rate <= 3.5:
        return {
            "status": "moderate_unemployment",
            "score": 0,
            "summary": (
                "Singapore's unemployment rate "
                "indicates moderate labour-market "
                "conditions."
            ),
        }

    if rate <= 5.0:
        return {
            "status": "elevated_unemployment",
            "score": -1,
            "summary": (
                "Singapore's unemployment rate is "
                "elevated."
            ),
        }

    return {
        "status": "high_unemployment",
        "score": -2,
        "summary": (
            "Singapore's unemployment rate is high, "
            "indicating significant labour-market "
            "weakness."
        ),
    }


def _interpret_australia_unemployment(
    rate: float,
):
    """
    Interpret Australia's unemployment rate.
    """

    if rate <= 4.5:
        return {
            "status": "healthy_labour_market",
            "score": 1,
            "summary": (
                "Australia's unemployment rate is "
                "consistent with a relatively healthy "
                "labour market."
            ),
        }

    if rate <= 5.5:
        return {
            "status": "moderate_unemployment",
            "score": 0,
            "summary": (
                "Australia's unemployment rate "
                "indicates moderate labour-market "
                "conditions."
            ),
        }

    if rate <= 7.0:
        return {
            "status": "elevated_unemployment",
            "score": -1,
            "summary": (
                "Australia's unemployment rate is "
                "elevated, indicating labour-market "
                "weakness."
            ),
        }

    return {
        "status": "high_unemployment",
        "score": -2,
        "summary": (
            "Australia's unemployment rate is high, "
            "indicating significant labour-market "
            "weakness."
        ),
    }


def analyze_macro_unemployment(
    stock_symbol: str,
):
    """
    Fetch macroeconomic features and return the
    country-aware unemployment interpretation.
    """

    features = build_macro_features(
        stock_symbol
    )

    interpretation = interpret_unemployment(
        market_code=features["market_code"],
        unemployment_rate=features[
            "unemployment_rate"
        ],
    )

    return {
        "stock_symbol": features["stock_symbol"],
        "market_code": features["market_code"],
        "country": features["country"],
        "unemployment": interpretation,
    }

# --------------------------------------------------
# Monetary-Rate Framework Configuration
# --------------------------------------------------

MONETARY_RATE_FRAMEWORKS = {
    "US": {
        "framework_name": (
            "Federal Reserve interest-rate environment"
        ),
        "rate_name": (
            "Federal Funds Effective Rate"
        ),
        "rate_role": "Policy-rate proxy",
    },
    "IN": {
        "framework_name": (
            "Reserve Bank of India monetary-policy "
            "environment"
        ),
        "rate_name": "RBI Repo Rate",
        "rate_role": "Policy rate",
    },
    "SG": {
        "framework_name": (
            "Singapore domestic interest-rate "
            "environment"
        ),
        "rate_name": (
            "Singapore Overnight Rate Average"
        ),
        "rate_role": (
            "Domestic overnight market reference rate"
        ),
    },
    "AU": {
        "framework_name": (
            "Reserve Bank of Australia interest-rate "
            "environment"
        ),
        "rate_name": "Cash Rate Target",
        "rate_role": "Policy rate",
    },
}


# --------------------------------------------------
# Monetary-Rate Interpretation
# --------------------------------------------------

def interpret_monetary_rate(
    market_code: str,
    monetary_rate,
    inflation_rate,
    is_policy_rate,
):
    """
    Interpret the monetary-rate environment.

    Monetary score:
         1 = supportive or low-rate environment
         0 = balanced, neutral, or unavailable
        -1 = restrictive or high-rate environment
        -2 = strongly restrictive environment

    For policy-rate markets, the analysis uses a simple
    real-rate proxy:

        monetary rate - inflation rate

    This is an analytical proxy and is not an official
    central-bank estimate of the monetary-policy stance.
    """

    normalized_market = (
        market_code.strip().upper()
        if market_code
        else None
    )

    framework = MONETARY_RATE_FRAMEWORKS.get(
        normalized_market
    )

    if framework is None:
        return {
            "status": "unsupported_market",
            "score": 0,
            "summary": (
                "Monetary-rate framework is unavailable "
                f"for market {normalized_market}."
            ),
        }

    try:
        rate = float(monetary_rate)

    except (TypeError, ValueError):
        return {
            "status": "unavailable",
            "score": 0,
            "monetary_rate": None,
            "inflation_rate": (
                _safe_float(inflation_rate)
            ),
            "is_policy_rate": (
                None
                if is_policy_rate is None
                else bool(is_policy_rate)
            ),
            "framework_name": framework[
                "framework_name"
            ],
            "rate_name": framework["rate_name"],
            "rate_role": framework["rate_role"],
            "summary": (
                "The monetary rate is currently "
                "unavailable."
            ),
        }

    if rate < 0:
        return {
            "status": "negative_rate_environment",
            "score": 1,
            "monetary_rate": rate,
            "inflation_rate": (
                _safe_float(inflation_rate)
            ),
            "is_policy_rate": bool(
                is_policy_rate
            ),
            "framework_name": framework[
                "framework_name"
            ],
            "rate_name": framework["rate_name"],
            "rate_role": framework["rate_role"],
            "summary": (
                "The monetary rate is negative, "
                "indicating an unusually supportive "
                "interest-rate environment."
            ),
        }

    policy_rate_flag = bool(is_policy_rate)

    if (
        normalized_market == "SG"
        or not policy_rate_flag
    ):
        interpretation = (
            _interpret_market_reference_rate(rate)
        )

        return {
            "monetary_rate": rate,
            "inflation_rate": (
                _safe_float(inflation_rate)
            ),
            "is_policy_rate": False,
            "framework_name": framework[
                "framework_name"
            ],
            "rate_name": framework["rate_name"],
            "rate_role": framework["rate_role"],
            **interpretation,
            "policy_framework_note": (
                "Singapore conducts monetary policy "
                "primarily through the exchange rate. "
                "SORA is a domestic overnight market "
                "reference rate and is not an MAS "
                "policy rate."
            ),
            "threshold_note": (
                "The classification describes the "
                "domestic interest-rate environment "
                "and not the official MAS policy stance."
            ),
        }

    inflation = _safe_float(
        inflation_rate
    )

    if inflation is None:
        return {
            "status": "rate_available_inflation_unavailable",
            "score": 0,
            "monetary_rate": rate,
            "inflation_rate": None,
            "real_rate_proxy": None,
            "is_policy_rate": True,
            "framework_name": framework[
                "framework_name"
            ],
            "rate_name": framework["rate_name"],
            "rate_role": framework["rate_role"],
            "summary": (
                "The monetary rate is available, but "
                "inflation is unavailable, so a simple "
                "real-rate proxy cannot be calculated."
            ),
        }

    real_rate_proxy = round(
        rate - inflation,
        2,
    )

    interpretation = (
        _interpret_real_rate_proxy(
            real_rate_proxy
        )
    )

    return {
        "monetary_rate": rate,
        "inflation_rate": inflation,
        "real_rate_proxy": real_rate_proxy,
        "is_policy_rate": True,
        "framework_name": framework[
            "framework_name"
        ],
        "rate_name": framework["rate_name"],
        "rate_role": framework["rate_role"],
        **interpretation,
        "calculation": (
            "monetary_rate - inflation_rate"
        ),
        "threshold_note": (
            "The real-rate proxy is a simplified "
            "analytical measure. It is not an official "
            "central-bank estimate of the neutral or "
            "real policy rate."
        ),
    }


def _safe_float(
    value,
):
    """
    Convert a value to float without raising an error.
    """

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def _interpret_real_rate_proxy(
    real_rate_proxy: float,
):
    """
    Interpret the simple monetary-rate-minus-inflation
    proxy.
    """

    if real_rate_proxy < -1.0:
        return {
            "status": "supportive_rate_environment",
            "score": 1,
            "summary": (
                "The monetary rate is materially below "
                "inflation, indicating a supportive "
                "real-rate environment."
            ),
        }

    if real_rate_proxy <= 1.0:
        return {
            "status": "balanced_rate_environment",
            "score": 0,
            "summary": (
                "The monetary rate is broadly aligned "
                "with inflation, indicating a balanced "
                "real-rate environment."
            ),
        }

    if real_rate_proxy <= 2.0:
        return {
            "status": "restrictive_rate_environment",
            "score": -1,
            "summary": (
                "The monetary rate is above inflation, "
                "indicating a restrictive real-rate "
                "environment."
            ),
        }

    return {
        "status": "strongly_restrictive_rate_environment",
        "score": -2,
        "summary": (
            "The monetary rate is substantially above "
            "inflation, indicating a strongly "
            "restrictive real-rate environment."
        ),
    }


def _interpret_market_reference_rate(
    rate: float,
):
    """
    Interpret a market reference rate without describing
    it as an official policy stance.
    """

    if rate <= 1.5:
        return {
            "status": "low_rate_environment",
            "score": 1,
            "summary": (
                "The domestic overnight reference rate "
                "indicates a relatively low interest-rate "
                "environment."
            ),
        }

    if rate <= 3.0:
        return {
            "status": "moderate_rate_environment",
            "score": 0,
            "summary": (
                "The domestic overnight reference rate "
                "indicates a moderate interest-rate "
                "environment."
            ),
        }

    if rate <= 5.0:
        return {
            "status": "high_rate_environment",
            "score": -1,
            "summary": (
                "The domestic overnight reference rate "
                "indicates a relatively high interest-rate "
                "environment."
            ),
        }

    return {
        "status": "very_high_rate_environment",
        "score": -2,
        "summary": (
            "The domestic overnight reference rate "
            "indicates a very high interest-rate "
            "environment."
        ),
    }


def analyze_macro_monetary_rate(
    stock_symbol: str,
):
    """
    Fetch macroeconomic features and return the
    country-aware monetary-rate interpretation.
    """

    features = build_macro_features(
        stock_symbol
    )

    interpretation = interpret_monetary_rate(
        market_code=features["market_code"],
        monetary_rate=features[
            "monetary_rate"
        ],
        inflation_rate=features[
            "inflation_rate"
        ],
        is_policy_rate=features[
            "monetary_rate_is_policy_rate"
        ],
    )

    return {
        "stock_symbol": features["stock_symbol"],
        "market_code": features["market_code"],
        "country": features["country"],
        "monetary_environment": interpretation,
    }