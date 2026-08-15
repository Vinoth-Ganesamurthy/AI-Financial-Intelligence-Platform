"""
Tests for RBI policy repo-rate integration.
"""

from unittest.mock import MagicMock, patch

from src.data.macro import macro_sources


RBI_HTML = """
<html>
    <body>
        <div>
            Policy Repo Rate : 5.25%
        </div>
        <footer>
            Website last updated date:
            Aug 14, 2026
        </footer>
    </body>
</html>
"""


def test_parse_rbi_policy_rate_html():
    result = (
        macro_sources
        ._parse_rbi_policy_rate_html(
            RBI_HTML
        )
    )

    assert result["value"] == 5.25

    assert result[
        "page_last_updated_date"
    ] == "2026-08-14"


@patch.object(
    macro_sources,
    "save_macro_cache",
)
@patch.object(
    macro_sources.browser_requests,
    "get",
)
def test_fetch_india_policy_rate_live(
    mock_get,
    mock_save_cache,
):
    response = MagicMock()
    response.text = RBI_HTML

    mock_get.return_value = response

    result = (
        macro_sources
        .fetch_india_policy_rate()
    )

    response.raise_for_status.assert_called_once()

    assert result["value"] == 5.25
    assert result["is_policy_rate"] is True
    assert result["is_cached"] is False
    assert result["is_fallback"] is False

    mock_save_cache.assert_called_once()


@patch.object(
    macro_sources,
    "get_macro_cache",
)
@patch.object(
    macro_sources.browser_requests,
    "get",
    side_effect=RuntimeError(
        "Simulated RBI outage"
    ),
)
def test_fetch_india_policy_rate_cache(
    mock_get,
    mock_get_cache,
):
    mock_get_cache.return_value = {
        "name": "Policy Repo Rate",
        "value": 5.25,
        "unit": "percent",
        "is_cached": True,
        "cached_at_utc": (
            "2026-08-15T17:30:00+00:00"
        ),
    }

    result = (
        macro_sources
        .fetch_india_policy_rate()
    )

    assert result["value"] == 5.25
    assert result["is_cached"] is True
    assert result["is_policy_rate"] is True
    assert result["is_fallback"] is False

    mock_get_cache.assert_called_once_with(
        "IN",
        "policy_rate",
    )