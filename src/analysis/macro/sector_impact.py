"""
Sector-Specific Macroeconomic Impact Module.

Adjusts the importance of macroeconomic indicators
according to the stock's business sector.
"""

from src.analysis.fundamental.fundamental_analysis import (
    fetch_fundamental_data,
)
from src.analysis.macro.macro_analysis import (
    build_combined_macro_analysis,
)


SECTOR_MACRO_WEIGHTS = {
    "Technology": {
        "inflation": 0.15,
        "gdp_growth": 0.30,
        "unemployment": 0.15,
        "monetary_environment": 0.40,
    },
    "Financial Services": {
        "inflation": 0.15,
        "gdp_growth": 0.30,
        "unemployment": 0.20,
        "monetary_environment": 0.35,
    },
    "Energy": {
        "inflation": 0.10,
        "gdp_growth": 0.45,
        "unemployment": 0.15,
        "monetary_environment": 0.30,
    },
    "Basic Materials": {
        "inflation": 0.15,
        "gdp_growth": 0.45,
        "unemployment": 0.15,
        "monetary_environment": 0.25,
    },
    "Consumer Cyclical": {
        "inflation": 0.20,
        "gdp_growth": 0.35,
        "unemployment": 0.30,
        "monetary_environment": 0.15,
    },
    "Consumer Defensive": {
        "inflation": 0.35,
        "gdp_growth": 0.20,
        "unemployment": 0.25,
        "monetary_environment": 0.20,
    },
    "Real Estate": {
        "inflation": 0.15,
        "gdp_growth": 0.20,
        "unemployment": 0.15,
        "monetary_environment": 0.50,
    },
    "Utilities": {
        "inflation": 0.20,
        "gdp_growth": 0.15,
        "unemployment": 0.15,
        "monetary_environment": 0.50,
    },
    "Healthcare": {
        "inflation": 0.25,
        "gdp_growth": 0.20,
        "unemployment": 0.30,
        "monetary_environment": 0.25,
    },
    "Industrials": {
        "inflation": 0.15,
        "gdp_growth": 0.40,
        "unemployment": 0.25,
        "monetary_environment": 0.20,
    },
    "Communication Services": {
        "inflation": 0.20,
        "gdp_growth": 0.30,
        "unemployment": 0.20,
        "monetary_environment": 0.30,
    },
}


DEFAULT_SECTOR_WEIGHTS = {
    "inflation": 0.25,
    "gdp_growth": 0.25,
    "unemployment": 0.25,
    "monetary_environment": 0.25,
}


def _classify_sector_macro_score(score):
    if score >= 0.50:
        return (
            "favourable",
            "Macroeconomic conditions are broadly "
            "supportive for this sector.",
        )

    if score >= 0.15:
        return (
            "mildly_favourable",
            "Macroeconomic conditions are mildly "
            "supportive for this sector.",
        )

    if score > -0.15:
        return (
            "neutral",
            "Macroeconomic conditions are broadly "
            "balanced for this sector.",
        )

    if score > -0.50:
        return (
            "mildly_unfavourable",
            "Macroeconomic conditions create moderate "
            "headwinds for this sector.",
        )

    return (
        "unfavourable",
        "Macroeconomic conditions create significant "
        "headwinds for this sector.",
    )


def build_sector_macro_impact(
    stock_symbol: str,
    fundamental_data=None,
    macro_analysis=None,
):
    if not stock_symbol:
        raise ValueError("Stock symbol is required.")

    normalized_symbol = stock_symbol.strip().upper()

    if fundamental_data is None:
        fundamental_data = fetch_fundamental_data(
            normalized_symbol
        )

        if macro_analysis is None:
         macro_analysis = build_combined_macro_analysis(
            normalized_symbol
        )

    sector = fundamental_data.get("sector")

    sector_weights = SECTOR_MACRO_WEIGHTS.get(
        sector,
        DEFAULT_SECTOR_WEIGHTS,
    )

    used_default_weights = (
        sector not in SECTOR_MACRO_WEIGHTS
    )

    component_scores = macro_analysis[
        "component_scores"
    ]

    weighted_total = 0.0
    available_weight = 0.0
    sector_components = {}

    for component_name, weight in (
        sector_weights.items()
    ):
        component = component_scores.get(
            component_name,
            {},
        )

        is_available = component.get(
            "is_available",
            False,
        )

        normalized_score = component.get(
            "normalized_score",
            0.0,
        )

        contribution = None

        if is_available:
            contribution = (
                normalized_score * weight
            )

            weighted_total += contribution
            available_weight += weight

        sector_components[component_name] = {
            "status": component.get("status"),
            "normalized_score": normalized_score,
            "sector_weight": weight,
            "is_available": is_available,
            "weighted_contribution": (
                round(contribution, 3)
                if contribution is not None
                else None
            ),
        }

    if available_weight:
        sector_score = (
            weighted_total / available_weight
        )
    else:
        sector_score = 0.0

    sector_score = round(
        sector_score,
        3,
    )

    classification, outlook = (
        _classify_sector_macro_score(
            sector_score
        )
    )

    return {
        "stock_symbol": normalized_symbol,
        "company_name": fundamental_data.get(
            "company_name"
        ),
        "sector": sector,
        "industry": fundamental_data.get(
            "industry"
        ),
        "country": macro_analysis["country"],
        "market_code": macro_analysis[
            "market_code"
        ],
        "general_macro_score": macro_analysis[
            "combined_macro_score"
        ],
        "sector_macro_score": sector_score,
        "classification": classification,
        "outlook": outlook,
        "available_sector_weight": round(
            available_weight,
            2,
        ),
        "used_default_weights": (
            used_default_weights
        ),
        "sector_weights": sector_weights,
        "component_impacts": sector_components,
        "macro_confidence_score": macro_analysis[
            "confidence_score"
        ],
        "methodology_note": (
            "The sector score changes the importance "
            "of each macroeconomic component according "
            "to broad sector sensitivity. It does not "
            "measure company-specific competitive, "
            "financial, or management factors."
        ),
    }