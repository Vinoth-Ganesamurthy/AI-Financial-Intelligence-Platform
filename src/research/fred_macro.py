"""Build US macro features from FRED responses for a fixed vintage."""

from datetime import date, timedelta
import math


SERIES = {
    "cpi": "CPIAUCSL",
    "unemployment": "UNRATE",
    "monetary_rate": "FEDFUNDS",
    "gdp_growth": "A191RL1Q225SBEA",
}


def vintage_before(observation_date):
    """Exclude observation-day releases conservatively."""
    observation = date.fromisoformat(str(observation_date)[:10])
    return (observation - timedelta(days=1)).isoformat()


def clean_vintage_observations(payload, vintage_date):
    """
    Validate a response requested for one historical as-of date.

    realtime_start/end identify the requested vintage here;
    they are not treated as the original publication date.
    """
    vintage = date.fromisoformat(str(vintage_date)[:10])
    expected = vintage.isoformat()

    if (
        payload.get("realtime_start") != expected
        or payload.get("realtime_end") != expected
    ):
        raise ValueError("FRED response has the wrong vintage.")

    observations = payload.get("observations")
    if not isinstance(observations, list):
        raise ValueError("FRED observations are missing.")

    if int(payload.get("count", len(observations))) != len(observations):
        raise ValueError("FRED response is incomplete; pagination required.")

    cleaned = {}

    for record in observations:
        if (
            record.get("realtime_start") != expected
            or record.get("realtime_end") != expected
        ):
            raise ValueError("FRED record has the wrong vintage.")

        period = date.fromisoformat(record["date"])
        if period > vintage:
            raise ValueError("FRED period is after the vintage date.")

        if record.get("value") in (None, "."):
            continue

        value = float(record["value"])
        if not math.isfinite(value):
            raise ValueError("FRED value is not finite.")

        if period.isoformat() in cleaned:
            raise ValueError("Duplicate FRED observation date.")

        cleaned[period.isoformat()] = value

    return cleaned


def build_us_macro_features(payloads, observation_date):
    """Use only the vintage from the day before the observation."""
    vintage = vintage_before(observation_date)
    series_values = {}

    for series_id in SERIES.values():
        if series_id not in payloads:
            raise ValueError(f"Missing FRED response: {series_id}")

        series_values[series_id] = clean_vintage_observations(
            payloads[series_id],
            vintage,
        )

    provenance = {}

    def latest(name):
        series_id = SERIES[name]
        values = series_values[series_id]

        if not values:
            provenance[name] = None
            return None, None

        period = max(values)
        value = values[period]
        provenance[name] = {
            "series_id": series_id,
            "period_date": period,
            "value": value,
            "vintage_date": vintage,
        }
        return period, value

    cpi_date, cpi = latest("cpi")
    _, unemployment = latest("unemployment")
    _, monetary_rate = latest("monetary_rate")
    _, gdp_growth = latest("gdp_growth")

    inflation = None
    if cpi_date is not None:
        period = date.fromisoformat(cpi_date)
        comparison_date = period.replace(
            year=period.year - 1
        ).isoformat()

        year_ago = series_values[SERIES["cpi"]].get(comparison_date)
        provenance["cpi_comparison"] = (
            {
                "series_id": SERIES["cpi"],
                "period_date": comparison_date,
                "value": year_ago,
                "vintage_date": vintage,
            }
            if year_ago is not None
            else None
        )

        if cpi > 0 and year_ago is not None and year_ago > 0:
            inflation = (cpi / year_ago - 1) * 100

    return {
        "observation_date": str(observation_date)[:10],
        "macro_vintage_date": vintage,
        "macro_source": "FRED historical vintage",
        "inflation_rate": inflation,
        "monetary_rate": monetary_rate,
        "gdp_growth_rate": gdp_growth,
        "unemployment_rate": unemployment,
        "provenance": provenance,
    }