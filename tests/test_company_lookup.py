"""
Tests for company-name lookup and invalid-symbol
protection.
"""

from unittest.mock import Mock, patch

import pytest

from src.analysis.intelligence.intelligence_engine import (
    build_financial_intelligence,
)
from src.data import company_lookup


def test_company_name_generates_acronym():
    queries = company_lookup._build_search_queries(
        "Tata Consultancy Services Limited"
    )

    assert "TCS" in queries


def test_company_lookup_retries_with_acronym():
    rejected_response = Mock()
    rejected_response.status_code = 422

    successful_response = Mock()
    successful_response.status_code = 200
    successful_response.json.return_value = {
        "result": [
            {
                "symbol": "TCS.NS",
                "displaySymbol": "TCS.NS",
            }
        ]
    }

    with (
        patch.object(
            company_lookup,
            "FINNHUB_API_KEY",
            "test-key",
        ),
        patch.object(
            company_lookup.requests,
            "get",
            side_effect=[
                rejected_response,
                successful_response,
            ],
        ) as mock_get,
    ):
        result = company_lookup.get_stock_symbol(
            "Tata Consultancy Services"
        )

    assert result == "TCS.NS"
    assert mock_get.call_count == 2

    second_query = (
        mock_get.call_args_list[1]
        .kwargs["params"]["q"]
    )

    assert second_query == "TCS"


def test_invalid_company_is_rejected():
    with (
        patch(
            "src.analysis.intelligence."
            "intelligence_engine.fetch_market_data",
            side_effect=ValueError(
                "No market data found."
            ),
        ),
        patch(
            "src.analysis.intelligence."
            "intelligence_engine."
            "fetch_fundamental_data",
            side_effect=ValueError(
                "No fundamental data found."
            ),
        ),
        patch(
            "src.analysis.intelligence."
            "intelligence_engine.get_stock_symbol",
            return_value=None,
        ),
    ):
        with pytest.raises(
            ValueError,
            match="No listed company found",
        ):
            build_financial_intelligence(
                "INVALID COMPANY"
            )