"""
Official Macroeconomic Data Sources

Version 1:
- United States macroeconomic data via FRED

Returns normalized values together with
the actual observation dates and source metadata.
"""

import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv


# ======================================================
# Configuration
# ======================================================

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")

FRED_OBSERVATIONS_URL = (
    "https://api.stlouisfed.org/"
    "fred/series/observations"
)


# ======================================================
# FRED Series Configuration
# ======================================================

US_FRED_SERIES = {
    "policy_rate": {
        "series_id": "FEDFUNDS",
        "name": "Federal Funds Effective Rate",
        "unit": "percent",
        "frequency": "monthly",
    },

    "cpi": {
        "series_id": "CPIAUCSL",
        "name": (
            "Consumer Price Index "
            "for All Urban Consumers"
        ),
        "unit": "index",
        "frequency": "monthly",
    },

    "unemployment": {
        "series_id": "UNRATE",
        "name": "Unemployment Rate",
        "unit": "percent",
        "frequency": "monthly",
    },

    "gdp_growth": {
        "series_id": "A191RL1Q225SBEA",
        "name": "Real GDP Growth",
        "unit": "percent",
        "frequency": "quarterly",
    },
}


# ======================================================
# Generic FRED Fetcher
# ======================================================

def fetch_fred_observations(
    series_id: str,
    limit: int = 24,
):
    """
    Fetch recent observations for one FRED series.
    """

    if not FRED_API_KEY:
        raise ValueError(
            "FRED_API_KEY is missing."
        )

    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit,
    }

    response = requests.get(
        FRED_OBSERVATIONS_URL,
        params=params,
        timeout=15,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"FRED request failed for "
            f"{series_id}: "
            f"HTTP {response.status_code}"
        )

    payload = response.json()

    observations = payload.get(
        "observations",
        []
    )

    cleaned = []

    for observation in observations:

        raw_value = observation.get(
            "value"
        )

        # FRED may use "." for missing values.
        if (
            raw_value is None
            or raw_value == "."
        ):
            continue

        try:
            value = float(raw_value)

        except ValueError:
            continue

        cleaned.append(
            {
                "date": observation.get(
                    "date"
                ),
                "value": value,
            }
        )

    return cleaned


# ======================================================
# Latest Observation
# ======================================================

def latest_fred_observation(
    series_id: str,
):
    """
    Return latest valid FRED observation.
    """

    observations = (
        fetch_fred_observations(
            series_id,
            limit=12,
        )
    )

    if not observations:
        return None

    latest = observations[0]

    return {
        "series_id": series_id,
        "value": round(
            latest["value"],
            4,
        ),
        "observation_date": latest[
            "date"
        ],
        "source": "FRED",
    }


# ======================================================
# US Policy Rate
# ======================================================

def fetch_us_policy_rate():
    """
    Fetch latest Federal Funds Effective Rate.
    """

    series = US_FRED_SERIES[
        "policy_rate"
    ]

    result = latest_fred_observation(
        series["series_id"]
    )

    if result is None:
        return None

    return {
        **result,
        "name": series["name"],
        "unit": series["unit"],
        "frequency": series[
            "frequency"
        ],
    }


# ======================================================
# US Inflation
# ======================================================
def fetch_us_inflation():
    """
    Calculate year-over-year US CPI inflation.

    Matches the latest CPI observation with
    the observation from exactly 12 months earlier.

    Formula:
        ((latest CPI / CPI one year earlier) - 1) * 100
    """

    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    series = US_FRED_SERIES["cpi"]

    observations = fetch_fred_observations(
        series["series_id"],
        limit=30,
    )

    if not observations:
        return None

    latest = observations[0]

    latest_date = datetime.strptime(
        latest["date"],
        "%Y-%m-%d",
    )

    target_date = (
        latest_date
        - relativedelta(years=1)
    ).strftime("%Y-%m-%d")

    year_ago = None

    for observation in observations:
        if observation["date"] == target_date:
            year_ago = observation
            break

    if year_ago is None:
        return None

    if year_ago["value"] == 0:
        return None

    inflation = (
        (
            latest["value"]
            / year_ago["value"]
        )
        - 1
    ) * 100

    return {
        "series_id": series["series_id"],
        "name": "US CPI Inflation YoY",
        "value": round(
            float(inflation),
            2,
        ),
        "unit": "percent",
        "frequency": "monthly",
        "observation_date": latest["date"],
        "comparison_date": year_ago["date"],
        "latest_cpi": round(
            latest["value"],
            4,
        ),
        "year_ago_cpi": round(
            year_ago["value"],
            4,
        ),
        "source": "FRED",
    }
# ======================================================
# US Unemployment
# ======================================================

def fetch_us_unemployment():
    """
    Fetch latest US unemployment rate.
    """

    series = US_FRED_SERIES[
        "unemployment"
    ]

    result = latest_fred_observation(
        series["series_id"]
    )

    if result is None:
        return None

    return {
        **result,
        "name": series["name"],
        "unit": series["unit"],
        "frequency": series[
            "frequency"
        ],
    }


# ======================================================
# US GDP Growth
# ======================================================

def fetch_us_gdp_growth():
    """
    Fetch latest real GDP growth rate.

    The selected FRED series is already expressed
    as percent change from the preceding period
    at a seasonally adjusted annual rate.
    """

    series = US_FRED_SERIES[
        "gdp_growth"
    ]

    result = latest_fred_observation(
        series["series_id"]
    )

    if result is None:
        return None

    return {
        **result,
        "name": series["name"],
        "unit": series["unit"],
        "frequency": series[
            "frequency"
        ],
    }


# ======================================================
# Complete US Macro Snapshot
# ======================================================

def fetch_us_macro_snapshot():
    """
    Fetch current/latest available US
    macroeconomic indicators.
    """

    return {
        "country": "United States",
        "market_code": "US",

        "policy_rate": (
            fetch_us_policy_rate()
        ),

        "inflation": (
            fetch_us_inflation()
        ),

        "gdp_growth": (
            fetch_us_gdp_growth()
        ),

        "unemployment": (
            fetch_us_unemployment()
        ),

        "retrieved_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }

# ======================================================
# World Bank Fallback Data
# ======================================================

WORLD_BANK_BASE_URL = (
    "https://api.worldbank.org/v2"
)


def fetch_world_bank_indicator(
    country_code: str,
    indicator: str,
):
    """
    Fetch latest available non-null World Bank observation.

    Includes retry logic because the World Bank API
    can occasionally respond slowly or time out.
    """

    url = (
        f"{WORLD_BANK_BASE_URL}/country/"
        f"{country_code}/indicator/{indicator}"
    )

    params = {
        "format": "json",
        "per_page": 10,
        "mrnev": 10,
    }

    timeout_values = [
        15,
        30,
        45,
    ]

    last_error = None

    for timeout in timeout_values:

        try:
            response = requests.get(
                url,
                params=params,
                timeout=timeout,
            )

            response.raise_for_status()

            payload = response.json()

            if (
                not isinstance(payload, list)
                or len(payload) < 2
                or not payload[1]
            ):
                return None

            for observation in payload[1]:

                value = observation.get(
                    "value"
                )

                if value is None:
                    continue

                return {
                    "value": round(
                        float(value),
                        2,
                    ),
                    "observation_date": (
                        observation.get("date")
                    ),
                    "source": "World Bank",
                    "is_fallback": True,
                    "frequency": "annual",
                    "indicator": indicator,
                    "country_code": country_code,
                }

        except (
            requests.RequestException,
            ValueError,
            TypeError,
        ) as error:

            last_error = error

            print(
                f"World Bank attempt with "
                f"{timeout}s timeout failed: "
                f"{error}"
            )

    print(
        "World Bank fallback unavailable "
        f"for {indicator}: {last_error}"
    )

    return None

# ======================================================
# India World Bank Fallbacks
# ======================================================

def fetch_india_gdp_fallback():
    """
    Annual real GDP growth fallback.

    Indicator:
    NY.GDP.MKTP.KD.ZG
    """

    result = fetch_world_bank_indicator(
        country_code="IND",
        indicator="NY.GDP.MKTP.KD.ZG",
    )

    if result is None:
        return None

    return {
        **result,
        "name": "GDP Growth",
        "unit": "percent",
    }


def fetch_india_inflation_fallback():
    """
    Annual CPI inflation fallback.

    Indicator:
    FP.CPI.TOTL.ZG
    """

    result = fetch_world_bank_indicator(
        country_code="IND",
        indicator="FP.CPI.TOTL.ZG",
    )

    if result is None:
        return None

    return {
        **result,
        "name": "CPI Inflation",
        "unit": "percent",
    }


def fetch_india_unemployment_fallback():
    """
    Annual national unemployment fallback.

    Indicator:
    SL.UEM.TOTL.NE.ZS
    """

    result = fetch_world_bank_indicator(
        country_code="IND",
        indicator="SL.UEM.TOTL.NE.ZS",
    )

    if result is None:
        return None

    return {
        **result,
        "name": "Unemployment Rate",
        "unit": "percent",
    }

# ======================================================
# India - Official MoSPI Macroeconomic Data
# ======================================================

import calendar

import esankhyiki


MONTH_NUMBER = {
    month: number
    for number, month in enumerate(calendar.month_name)
    if month
}


# ======================================================
# India Inflation - MoSPI CPI
# ======================================================

def fetch_india_inflation():
    """
    Fetch latest available All-India CPI inflation
    from the official MoSPI CPI dataset.

    Configuration:
    - Base year: 2024
    - Series: Current
    - Geography: All India
    - Sector: Combined
    - Measure: CPI (General)

    MoSPI already publishes the inflation percentage,
    so we use the official value directly.
    """

    try:
        filters = {
            "base_year": "2024",
            "series": "Current",
            "state_code": 1,
            "sector_code": 3,
            "limit": 100,
            "page": 1,
        }

        data = esankhyiki.get_data(
            "CPI",
            filters,
        )

        if not data:
            return None

        candidates = []

        for record in data:

            if record.get("division") != "CPI (General)":
                continue

            inflation = record.get("inflation")
            year = record.get("year")
            month = record.get("month")

            if (
                inflation is None
                or year is None
                or month is None
            ):
                continue

            try:
                value = float(inflation)
                year_number = int(year)
                month_number = MONTH_NUMBER.get(
                    month
                )

            except (ValueError, TypeError):
                continue

            if month_number is None:
                continue

            candidates.append(
                {
                    "value": value,
                    "year": year_number,
                    "month": month,
                    "month_number": month_number,
                    "index_value": record.get(
                        "index"
                    ),
                }
            )

        if not candidates:
            return None

        latest = max(
            candidates,
            key=lambda item: (
                item["year"],
                item["month_number"],
            ),
        )

        observation_date = (
            f"{latest['year']}-"
            f"{latest['month_number']:02d}"
        )

        return {
            "name": "CPI Inflation",
            "value": round(
                latest["value"],
                2,
            ),
            "unit": "percent",
            "frequency": "monthly",
            "observation_date": (
                observation_date
            ),
            "month": latest["month"],
            "year": latest["year"],
            "cpi_index": latest[
                "index_value"
            ],
            "source": "MoSPI CPI",
            "is_fallback": False,
        }

    except Exception as error:
        print(
            "MoSPI CPI request failed: "
            f"{error}"
        )

        return fetch_india_inflation_fallback()


# ======================================================
# India Unemployment - MoSPI PLFS
# ======================================================

def fetch_india_unemployment():
    """
    Fetch latest available monthly unemployment rate
    from the official MoSPI PLFS dataset.

    Configuration:
    - Indicator: Unemployment Rate
    - Frequency: Monthly
    - Calendar Year
    - All India
    - Person
    - Age: 15 years and above
    - Sector: Rural + Urban

    Duplicate observations are removed before selecting
    the latest available month.
    """

    try:
        filters = {
            "indicator_code": 3,
            "frequency_code": 3,
            "year_type_code": 2,
            "state_code": 99,
            "gender_code": 3,
            "age_code": 1,
            "sector_code": 3,
            "limit": 100,
            "page": 1,
        }

        data = esankhyiki.get_data(
            "PLFS",
            filters,
        )

        if not data:
            return None

        observations = {}

        for record in data:

            year = record.get("year")
            month = record.get("month")
            value = record.get("value")

            if (
                year is None
                or month is None
                or value is None
            ):
                continue

            try:
                year_number = int(year)
                month_number = MONTH_NUMBER.get(
                    month
                )
                unemployment = float(value)

            except (ValueError, TypeError):
                continue

            if month_number is None:
                continue

            key = (
                year_number,
                month_number,
            )

            observations[key] = {
                "year": year_number,
                "month": month,
                "month_number": month_number,
                "value": unemployment,
            }

        if not observations:
            return None

        latest_key = max(
            observations.keys()
        )

        latest = observations[
            latest_key
        ]

        observation_date = (
            f"{latest['year']}-"
            f"{latest['month_number']:02d}"
        )

        return {
            "name": "Unemployment Rate",
            "value": round(
                latest["value"],
                2,
            ),
            "unit": "percent",
            "frequency": "monthly",
            "observation_date": (
                observation_date
            ),
            "month": latest["month"],
            "year": latest["year"],
            "population": (
                "15 years and above"
            ),
            "gender": "Person",
            "sector": "Rural + Urban",
            "geography": "All India",
            "source": "MoSPI PLFS",
            "is_fallback": False,
        }

    except Exception as error:
        print(
            "MoSPI PLFS request failed: "
            f"{error}"
        )

        return (
            fetch_india_unemployment_fallback()
        )