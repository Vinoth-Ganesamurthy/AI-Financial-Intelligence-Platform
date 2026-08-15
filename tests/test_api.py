"""
Tests for the FastAPI routes.

The intelligence engine is mocked so API tests do not
call external financial-data services.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"
    assert response.json()["documentation"] == "/docs"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
    }


@patch(
    "src.api.main.build_financial_intelligence"
)
def test_intelligence_endpoint(
    mock_build_intelligence,
):
    mock_build_intelligence.return_value = {
        "stock_symbol": "AAPL",
        "company_name": "Apple Inc.",
        "intelligence_score": 0.3,
        "classification": "favourable",
        "coverage_ratio": 1.0,
        "confidence_score": 0.9,
        "errors": {},
    }

    response = client.get(
        "/api/v1/intelligence/aapl",
        params={"news_limit": 3},
    )

    assert response.status_code == 200

    result = response.json()

    assert result["stock_symbol"] == "AAPL"
    assert result["classification"] == "favourable"

    mock_build_intelligence.assert_called_once_with(
        stock_symbol="AAPL",
        news_limit=3,
    )


def test_invalid_news_limit():
    response = client.get(
        "/api/v1/intelligence/AAPL",
        params={"news_limit": 0},
    )

    assert response.status_code == 422


@patch(
    "src.api.main.build_financial_intelligence"
)
def test_engine_value_error_returns_400(
    mock_build_intelligence,
):
    mock_build_intelligence.side_effect = ValueError(
        "No market data found."
    )

    response = client.get(
        "/api/v1/intelligence/INVALID",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "No market data found."
    )