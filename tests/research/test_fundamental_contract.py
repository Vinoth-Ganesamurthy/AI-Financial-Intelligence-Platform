"""
Regression tests for consistent fundamental-data units.

External Yahoo endpoints are mocked so these tests
remain deterministic and do not require network access.
"""

from unittest.mock import patch

from src.analysis.fundamental.fundamental_analysis import (
    _fetch_yahoo_direct_fundamental_data,
)


MODULE_PATH = (
    "src.analysis.fundamental."
    "fundamental_analysis"
)


def _timeseries(
    series_name: str,
    value: float,
) -> dict:
    """Build one mocked Yahoo annual series."""

    return {
        "meta": {
            "symbol": ["TEST"],
            "type": [series_name],
        },
        series_name: [
            {
                "asOfDate": "2025-12-31",
                "periodType": "12M",
                "currencyCode": "USD",
                "reportedValue": {
                    "raw": value,
                },
            }
        ],
    }


def test_direct_yahoo_debt_to_equity_is_percentage():
    search_payload = {
        "quotes": [
            {
                "symbol": "TEST",
                "longname": "Test Company",
                "sector": "Technology",
                "industry": "Software",
                "currency": "USD",
                "marketCap": 1_000,
            }
        ]
    }

    chart_payload = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "currency": "USD",
                        "regularMarketPrice": 10,
                    }
                }
            ]
        }
    }

    fundamentals_payload = {
        "timeseries": {
            "result": [
                _timeseries(
                    "annualTotalRevenue",
                    1_000,
                ),
                _timeseries(
                    "annualNetIncome",
                    100,
                ),
                _timeseries(
                    "annualStockholdersEquity",
                    100,
                ),
                _timeseries(
                    "annualTotalAssets",
                    500,
                ),
                _timeseries(
                    "annualTotalDebt",
                    200,
                ),
                _timeseries(
                    "annualFreeCashFlow",
                    50,
                ),
            ]
        }
    }

    with patch(
        f"{MODULE_PATH}._get_yahoo_browser_json",
        side_effect=[
            search_payload,
            chart_payload,
            fundamentals_payload,
        ],
    ), patch(
        f"{MODULE_PATH}._get_yahoo_exchange_rate",
        return_value=1.0,
    ):
        result = (
            _fetch_yahoo_direct_fundamental_data(
                "TEST"
            )
        )

    assert result["debt_to_equity"] == 200.0
    assert (
        result["data_source"]
        == "Yahoo Finance Direct"
    )