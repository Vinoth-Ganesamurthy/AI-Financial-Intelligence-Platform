"""
Financial Intelligence Engine.

Combines historical, technical, fundamental,
sentiment, and sector-adjusted macro analysis.
"""

from datetime import datetime, timezone

from src.data.market_data import fetch_market_data
from src.analysis.historical.historical_analysis import (
    historical_analysis,
)
from src.analysis.technical.technical_analysis import (
    technical_analysis,
)
from src.analysis.fundamental.fundamental_analysis import (
    fetch_fundamental_data,
)
from src.analysis.sentiment.sentiment_analysis import (
    analyze_company_sentiment,
)
from src.analysis.macro.macro_analysis import (
    build_combined_macro_analysis,
)
from src.analysis.macro.sector_impact import (
    build_sector_macro_impact,
)
from src.data.company_lookup import get_stock_symbol

INTELLIGENCE_WEIGHTS = {
    "fundamental": 0.30,
    "technical": 0.20,
    "sentiment": 0.15,
    "historical": 0.15,
    "sector_macro": 0.20,
}


def _clamp(value, minimum=-1.0, maximum=1.0):
    return max(minimum, min(maximum, value))


def _safe_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def score_technical_analysis(analysis):
    if not analysis:
        return {
            "score": 0.0,
            "is_available": False,
            "quality_factor": 0.0,
        }

    net_score = _safe_number(
        analysis.get("net_score")
    )

    if net_score is None:
        return {
            "score": 0.0,
            "is_available": False,
            "quality_factor": 0.0,
        }

    score = _clamp(net_score / 6)

    return {
        "score": round(score, 3),
        "is_available": True,
        "quality_factor": 1.0,
        "signal": analysis.get("signal"),
        "net_score": net_score,
    }


def score_sentiment_analysis(analysis):
    if not analysis:
        return {
            "score": 0.0,
            "is_available": False,
            "quality_factor": 0.0,
        }

    features = analysis.get("features", {})
    article_count = features.get("article_count", 0)
    sentiment_score = _safe_number(
        features.get("sentiment_score")
    )

    if not article_count or sentiment_score is None:
        return {
            "score": 0.0,
            "is_available": False,
            "quality_factor": 0.0,
            "article_count": article_count,
        }

    quality_factor = min(
        article_count / 5,
        1.0,
    )

    return {
        "score": round(
            _clamp(sentiment_score),
            3,
        ),
        "is_available": True,
        "quality_factor": round(
            quality_factor,
            2,
        ),
        "article_count": article_count,
        "overall_sentiment": features.get(
            "overall_sentiment"
        ),
    }


def score_historical_analysis(analysis):
    if not analysis:
        return {
            "score": 0.0,
            "is_available": False,
            "quality_factor": 0.0,
        }

    return_periods = {
        "one_month_return": {
            "weight": 0.20,
            "scale": 20,
        },
        "three_month_return": {
            "weight": 0.30,
            "scale": 30,
        },
        "six_month_return": {
            "weight": 0.25,
            "scale": 40,
        },
        "one_year_return": {
            "weight": 0.25,
            "scale": 50,
        },
    }

    weighted_score = 0.0
    available_weight = 0.0

    for field, configuration in (
        return_periods.items()
    ):
        value = _safe_number(
            analysis.get(field)
        )

        if value is None:
            continue

        normalized_return = _clamp(
            value / configuration["scale"]
        )

        weighted_score += (
            normalized_return
            * configuration["weight"]
        )

        available_weight += configuration[
            "weight"
        ]

    if available_weight == 0:
        return {
            "score": 0.0,
            "is_available": False,
            "quality_factor": 0.0,
        }

    score = weighted_score / available_weight

    volatility = _safe_number(
        analysis.get("annualized_volatility")
    )

    drawdown = _safe_number(
        analysis.get("maximum_drawdown")
    )

    risk_penalty = 0.0

    if volatility is not None:
        if volatility > 75:
            risk_penalty -= 0.20
        elif volatility > 50:
            risk_penalty -= 0.10

    if drawdown is not None:
        if drawdown < -50:
            risk_penalty -= 0.20
        elif drawdown < -30:
            risk_penalty -= 0.10

    score = _clamp(
        score + risk_penalty
    )

    return {
        "score": round(score, 3),
        "is_available": True,
        "quality_factor": round(
            available_weight,
            2,
        ),
        "risk_penalty": risk_penalty,
    }


def score_fundamental_analysis(analysis):
    if not analysis:
        return {
            "score": 0.0,
            "is_available": False,
            "quality_factor": 0.0,
        }

    metric_scores = {}

    profit_margin = _safe_number(
        analysis.get("profit_margin")
    )
    if profit_margin is not None:
        if profit_margin >= 10:
            metric_scores["profit_margin"] = 1.0
        elif profit_margin > 0:
            metric_scores["profit_margin"] = 0.5
        else:
            metric_scores["profit_margin"] = -1.0

    return_on_equity = _safe_number(
        analysis.get("return_on_equity")
    )
    if return_on_equity is not None:
        if return_on_equity >= 15:
            metric_scores["return_on_equity"] = 1.0
        elif return_on_equity >= 5:
            metric_scores["return_on_equity"] = 0.5
        elif return_on_equity >= 0:
            metric_scores["return_on_equity"] = 0.0
        else:
            metric_scores["return_on_equity"] = -1.0

    for field in [
        "revenue_growth",
        "earnings_growth",
    ]:
        value = _safe_number(
            analysis.get(field)
        )

        if value is None:
            continue

        if value >= 10:
            metric_scores[field] = 1.0
        elif value > 0:
            metric_scores[field] = 0.5
        elif value <= -10:
            metric_scores[field] = -1.0
        else:
            metric_scores[field] = -0.5

    forward_pe = _safe_number(
        analysis.get("forward_pe")
    )
    if forward_pe is not None:
        if 0 < forward_pe <= 25:
            metric_scores["forward_pe"] = 1.0
        elif forward_pe <= 40:
            metric_scores["forward_pe"] = 0.25
        elif forward_pe > 40:
            metric_scores["forward_pe"] = -0.5
        else:
            metric_scores["forward_pe"] = -1.0

    debt_to_equity = _safe_number(
        analysis.get("debt_to_equity")
    )
    if debt_to_equity is not None:
        if debt_to_equity <= 100:
            metric_scores["debt_to_equity"] = 0.5
        elif debt_to_equity <= 200:
            metric_scores["debt_to_equity"] = 0.0
        else:
            metric_scores["debt_to_equity"] = -0.5

    free_cash_flow = _safe_number(
        analysis.get("free_cash_flow")
    )
    if free_cash_flow is not None:
        metric_scores["free_cash_flow"] = (
            1.0 if free_cash_flow > 0 else -1.0
        )

    if not metric_scores:
        return {
            "score": 0.0,
            "is_available": False,
            "quality_factor": 0.0,
        }

    score = sum(
        metric_scores.values()
    ) / len(metric_scores)

    quality_factor = min(
        len(metric_scores) / 7,
        1.0,
    )

    return {
        "score": round(
            _clamp(score),
            3,
        ),
        "is_available": True,
        "quality_factor": round(
            quality_factor,
            2,
        ),
        "metric_scores": metric_scores,
    }


def score_sector_macro_analysis(analysis):
    if not analysis:
        return {
            "score": 0.0,
            "is_available": False,
            "quality_factor": 0.0,
        }

    score = _safe_number(
        analysis.get("sector_macro_score")
    )

    available_weight = _safe_number(
        analysis.get("available_sector_weight")
    )

    if score is None or not available_weight:
        return {
            "score": 0.0,
            "is_available": False,
            "quality_factor": 0.0,
        }

    confidence = _safe_number(
        analysis.get("macro_confidence_score")
    )

    return {
        "score": round(
            _clamp(score),
            3,
        ),
        "is_available": True,
        "quality_factor": (
            round(confidence, 2)
            if confidence is not None
            else 0.0
        ),
        "classification": analysis.get(
            "classification"
        ),
    }


def _classify_intelligence_score(score):
    if score >= 0.50:
        return (
            "strongly_favourable",
            "The available financial indicators are "
            "strongly favourable overall.",
        )

    if score >= 0.20:
        return (
            "favourable",
            "The available financial indicators are "
            "favourable overall.",
        )

    if score > -0.20:
        return (
            "neutral",
            "The available financial indicators are "
            "mixed or broadly balanced.",
        )

    if score > -0.50:
        return (
            "cautious",
            "The available financial indicators show "
            "meaningful risks or headwinds.",
        )

    return (
        "unfavourable",
        "The available financial indicators are "
        "unfavourable overall.",
    )


def build_financial_intelligence(
    stock_symbol: str,
    news_limit: int = 5,
    _allow_company_lookup: bool = True,
):
    if not stock_symbol:
        raise ValueError("Stock symbol is required.")

    symbol = stock_symbol.strip().upper()
    errors = {}

    market_data = None
    historical = None
    technical = None
    fundamental = None
    sentiment = None
    macro = None
    sector_macro = None

    try:
        market_data = fetch_market_data(
            symbol,
            period="2y",
            interval="1d",
        )
    except Exception as error:
        errors["market_data"] = str(error)

    if market_data is not None:
        try:
            historical = historical_analysis(
                market_data
            )
        except Exception as error:
            errors["historical"] = str(error)

        try:
            technical = technical_analysis(
                market_data
            )
        except Exception as error:
            errors["technical"] = str(error)

    try:
        fundamental = fetch_fundamental_data(
            symbol
        )
    except Exception as error:
        errors["fundamental"] = str(error)
    has_market_data = market_data is not None

    has_company_identity = bool(
        fundamental
        and fundamental.get("company_name")
    )

    if (
        not has_market_data
        and not has_company_identity
    ):
        if _allow_company_lookup:
            resolved_symbol = get_stock_symbol(
                stock_symbol
            )

            if resolved_symbol:
                resolved_symbol = (
                    resolved_symbol
                    .strip()
                    .upper()
                )

                if resolved_symbol != symbol:
                    return build_financial_intelligence(
                        stock_symbol=resolved_symbol,
                        news_limit=news_limit,
                        _allow_company_lookup=False,
                    )

        raise ValueError(
            f"No listed company found for "
            f"{stock_symbol}. Enter a valid "
            f"company name or stock symbol."
        )
    try:
        company_name = (
            fundamental.get("company_name")
            if fundamental
            else None
        )

        sentiment = analyze_company_sentiment(
            symbol=symbol,
            company_name=company_name,
            limit=news_limit,
        )
    except Exception as error:
        errors["sentiment"] = str(error)

    try:
        macro = build_combined_macro_analysis(
            symbol
        )
    except Exception as error:
        errors["macro"] = str(error)

    if macro is not None:
        try:
            fundamental_for_sector = (
                fundamental
                if fundamental is not None
                else {
                    "symbol": symbol,
                    "company_name": None,
                    "sector": None,
                    "industry": None,
                }
            )

            sector_macro = build_sector_macro_impact(
                stock_symbol=symbol,
                fundamental_data=(
                    fundamental_for_sector
                ),
                macro_analysis=macro,
            )
        except Exception as error:
            errors["sector_macro"] = str(error)

    module_scores = {
        "fundamental": score_fundamental_analysis(
            fundamental
        ),
        "technical": score_technical_analysis(
            technical
        ),
        "sentiment": score_sentiment_analysis(
            sentiment
        ),
        "historical": score_historical_analysis(
            historical
        ),
        "sector_macro": score_sector_macro_analysis(
            sector_macro
        ),
    }

    weighted_total = 0.0
    available_weight = 0.0
    confidence_total = 0.0

    for module_name, module_score in (
        module_scores.items()
    ):
        weight = INTELLIGENCE_WEIGHTS[
            module_name
        ]

        if not module_score["is_available"]:
            module_score["weight"] = weight
            module_score[
                "weighted_contribution"
            ] = None
            continue

        contribution = (
            module_score["score"] * weight
        )

        weighted_total += contribution
        available_weight += weight

        confidence_total += (
            weight
            * module_score["quality_factor"]
        )

        module_score["weight"] = weight
        module_score[
            "weighted_contribution"
        ] = round(contribution, 3)

    if available_weight:
        intelligence_score = (
            weighted_total / available_weight
        )
    else:
        intelligence_score = 0.0

    intelligence_score = round(
        intelligence_score,
        3,
    )

    classification, summary = (
        _classify_intelligence_score(
            intelligence_score
        )
    )

    return {
        "stock_symbol": symbol,
        "company_name": (
            fundamental.get("company_name")
            if fundamental
            else None
        ),
        "sector": (
            fundamental.get("sector")
            if fundamental
            else None
        ),
        "intelligence_score": intelligence_score,
        "classification": classification,
        "summary": summary,
        "coverage_ratio": round(
            available_weight,
            2,
        ),
        "confidence_score": round(
            confidence_total,
            2,
        ),
        "module_scores": module_scores,
        "analysis": {
            "historical": historical,
            "technical": technical,
            "fundamental": fundamental,
            "sentiment": sentiment,
            "macro": macro,
            "sector_macro": sector_macro,
        },
        "errors": errors,
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "disclaimer": (
            "This analysis is for research and "
            "educational purposes. It is not personal "
            "financial advice or a guaranteed investment "
            "recommendation."
        ),
    }