"""Tests for historical FRED macro features; no network requests."""

import pytest

from src.research.fred_macro import (
    SERIES,
    build_us_macro_features,
    clean_vintage_observations,
    vintage_before,
)


VINTAGE = "2020-12-31"
OBSERVATION = "2021-01-01"


def payload(values, vintage=VINTAGE):
    return {
        "realtime_start": vintage,
        "realtime_end": vintage,
        "count": len(values),
        "observations": [
            {
                "realtime_start": vintage,
                "realtime_end": vintage,
                "date": period,
                "value": str(value),
            }
            for period, value in values
        ],
    }


def responses():
    return {
        SERIES["cpi"]: payload([
            ("2020-11-01", 110),
            ("2019-11-01", 100),
        ]),
        SERIES["unemployment"]: payload([
            ("2020-11-01", 6.7),
        ]),
        SERIES["monetary_rate"]: payload([
            ("2020-11-01", 0.09),
        ]),
        SERIES["gdp_growth"]: payload([
            ("2020-07-01", 33.4),
        ]),
    }


def test_vintage_excludes_observation_day():
    assert vintage_before("2021-01-01") == "2020-12-31"
    assert vintage_before("2024-03-01") == "2024-02-29"


def test_builds_features_from_same_historical_vintage():
    result = build_us_macro_features(responses(), OBSERVATION)

    assert result["inflation_rate"] == pytest.approx(10)
    assert result["unemployment_rate"] == pytest.approx(6.7)
    assert result["monetary_rate"] == pytest.approx(0.09)
    assert result["gdp_growth_rate"] == pytest.approx(33.4)
    assert result["macro_vintage_date"] == VINTAGE
    assert (
        result["provenance"]["cpi_comparison"]["period_date"]
        == "2019-11-01"
    )


def test_rejects_wrong_response_vintage():
    data = responses()
    data[SERIES["unemployment"]] = payload(
        [("2020-11-01", 6.7)],
        vintage="2021-01-01",
    )

    with pytest.raises(ValueError, match="wrong vintage"):
        build_us_macro_features(data, OBSERVATION)


def test_rejects_wrong_record_vintage():
    data = payload([("2020-11-01", 6.7)])
    data["observations"][0]["realtime_start"] = "2021-01-01"

    with pytest.raises(ValueError, match="wrong vintage"):
        clean_vintage_observations(data, VINTAGE)


def test_rejects_future_period():
    data = payload([("2021-01-01", 6.7)])

    with pytest.raises(ValueError, match="after the vintage"):
        clean_vintage_observations(data, VINTAGE)


def test_rejects_incomplete_response():
    data = payload([("2020-11-01", 6.7)])
    data["count"] = 2

    with pytest.raises(ValueError, match="pagination"):
        clean_vintage_observations(data, VINTAGE)


def test_rejects_duplicate_period():
    data = payload([
        ("2020-11-01", 6.7),
        ("2020-11-01", 6.8),
    ])

    with pytest.raises(ValueError, match="Duplicate"):
        clean_vintage_observations(data, VINTAGE)


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_rejects_nonfinite_values(value):
    data = payload([("2020-11-01", value)])

    with pytest.raises(ValueError, match="not finite"):
        clean_vintage_observations(data, VINTAGE)


def test_missing_indicator_stays_unavailable():
    data = responses()
    data[SERIES["unemployment"]] = payload([
        ("2020-11-01", "."),
    ])

    result = build_us_macro_features(data, OBSERVATION)

    assert result["unemployment_rate"] is None
    assert result["provenance"]["unemployment"] is None


def test_missing_comparison_cpi_does_not_become_zero_inflation():
    data = responses()
    data[SERIES["cpi"]] = payload([("2020-11-01", 110)])

    result = build_us_macro_features(data, OBSERVATION)

    assert result["inflation_rate"] is None


def test_missing_series_is_explicit_error():
    data = responses()
    del data[SERIES["gdp_growth"]]

    with pytest.raises(ValueError, match="Missing FRED response"):
        build_us_macro_features(data, OBSERVATION)