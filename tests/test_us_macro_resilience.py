"""
Tests for US FRED snapshot resilience.

All external calls and cache writes are mocked.
"""

from unittest.mock import patch

from src.data.macro import macro_sources


def _indicator(value):
    return {
        "value": value,
        "source": "FRED",
    }


@patch.object(
    macro_sources,
    "save_macro_cache",
)
@patch.object(
    macro_sources,
    "fetch_us_unemployment",
    return_value=_indicator(4.1),
)
@patch.object(
    macro_sources,
    "fetch_us_gdp_growth",
    return_value=_indicator(1.5),
)
@patch.object(
    macro_sources,
    "fetch_us_inflation",
    return_value=_indicator(3.3),
)
@patch.object(
    macro_sources,
    "fetch_us_policy_rate",
    return_value=_indicator(3.63),
)
def test_live_us_snapshot_is_cached(
    mock_policy,
    mock_inflation,
    mock_gdp,
    mock_unemployment,
    mock_save_cache,
):
    result = (
        macro_sources.fetch_us_macro_snapshot()
    )

    assert result["country"] == "United States"
    assert result["market_code"] == "US"

    assert result["policy_rate"][
        "is_cached"
    ] is False

    assert result["inflation"][
        "is_fallback"
    ] is False

    mock_save_cache.assert_called_once()

    call_arguments = (
        mock_save_cache.call_args.args
    )

    assert call_arguments[0] == "US"
    assert call_arguments[1] == "macro_snapshot"


@patch.object(
    macro_sources,
    "get_macro_cache",
)
@patch.object(
    macro_sources,
    "fetch_us_policy_rate",
    side_effect=RuntimeError(
        "Simulated FRED outage"
    ),
)
def test_us_snapshot_uses_cache_on_failure(
    mock_policy,
    mock_get_cache,
):
    mock_get_cache.return_value = {
        "country": "United States",
        "market_code": "US",
        "policy_rate": _indicator(3.63),
        "inflation": _indicator(3.3),
        "gdp_growth": _indicator(1.5),
        "unemployment": _indicator(4.1),
        "retrieved_at_utc": (
            "2026-08-15T09:00:00+00:00"
        ),
        "is_cached": True,
        "cached_at_utc": (
            "2026-08-15T09:00:01+00:00"
        ),
    }

    result = (
        macro_sources.fetch_us_macro_snapshot()
    )

    assert result["is_cached"] is True
    assert "served_at_utc" in result

    for indicator_name in [
        "policy_rate",
        "inflation",
        "gdp_growth",
        "unemployment",
    ]:
        indicator = result[indicator_name]

        assert indicator["is_cached"] is True
        assert indicator["cached_at_utc"] == (
            "2026-08-15T09:00:01+00:00"
        )

    mock_get_cache.assert_called_once_with(
        "US",
        "macro_snapshot",
    )