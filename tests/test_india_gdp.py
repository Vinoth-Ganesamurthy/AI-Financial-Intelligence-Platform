"""
Tests for official India MoSPI NAS GDP integration.
"""

from unittest.mock import patch

from src.analysis.macro.macro_analysis import (
    interpret_gdp_growth,
)
from src.data.macro import macro_sources


NAS_GDP_DATA = [
    {
        "indicator": "GDP Growth Rate",
        "year": "2024-25",
        "quarter": "Q4",
        "constant_price": "7.0",
        "base_year": "2022-23",
        "series": "Current",
    },
    {
        "indicator": "GDP Growth Rate",
        "year": "2025-26",
        "quarter": "Q3",
        "constant_price": "8.0",
        "base_year": "2022-23",
        "series": "Current",
    },
    {
        "indicator": "GDP Growth Rate",
        "year": "2025-26",
        "quarter": "Q4",
        "constant_price": "7.8",
        "base_year": "2022-23",
        "series": "Current",
    },
]


@patch.object(
    macro_sources,
    "save_macro_cache",
)
@patch.object(
    macro_sources,
    "get_mospi_data",
    return_value=NAS_GDP_DATA,
)
def test_fetch_india_gdp_live(
    mock_get_data,
    mock_save_cache,
):
    result = (
        macro_sources
        .fetch_india_gdp_growth()
    )

    assert result["value"] == 7.8
    assert result["fiscal_year"] == "2025-26"
    assert result["quarter"] == 4
    assert result["frequency"] == "quarterly"
    assert result["growth_type"] == "Year-on-Year"
    assert result["source"] == "MoSPI NAS"
    assert result["is_fallback"] is False
    assert result["is_cached"] is False

    mock_save_cache.assert_called_once()


@patch.object(
    macro_sources,
    "get_macro_cache",
)
@patch.object(
    macro_sources,
    "get_mospi_data",
    side_effect=RuntimeError(
        "Simulated NAS outage"
    ),
)
def test_fetch_india_gdp_cache(
    mock_get_data,
    mock_get_cache,
):
    mock_get_cache.return_value = {
        "name": "Real GDP Growth",
        "value": 7.8,
        "frequency": "quarterly",
        "is_cached": True,
        "cached_at_utc": (
            "2026-08-15T17:44:00+00:00"
        ),
    }

    result = (
        macro_sources
        .fetch_india_gdp_growth()
    )

    assert result["value"] == 7.8
    assert result["is_cached"] is True
    assert result["is_fallback"] is False

    mock_get_cache.assert_called_once_with(
        "IN",
        "gdp_growth",
    )


@patch.object(
    macro_sources,
    "fetch_india_gdp_fallback",
)
@patch.object(
    macro_sources,
    "get_macro_cache",
    return_value=None,
)
@patch.object(
    macro_sources,
    "get_mospi_data",
    side_effect=RuntimeError(
        "Simulated NAS outage"
    ),
)
def test_fetch_india_gdp_world_bank_fallback(
    mock_get_data,
    mock_get_cache,
    mock_fallback,
):
    mock_fallback.return_value = {
        "name": "GDP Growth",
        "value": 7.5,
        "is_fallback": True,
        "source": "World Bank",
    }

    result = (
        macro_sources
        .fetch_india_gdp_growth()
    )

    assert result["value"] == 7.5
    assert result["is_fallback"] is True
    assert result["source"] == "World Bank"

    mock_fallback.assert_called_once()


def test_india_gdp_interpretation():
    result = interpret_gdp_growth(
        market_code="IN",
        gdp_growth_rate=7.8,
        is_fallback=False,
    )

    assert result["status"] == "strong_growth"
    assert result["score"] == 2
    assert result["frequency"] == "quarterly"
    assert result["data_quality"] == (
        "official_source"
    )