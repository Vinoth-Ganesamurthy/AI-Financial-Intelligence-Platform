"""
Tests for the financial intelligence engine.

External services are mocked so these tests do not
depend on Yahoo Finance, news, FRED, or government APIs.
"""

from unittest.mock import patch

import pytest

from src.analysis.intelligence.intelligence_engine import (
    build_financial_intelligence,
    score_fundamental_analysis,
    score_historical_analysis,
    score_sentiment_analysis,
    score_technical_analysis,
)


def test_technical_score():
    result = score_technical_analysis(
        {
            "net_score": 3,
            "signal": "BULLISH",
        }
    )

    assert result["is_available"] is True
    assert result["score"] == 0.5
    assert result["signal"] == "BULLISH"


def test_sentiment_score():
    result = score_sentiment_analysis(
        {
            "features": {
                "article_count": 5,
                "sentiment_score": 0.6,
                "overall_sentiment": "POSITIVE",
            }
        }
    )

    assert result["is_available"] is True
    assert result["score"] == 0.6
    assert result["quality_factor"] == 1.0


def test_sentiment_without_articles_is_unavailable():
    result = score_sentiment_analysis(
        {
            "features": {
                "article_count": 0,
                "sentiment_score": 0.0,
                "overall_sentiment": "NEUTRAL",
            }
        }
    )

    assert result["is_available"] is False
    assert result["quality_factor"] == 0.0


def test_historical_score():
    result = score_historical_analysis(
        {
            "one_month_return": 10,
            "three_month_return": 15,
            "six_month_return": 20,
            "one_year_return": 25,
            "annualized_volatility": 20,
            "maximum_drawdown": -10,
        }
    )

    assert result["is_available"] is True
    assert result["score"] == 0.5
    assert result["risk_penalty"] == 0.0


def test_fundamental_score():
    result = score_fundamental_analysis(
        {
            "profit_margin": 20,
            "return_on_equity": 20,
            "revenue_growth": 15,
            "earnings_growth": 15,
            "forward_pe": 20,
            "debt_to_equity": 50,
            "free_cash_flow": 100,
        }
    )

    assert result["is_available"] is True
    assert result["score"] == 0.929
    assert result["quality_factor"] == 1.0


@patch(
    "src.analysis.intelligence.intelligence_engine."
    "build_sector_macro_impact"
)
@patch(
    "src.analysis.intelligence.intelligence_engine."
    "build_combined_macro_analysis"
)
@patch(
    "src.analysis.intelligence.intelligence_engine."
    "analyze_company_sentiment"
)
@patch(
    "src.analysis.intelligence.intelligence_engine."
    "fetch_fundamental_data"
)
@patch(
    "src.analysis.intelligence.intelligence_engine."
    "technical_analysis"
)
@patch(
    "src.analysis.intelligence.intelligence_engine."
    "historical_analysis"
)
@patch(
    "src.analysis.intelligence.intelligence_engine."
    "fetch_market_data"
)
def test_complete_financial_intelligence(
    mock_market_data,
    mock_historical,
    mock_technical,
    mock_fundamental,
    mock_sentiment,
    mock_macro,
    mock_sector_macro,
):
    mock_market_data.return_value = object()

    mock_historical.return_value = {
        "one_month_return": 10,
        "three_month_return": 15,
        "six_month_return": 20,
        "one_year_return": 25,
        "annualized_volatility": 20,
        "maximum_drawdown": -10,
    }

    mock_technical.return_value = {
        "net_score": 3,
        "signal": "BULLISH",
    }

    mock_fundamental.return_value = {
        "symbol": "TEST",
        "company_name": "Test Company",
        "sector": "Technology",
        "industry": "Software",
        "profit_margin": 20,
        "return_on_equity": 20,
        "revenue_growth": 15,
        "earnings_growth": 15,
        "forward_pe": 20,
        "debt_to_equity": 50,
        "free_cash_flow": 100,
    }

    mock_sentiment.return_value = {
        "features": {
            "article_count": 5,
            "sentiment_score": 0.6,
            "overall_sentiment": "POSITIVE",
        },
        "articles": [],
    }

    mock_macro.return_value = {
        "combined_macro_score": 0.5,
        "component_scores": {},
        "confidence_score": 1.0,
        "country": "United States",
        "market_code": "US",
    }

    mock_sector_macro.return_value = {
        "sector_macro_score": 0.5,
        "available_sector_weight": 1.0,
        "macro_confidence_score": 1.0,
        "classification": "favourable",
    }

    result = build_financial_intelligence(
        "test",
        news_limit=5,
    )

    assert result["stock_symbol"] == "TEST"
    assert result["company_name"] == "Test Company"
    assert result["coverage_ratio"] == 1.0
    assert result["confidence_score"] == 1.0
    assert result["errors"] == {}
    assert result["intelligence_score"] == pytest.approx(
        0.644,
        abs=0.001,
    )
    assert result["classification"] == (
        "strongly_favourable"
    )

    mock_market_data.assert_called_once_with(
        "TEST",
        period="2y",
        interval="1d",
    )

    mock_sector_macro.assert_called_once()