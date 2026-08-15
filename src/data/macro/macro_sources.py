"""
Official Macroeconomic Data Sources

Version 1:
- United States macroeconomic data via FRED

Returns normalized values together with
the actual observation dates and source metadata.
"""
import csv
import io
import os
import re
from datetime import datetime, timezone
from html import unescape
from curl_cffi import requests as browser_requests
import requests
from dotenv import load_dotenv

from src.data.macro.macro_cache import (
    save_macro_cache,
    get_macro_cache,
)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
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
    Fetch recent FRED observations with retry support.
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

    retry_strategy = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=0.5,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],
        allowed_methods=["GET"],
        raise_on_status=False,
    )

    session = requests.Session()

    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=retry_strategy
        ),
    )

    response = session.get(
        FRED_OBSERVATIONS_URL,
        params=params,
        timeout=(5, 20),
    )

    response.raise_for_status()

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

        if (
            raw_value is None
            or raw_value == "."
        ):
            continue

        try:
            value = float(raw_value)

        except (TypeError, ValueError):
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
    Fetch the latest US macroeconomic snapshot.

    A successful complete snapshot is cached. If FRED
    is temporarily unavailable, the last successful
    cached snapshot is returned.
    """

    indicator_names = [
        "policy_rate",
        "inflation",
        "gdp_growth",
        "unemployment",
    ]

    try:
        snapshot = {
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

        missing_indicators = [
            name
            for name in indicator_names
            if snapshot.get(name) is None
        ]

        if missing_indicators:
            raise RuntimeError(
                "Missing US macro indicators: "
                + ", ".join(missing_indicators)
            )

        for name in indicator_names:
            snapshot[name][
                "is_cached"
            ] = False

            snapshot[name][
                "is_fallback"
            ] = False

        save_macro_cache(
            "US",
            "macro_snapshot",
            snapshot,
        )

        return snapshot

    except Exception as error:
        print(
            "FRED US macro snapshot request failed: "
            f"{error}"
        )

        cached = get_macro_cache(
            "US",
            "macro_snapshot",
        )

        if cached is None:
            return None

        cached_at = cached.get(
            "cached_at_utc"
        )

        for name in indicator_names:
            indicator = cached.get(name)

            if indicator:
                indicator["is_cached"] = True
                indicator[
                    "cached_at_utc"
                ] = cached_at

        cached["served_at_utc"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        return cached
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
    "mrnev": 1,
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

from src.data.macro.mospi_client import (
    get_mospi_data,
)

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
    Fetch latest available All-India CPI inflation.

    Priority:
    1. Official MoSPI CPI
    2. Cached official MoSPI value
    3. World Bank annual fallback
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

        data = get_mospi_data(
            "CPI",
            filters,
        )

        if not data:
            raise ValueError(
                "No MoSPI CPI data returned."
            )

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
                month_number = MONTH_NUMBER.get(month)

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
                    "index_value": record.get("index"),
                }
            )

        if not candidates:
            raise ValueError(
                "No valid CPI General records found."
            )

        latest = max(
            candidates,
            key=lambda item: (
                item["year"],
                item["month_number"],
            ),
        )

        result = {
            "name": "CPI Inflation",
            "value": round(
                latest["value"],
                2,
            ),
            "unit": "percent",
            "frequency": "monthly",
            "observation_date": (
                f"{latest['year']}-"
                f"{latest['month_number']:02d}"
            ),
            "month": latest["month"],
            "year": latest["year"],
            "cpi_index": latest["index_value"],
            "source": "MoSPI CPI",
            "is_fallback": False,
            "is_cached": False,
        }

        save_macro_cache(
            "IN",
            "inflation",
            result,
        )

        return result

    except Exception as error:
        print(
            "MoSPI CPI request failed: "
            f"{error}"
        )

        cached = get_macro_cache(
            "IN",
            "inflation",
        )

        if cached:
            cached["is_fallback"] = False
            return cached

        return fetch_india_inflation_fallback()

# ======================================================
# India Unemployment - MoSPI PLFS
# ======================================================

def fetch_india_unemployment():
    """
    Fetch latest available monthly unemployment rate.

    Priority:
    1. Official MoSPI PLFS
    2. Cached official MoSPI value
    3. World Bank annual fallback
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

        data = get_mospi_data(
            "PLFS",
            filters,
        )

        if not data:
            raise ValueError(
                "No MoSPI PLFS data returned."
            )

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
                month_number = MONTH_NUMBER.get(month)
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
            raise ValueError(
                "No valid PLFS unemployment records found."
            )

        latest_key = max(
            observations.keys()
        )

        latest = observations[
            latest_key
        ]

        result = {
            "name": "Unemployment Rate",
            "value": round(
                latest["value"],
                2,
            ),
            "unit": "percent",
            "frequency": "monthly",
            "observation_date": (
                f"{latest['year']}-"
                f"{latest['month_number']:02d}"
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
            "is_cached": False,
        }

        save_macro_cache(
            "IN",
            "unemployment",
            result,
        )

        return result

    except Exception as error:
        print(
            "MoSPI PLFS request failed: "
            f"{error}"
        )

        cached = get_macro_cache(
            "IN",
            "unemployment",
        )

        if cached:
            cached["is_fallback"] = False
            return cached

        return (
            fetch_india_unemployment_fallback()
        )

RBI_CURRENT_RATES_URL = (
    "https://www.rbi.org.in/"
)


def _parse_rbi_policy_rate_html(
    html,
):
    """
    Parse the current RBI policy repo rate and the
    website's last-updated date.
    """

    page_text = BeautifulSoup(
        html,
        "html.parser",
    ).get_text(
        " ",
        strip=True,
    )

    rate_match = re.search(
        (
            r"Policy\s+Repo\s+Rate\s*:\s*"
            r"([0-9]+(?:\.[0-9]+)?)\s*%"
        ),
        page_text,
        flags=re.IGNORECASE,
    )

    if rate_match is None:
        raise ValueError(
            "RBI policy repo rate was not found."
        )

    rate = float(
        rate_match.group(1)
    )

    updated_match = re.search(
        (
            r"Website\s+last\s+updated\s+date"
            r"\s*:\s*"
            r"([A-Za-z]{3}\s+\d{1,2},\s+\d{4})"
        ),
        page_text,
        flags=re.IGNORECASE,
    )

    page_last_updated_date = None

    if updated_match is not None:
        try:
            page_last_updated_date = (
                datetime.strptime(
                    updated_match.group(1),
                    "%b %d, %Y",
                )
                .date()
                .isoformat()
            )

        except ValueError:
            page_last_updated_date = None

    return {
        "value": rate,
        "page_last_updated_date": (
            page_last_updated_date
        ),
    }


def fetch_india_policy_rate():
    """
    Fetch India's current RBI policy repo rate.

    Priority:
    1. RBI official current-rates page
    2. Last successfully cached RBI observation
    """

    try:
        response = browser_requests.get(
            RBI_CURRENT_RATES_URL,
            impersonate="chrome",
            headers={
                "Accept": "text/html",
                "Accept-Language": "en-IN,en;q=0.9",
            },
            timeout=30,
        )

        response.raise_for_status()

        parsed = _parse_rbi_policy_rate_html(
            response.text
        )

        result = {
            "name": "Policy Repo Rate",
            "value": round(
                parsed["value"],
                2,
            ),
            "unit": "percent",
            "frequency": "event_driven",
            "observation_date": (
                datetime.now(
                    timezone.utc
                )
                .date()
                .isoformat()
            ),
            "page_last_updated_date": (
                parsed[
                    "page_last_updated_date"
                ]
            ),
            "source": "Reserve Bank of India",
            "source_url": (
                RBI_CURRENT_RATES_URL
            ),
            "series_id": (
                "RBI_POLICY_REPO_RATE"
            ),
            "is_policy_rate": True,
            "is_fallback": False,
            "is_cached": False,
        }

        save_macro_cache(
            "IN",
            "policy_rate",
            result,
        )

        return result

    except Exception as error:
        print(
            "RBI policy rate request failed: "
            f"{error}"
        )

        cached = get_macro_cache(
            "IN",
            "policy_rate",
        )

        if cached:
            cached["is_fallback"] = False
            cached["is_policy_rate"] = True
            return cached

        return None
    
def fetch_india_gdp_growth():
    """
    Fetch India's latest official quarterly real GDP
    growth rate.

    Source:
    MoSPI National Accounts Statistics

    Indicator:
    22 - GDP Growth Rate

    Priority:
    1. Official MoSPI NAS
    2. Cached official observation
    3. World Bank annual fallback
    """

    try:
        filters = {
            "base_year": "2022-23",
            "series": "Current",
            "frequency_code": "Quarterly",
            "indicator_code": 22,
            "limit": 100,
            "page": 1,
        }

        data = get_mospi_data(
            "NAS",
            filters,
        )

        if not data:
            raise ValueError(
                "No MoSPI NAS GDP data returned."
            )

        candidates = []

        for record in data:
            if (
                record.get("indicator")
                != "GDP Growth Rate"
            ):
                continue

            fiscal_year = record.get("year")
            quarter = record.get("quarter")
            real_growth = record.get(
                "constant_price"
            )

            if (
                fiscal_year is None
                or quarter is None
                or real_growth is None
            ):
                continue

            year_match = re.fullmatch(
                r"(\d{4})-(\d{2})",
                str(fiscal_year),
            )

            quarter_match = re.fullmatch(
                r"Q([1-4])",
                str(quarter),
                flags=re.IGNORECASE,
            )

            if (
                year_match is None
                or quarter_match is None
            ):
                continue

            try:
                fiscal_start_year = int(
                    year_match.group(1)
                )

                quarter_number = int(
                    quarter_match.group(1)
                )

                growth_value = float(
                    real_growth
                )

            except (TypeError, ValueError):
                continue

            candidates.append(
                {
                    "fiscal_year": fiscal_year,
                    "fiscal_start_year": (
                        fiscal_start_year
                    ),
                    "quarter": quarter_number,
                    "value": growth_value,
                    "base_year": record.get(
                        "base_year"
                    ),
                    "series": record.get(
                        "series"
                    ),
                }
            )

        if not candidates:
            raise ValueError(
                "No valid MoSPI GDP growth "
                "records found."
            )

        latest = max(
            candidates,
            key=lambda item: (
                item["fiscal_start_year"],
                item["quarter"],
            ),
        )

        result = {
            "name": "Real GDP Growth",
            "value": round(
                latest["value"],
                2,
            ),
            "unit": "percent",
            "frequency": "quarterly",
            "observation_date": (
                f"{latest['fiscal_year']}-"
                f"Q{latest['quarter']}"
            ),
            "fiscal_year": (
                latest["fiscal_year"]
            ),
            "quarter": latest["quarter"],
            "growth_type": "Year-on-Year",
            "measure": (
                "GDP Growth Rate at "
                "Constant Prices"
            ),
            "base_year": (
                latest["base_year"]
            ),
            "series": latest["series"],
            "source": "MoSPI NAS",
            "resource_id": (
                "NAS indicator 22"
            ),
            "is_fallback": False,
            "is_cached": False,
        }

        save_macro_cache(
            "IN",
            "gdp_growth",
            result,
        )

        return result

    except Exception as error:
        print(
            "India GDP official source failed: "
            f"{error}"
        )

        cached = get_macro_cache(
            "IN",
            "gdp_growth",
        )

        if cached:
            cached["is_fallback"] = False
            return cached

        return fetch_india_gdp_fallback()
    
def fetch_india_macro_snapshot():
    """
    Fetch the latest available macroeconomic snapshot for India.

    Each indicator independently uses its configured official source,
    cache, and fallback strategy.
    """

    return {
        "country": "India",
        "market_code": "IN",
        "inflation": fetch_india_inflation(),
        "policy_rate": fetch_india_policy_rate(),
        "gdp_growth": fetch_india_gdp_growth(),
        "unemployment": fetch_india_unemployment(),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }

def fetch_singapore_inflation():
    """
    Fetch Singapore's latest monthly CPI inflation.

    Source:
    Singapore Department of Statistics (SingStat)

    Table:
    M213781 - Percent Change in CPI over the
    corresponding period of the previous year.

    Priority:
    1. SingStat official API
    2. Cached official SingStat value
    """

    try:
        url = (
            "https://tablebuilder.singstat.gov.sg/"
            "api/table/tabledata/M213781"
        )

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=20,
        )

        response.raise_for_status()

        payload = response.json()

        data = payload.get("Data", {})

        rows = data.get("row", [])

        # Find the overall CPI row
        all_items_row = None

        for row in rows:
            if row.get("rowText") == "All Items":
                all_items_row = row
                break

        if all_items_row is None:
            raise ValueError(
                "SingStat CPI 'All Items' row not found."
            )

        observations = []

        for column in all_items_row.get(
            "columns",
            [],
        ):
            date_text = column.get("key")
            raw_value = column.get("value")

            if not date_text or raw_value in (
                None,
                "",
                "na",
                "NA",
            ):
                continue

            try:
                observation_date = (
                    datetime.strptime(
                        date_text,
                        "%Y %b",
                    )
                )

                value = float(raw_value)

            except (ValueError, TypeError):
                continue

            observations.append(
                {
                    "date": observation_date,
                    "date_text": date_text,
                    "value": value,
                }
            )

        if not observations:
            raise ValueError(
                "No valid Singapore CPI observations found."
            )

        latest = max(
            observations,
            key=lambda item: item["date"],
        )

        result = {
            "name": "CPI Inflation",
            "value": round(
                latest["value"],
                2,
            ),
            "unit": "percent",
            "frequency": "monthly",
            "observation_date": (
                latest["date"].strftime(
                    "%Y-%m"
                )
            ),
            "month": (
                latest["date"].strftime(
                    "%B"
                )
            ),
            "year": latest["date"].year,
            "source": "Singapore Department of Statistics",
            "resource_id": "M213781",
            "data_last_updated": data.get(
                "dataLastUpdated"
            ),
            "is_fallback": False,
            "is_cached": False,
        }

        save_macro_cache(
            "SG",
            "inflation",
            result,
        )

        return result

    except Exception as error:
        print(
            "SingStat CPI request failed: "
            f"{error}"
        )

        cached = get_macro_cache(
            "SG",
            "inflation",
        )

        if cached:
            cached["is_fallback"] = False
            return cached

        return None

def fetch_singapore_unemployment():
    """
    Fetch Singapore's latest seasonally adjusted
    total unemployment rate.

    Source:
    Singapore Ministry of Manpower via SingStat

    Table:
    M182342 - Unemployment Rate (End Of Period),
    Quarterly, Seasonally Adjusted.

    Priority:
    1. SingStat official API
    2. Cached official value
    """

    try:
        url = (
            "https://tablebuilder.singstat.gov.sg/"
            "api/table/tabledata/M182342"
        )

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=20,
        )

        response.raise_for_status()

        payload = response.json()
        data = payload.get("Data", {})
        rows = data.get("row", [])

        target_row = None

        for row in rows:
            if row.get("rowText") == (
                "Total Unemployment Rate, (SA)"
            ):
                target_row = row
                break

        if target_row is None:
            raise ValueError(
                "Singapore total unemployment row not found."
            )

        observations = []

        for column in target_row.get(
            "columns",
            [],
        ):
            date_text = column.get("key")
            raw_value = column.get("value")

            if (
                not date_text
                or raw_value in (
                    None,
                    "",
                    "na",
                    "NA",
                )
            ):
                continue

            try:
                value = float(raw_value)

                cleaned_date = (
                    date_text
                    .replace(" ", "")
                )

                year = int(
                    cleaned_date[:4]
                )

                quarter = int(
                    cleaned_date[4]
                )

            except (
                ValueError,
                TypeError,
                IndexError,
            ):
                continue

            if quarter not in (
                1,
                2,
                3,
                4,
            ):
                continue

            observations.append(
                {
                    "year": year,
                    "quarter": quarter,
                    "value": value,
                }
            )

        if not observations:
            raise ValueError(
                "No valid Singapore unemployment observations found."
            )

        latest = max(
            observations,
            key=lambda item: (
                item["year"],
                item["quarter"],
            ),
        )

        result = {
            "name": "Unemployment Rate",
            "value": round(
                latest["value"],
                2,
            ),
            "unit": "percent",
            "frequency": "quarterly",
            "observation_date": (
                f"{latest['year']}-Q"
                f"{latest['quarter']}"
            ),
            "year": latest["year"],
            "quarter": latest["quarter"],
            "adjustment": (
                "Seasonally Adjusted"
            ),
            "population": "Total",
            "source": (
                "Singapore Ministry of Manpower"
            ),
            "resource_id": "M182342",
            "data_last_updated": data.get(
                "dataLastUpdated"
            ),
            "is_fallback": False,
            "is_cached": False,
        }

        save_macro_cache(
            "SG",
            "unemployment",
            result,
        )

        return result

    except Exception as error:
        print(
            "Singapore unemployment request failed: "
            f"{error}"
        )

        cached = get_macro_cache(
            "SG",
            "unemployment",
        )

        if cached:
            cached["is_fallback"] = False
            return cached

        return None

def fetch_singapore_gdp_growth():
    """
    Fetch Singapore's latest seasonally adjusted
    quarter-on-quarter real GDP growth.

    Source:
    Singapore Department of Statistics via SingStat

    Table:
    M015902 - GDP in Chained (2015) Dollars,
    Seasonally Adjusted, Quarter-on-Quarter Growth.

    Priority:
    1. SingStat official API
    2. Cached official value
    """

    try:
        url = (
            "https://tablebuilder.singstat.gov.sg/"
            "api/table/tabledata/M015902"
        )

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=20,
        )

        response.raise_for_status()

        payload = response.json()
        data = payload.get("Data", {})
        rows = data.get("row", [])

        target_row = None

        for row in rows:
            row_text = (
                row.get("rowText") or ""
            ).strip().lower()

            if (
                "gdp" in row_text
                and "chained" in row_text
            ):
                target_row = row
                break

        if target_row is None:
            raise ValueError(
                "Singapore GDP row not found."
            )

        observations = []

        for column in target_row.get("columns", []):
            date_text = column.get("key")
            raw_value = column.get("value")

            if (
                not date_text
                or raw_value in (
                    None,
                    "",
                    "na",
                    "NA",
                )
            ):
                continue

            try:
                value = float(raw_value)

                cleaned_date = date_text.replace(
                    " ",
                    "",
                )

                year = int(cleaned_date[:4])
                quarter = int(cleaned_date[4])

            except (
                ValueError,
                TypeError,
                IndexError,
            ):
                continue

            if quarter not in (1, 2, 3, 4):
                continue

            observations.append(
                {
                    "year": year,
                    "quarter": quarter,
                    "value": value,
                }
            )

        if not observations:
            raise ValueError(
                "No valid Singapore GDP observations found."
            )

        latest = max(
            observations,
            key=lambda item: (
                item["year"],
                item["quarter"],
            ),
        )

        result = {
            "name": "Real GDP Growth",
            "value": round(
                latest["value"],
                2,
            ),
            "unit": "percent",
            "frequency": "quarterly",
            "observation_date": (
                f"{latest['year']}-Q"
                f"{latest['quarter']}"
            ),
            "year": latest["year"],
            "quarter": latest["quarter"],
            "growth_type": "Quarter-on-Quarter",
            "adjustment": "Seasonally Adjusted",
            "source": (
                "Singapore Department of Statistics"
            ),
            "resource_id": "M015902",
            "data_last_updated": data.get(
                "dataLastUpdated"
            ),
            "is_fallback": False,
            "is_cached": False,
        }

        save_macro_cache(
            "SG",
            "gdp_growth",
            result,
        )

        return result

    except Exception as error:
        print(
            "Singapore GDP request failed: "
            f"{error}"
        )

        cached = get_macro_cache(
            "SG",
            "gdp_growth",
        )

        if cached:
            cached["is_fallback"] = False
            return cached

        return None


# ======================================================
# Singapore Policy-Rate Proxy - MAS SORA
# ======================================================

MAS_DOMESTIC_INTEREST_RATES_URL = (
    "https://eservices.mas.gov.sg/"
    "statistics/dir/domesticinterestrates.aspx"
)


def _extract_hidden_form_value(
    page_html,
    field_name,
):
    """Extract one ASP.NET hidden form value."""

    pattern = (
        rf'name="{re.escape(field_name)}"'
        rf'[^>]*value="([^"]*)"'
    )

    match = re.search(
        pattern,
        page_html,
        flags=re.IGNORECASE,
    )

    if match is None:
        raise ValueError(
            f"MAS form field not found: {field_name}"
        )

    return unescape(match.group(1))


def _clean_html_cell(cell_html):
    """Convert one MAS table cell to plain text."""

    text = re.sub(
        r"<[^>]+>",
        " ",
        cell_html,
    )

    return " ".join(
        unescape(text)
        .replace("\xa0", " ")
        .split()
    )


def _parse_mas_sora_observations(page_html):
    """Parse SORA observations from the MAS result table."""

    header_position = page_html.find(
        "ContentPlaceHolder1_soraHeader"
    )

    if header_position < 0:
        raise ValueError(
            "MAS SORA result table not found."
        )

    sora_html = page_html[header_position:]
    observations = []
    current_year = None
    current_month = None

    rows = re.findall(
        r"<tr[^>]*>(.*?)</tr>",
        sora_html,
        flags=(
            re.IGNORECASE
            | re.DOTALL
        ),
    )

    for row_html in rows:
        cells = [
            _clean_html_cell(cell)
            for cell in re.findall(
                r"<td[^>]*>(.*?)</td>",
                row_html,
                flags=(
                    re.IGNORECASE
                    | re.DOTALL
                ),
            )
        ]

        if len(cells) < 5:
            continue

        if cells[0]:
            try:
                current_year = int(cells[0])
            except ValueError:
                continue

        if cells[1]:
            current_month = cells[1]

        if (
            current_year is None
            or current_month is None
            or not cells[2]
            or not cells[4]
        ):
            continue

        try:
            value_date = datetime.strptime(
                (
                    f"{current_year} "
                    f"{current_month} "
                    f"{cells[2]}"
                ),
                "%Y %b %d",
            )

            publication_date = datetime.strptime(
                cells[3],
                "%d %b %Y",
            )

            value = float(cells[4])

        except (ValueError, TypeError):
            continue

        observations.append(
            {
                "value_date": value_date,
                "publication_date": publication_date,
                "value": value,
            }
        )

    return observations


def fetch_singapore_policy_rate():
    """
    Fetch Singapore's latest official daily SORA.

    Singapore implements monetary policy through its
    exchange-rate framework rather than a conventional
    central-bank policy interest rate. SORA is therefore
    stored as the domestic overnight rate proxy.

    Priority:
    1. MAS official Domestic Interest Rates table
    2. Cached official MAS value
    """

    try:
        session = requests.Session()

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html",
        }

        initial_response = session.get(
            MAS_DOMESTIC_INTEREST_RATES_URL,
            headers=headers,
            timeout=20,
        )

        initial_response.raise_for_status()

        now = datetime.now()

        form_data = {
            "__VIEWSTATE": (
                _extract_hidden_form_value(
                    initial_response.text,
                    "__VIEWSTATE",
                )
            ),
            "__VIEWSTATEGENERATOR": (
                _extract_hidden_form_value(
                    initial_response.text,
                    "__VIEWSTATEGENERATOR",
                )
            ),
            "__EVENTVALIDATION": (
                _extract_hidden_form_value(
                    initial_response.text,
                    "__EVENTVALIDATION",
                )
            ),
            (
                "ctl00$ContentPlaceHolder1$"
                "StartYearDropDownList"
            ): str(now.year),
            (
                "ctl00$ContentPlaceHolder1$"
                "EndYearDropDownList"
            ): str(now.year),
            (
                "ctl00$ContentPlaceHolder1$"
                "StartMonthDropDownList"
            ): "1",
            (
                "ctl00$ContentPlaceHolder1$"
                "EndMonthDropDownList"
            ): str(now.month),
            (
                "ctl00$ContentPlaceHolder1$"
                "ColumnsCheckBoxList$13"
            ): "on",
            (
                "ctl00$ContentPlaceHolder1$Button1"
            ): "Display",
        }

        response = session.post(
            MAS_DOMESTIC_INTEREST_RATES_URL,
            data=form_data,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()

        observations = (
            _parse_mas_sora_observations(
                response.text
            )
        )

        if not observations:
            raise ValueError(
                "No valid MAS SORA observations found."
            )

        latest = max(
            observations,
            key=lambda item: item[
                "value_date"
            ],
        )

        result = {
            "name": (
                "Singapore Overnight Rate Average"
            ),
            "value": round(
                latest["value"],
                4,
            ),
            "unit": "percent_per_annum",
            "frequency": "daily",
            "observation_date": (
                latest["value_date"]
                .strftime("%Y-%m-%d")
            ),
            "publication_date": (
                latest["publication_date"]
                .strftime("%Y-%m-%d")
            ),
            "source": (
                "Monetary Authority of Singapore"
            ),
            "series_id": "SORA",
            "policy_framework": (
                "Exchange-rate-centred monetary policy"
            ),
            "role": (
                "Domestic overnight interest-rate proxy"
            ),
            "is_policy_rate": False,
            "is_fallback": False,
            "is_cached": False,
        }

        save_macro_cache(
            "SG",
            "policy_rate",
            result,
        )

        return result

    except Exception as error:
        print(
            "MAS SORA request failed: "
            f"{error}"
        )

        cached = get_macro_cache(
            "SG",
            "policy_rate",
        )

        if cached:
            cached["is_fallback"] = False
            return cached

        return None


def fetch_singapore_macro_snapshot():
    """
    Fetch Singapore's latest macroeconomic snapshot.

    Each indicator independently uses its official
    source and cached official-data fallback.
    """

    return {
        "country": "Singapore",
        "market_code": "SG",
        "inflation": (
            fetch_singapore_inflation()
        ),
        "policy_rate": (
            fetch_singapore_policy_rate()
        ),
        "gdp_growth": (
            fetch_singapore_gdp_growth()
        ),
        "unemployment": (
            fetch_singapore_unemployment()
        ),
        "retrieved_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }

# ======================================================
# Australia Policy Rate - RBA
# ======================================================

RBA_MONEY_MARKET_CSV_URL = (
    "https://www.rba.gov.au/"
    "statistics/tables/csv/f1-data.csv"
)


def fetch_australia_policy_rate():
    """
    Fetch Australia's latest official cash rate target.

    Source:
    Reserve Bank of Australia Statistical Table F1.

    Priority:
    1. RBA official daily CSV
    2. Cached official RBA value
    """

    try:
        response = browser_requests.get(
    RBA_MONEY_MARKET_CSV_URL,
    impersonate="chrome",
    headers={
        "Accept": "text/csv",
    },
    timeout=20,
    )

        response.raise_for_status()

        csv_text = response.content.decode(
            "utf-8-sig"
        )

        rows = list(
            csv.reader(
                io.StringIO(csv_text)
            )
        )

        publication_date = None
        series_id = None
        data_start_index = None

        for index, row in enumerate(rows):
            if not row:
                continue

            row_name = row[0].strip()

            if (
                row_name == "Publication date"
                and len(row) > 1
            ):
                publication_date = row[1].strip()

            elif (
                row_name == "Series ID"
                and len(row) > 1
            ):
                series_id = row[1].strip()
                data_start_index = index + 1
                break

        if data_start_index is None:
            raise ValueError(
                "RBA F1 data section not found."
            )

        if series_id != "FIRMMCRTD":
            raise ValueError(
                "Unexpected RBA cash-rate series."
            )

        observations = []

        for row in rows[data_start_index:]:
            if len(row) < 2:
                continue

            raw_date = row[0].strip()
            raw_value = row[1].strip()

            if not raw_date or not raw_value:
                continue

            try:
                observation_date = (
                    datetime.strptime(
                        raw_date,
                        "%d-%b-%Y",
                    )
                )

                value = float(raw_value)

            except (ValueError, TypeError):
                continue

            observations.append(
                {
                    "date": observation_date,
                    "value": value,
                }
            )

        if not observations:
            raise ValueError(
                "No valid RBA cash-rate observations found."
            )

        latest = max(
            observations,
            key=lambda item: item["date"],
        )

        normalized_publication_date = None

        if publication_date:
            try:
                normalized_publication_date = (
                    datetime.strptime(
                        publication_date,
                        "%d-%b-%Y",
                    ).strftime("%Y-%m-%d")
                )

            except ValueError:
                normalized_publication_date = (
                    publication_date
                )

        result = {
            "name": "Cash Rate Target",
            "value": round(
                latest["value"],
                2,
            ),
            "unit": "percent",
            "frequency": "daily",
            "observation_date": (
                latest["date"].strftime(
                    "%Y-%m-%d"
                )
            ),
            "publication_date": (
                normalized_publication_date
            ),
            "source": (
                "Reserve Bank of Australia"
            ),
            "resource_id": "F1",
            "series_id": series_id,
            "is_policy_rate": True,
            "is_fallback": False,
            "is_cached": False,
        }

        save_macro_cache(
            "AU",
            "policy_rate",
            result,
        )

        return result

    except Exception as error:
        print(
            "RBA cash-rate request failed: "
            f"{error}"
        )

        cached = get_macro_cache(
            "AU",
            "policy_rate",
        )

        if cached:
            cached["is_fallback"] = False
            return cached

        return None

# ======================================================
# Australia Inflation - ABS
# ======================================================

ABS_CPI_RELEASE_URL = (
    "https://www.abs.gov.au/statistics/economy/"
    "price-indexes-and-inflation/"
    "consumer-price-index-australia/latest-release"
)

ABS_CPI_TABLE_CAPTION = (
    "All groups CPI, Australia, monthly "
    "and annual movement (%)"
)


def fetch_australia_inflation():
    """
    Fetch Australia's latest monthly headline CPI inflation.

    Priority:
    1. Official ABS monthly CPI table
    2. Cached official ABS value
    """

    try:
        response = browser_requests.get(
            ABS_CPI_RELEASE_URL,
            impersonate="chrome",
            headers={
                "Accept": "text/html",
            },
            timeout=30,
        )

        response.raise_for_status()

        page_html = response.text

        caption_marker = (
            f"<caption>{ABS_CPI_TABLE_CAPTION}"
            "</caption>"
        )

        table_start = page_html.find(
            caption_marker
        )

        if table_start < 0:
            raise ValueError(
                "ABS monthly CPI table not found."
            )

        table_end = page_html.find(
            "</table>",
            table_start,
        )

        if table_end < 0:
            raise ValueError(
                "ABS monthly CPI table is incomplete."
            )

        table_html = page_html[
            table_start:table_end
        ]

        observations = []

        rows = re.findall(
            r"<tr[^>]*>(.*?)</tr>",
            table_html,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        for row_html in rows:
            date_match = re.search(
                (
                    r'<th[^>]*class="row-header"'
                    r"[^>]*>(.*?)</th>"
                ),
                row_html,
                flags=(
                    re.IGNORECASE
                    | re.DOTALL
                ),
            )

            if date_match is None:
                continue

            cells = [
                _clean_html_cell(cell)
                for cell in re.findall(
                    r"<td[^>]*>(.*?)</td>",
                    row_html,
                    flags=(
                        re.IGNORECASE
                        | re.DOTALL
                    ),
                )
            ]

            if len(cells) < 2:
                continue

            date_text = _clean_html_cell(
                date_match.group(1)
            )

            monthly_change_text = cells[0]
            annual_change_text = cells[1]

            if not annual_change_text:
                continue

            try:
                observation_date = (
                    datetime.strptime(
                        date_text,
                        "%b-%y",
                    )
                )

                monthly_change = float(
                    monthly_change_text
                )

                annual_change = float(
                    annual_change_text
                )

            except (ValueError, TypeError):
                continue

            observations.append(
                {
                    "date": observation_date,
                    "monthly_change": (
                        monthly_change
                    ),
                    "annual_change": (
                        annual_change
                    ),
                }
            )

        if not observations:
            raise ValueError(
                "No valid ABS CPI observations found."
            )

        latest = max(
            observations,
            key=lambda item: item["date"],
        )

        result = {
            "name": "CPI Inflation",
            "value": round(
                latest["annual_change"],
                2,
            ),
            "monthly_change": round(
                latest["monthly_change"],
                2,
            ),
            "unit": "percent",
            "frequency": "monthly",
            "observation_date": (
                latest["date"].strftime(
                    "%Y-%m"
                )
            ),
            "month": (
                latest["date"].strftime(
                    "%B"
                )
            ),
            "year": latest["date"].year,
            "measure": (
                "All Groups CPI annual change"
            ),
            "geography": (
                "Weighted average of eight "
                "capital cities"
            ),
            "source": (
                "Australian Bureau of Statistics"
            ),
            "resource_id": (
                "Consumer Price Index, Australia"
            ),
            "is_fallback": False,
            "is_cached": False,
        }

        save_macro_cache(
            "AU",
            "inflation",
            result,
        )

        return result

    except Exception as error:
        print(
            "ABS CPI request failed: "
            f"{error}"
        )

        cached = get_macro_cache(
            "AU",
            "inflation",
        )

        if cached:
            cached["is_fallback"] = False
            return cached

        return None

# ======================================================
# Australia Unemployment - ABS
# ======================================================

ABS_LABOUR_FORCE_RELEASE_URL = (
    "https://www.abs.gov.au/statistics/labour/"
    "employment-and-unemployment/"
    "labour-force-australia/latest-release"
)


def fetch_australia_unemployment():
    """
    Fetch Australia's latest monthly seasonally
    adjusted unemployment rate.

    Priority:
    1. Official ABS Labour Force table
    2. Cached official ABS value
    """

    try:
        response = browser_requests.get(
            ABS_LABOUR_FORCE_RELEASE_URL,
            impersonate="chrome",
            headers={
                "Accept": "text/html",
            },
            timeout=30,
        )

        response.raise_for_status()

        page_html = response.text

        caption_marker = (
            "<caption>Unemployment rate</caption>"
        )

        table_start = page_html.find(
            caption_marker
        )

        if table_start < 0:
            raise ValueError(
                "ABS unemployment table not found."
            )

        table_end = page_html.find(
            "</table>",
            table_start,
        )

        if table_end < 0:
            raise ValueError(
                "ABS unemployment table is incomplete."
            )

        table_html = page_html[
            table_start:table_end
        ]

        observations = []

        rows = re.findall(
            r"<tr[^>]*>(.*?)</tr>",
            table_html,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        for row_html in rows:
            date_match = re.search(
                (
                    r'<th[^>]*class="row-header"'
                    r"[^>]*>(.*?)</th>"
                ),
                row_html,
                flags=(
                    re.IGNORECASE
                    | re.DOTALL
                ),
            )

            if date_match is None:
                continue

            cells = [
                _clean_html_cell(cell)
                for cell in re.findall(
                    r"<td[^>]*>(.*?)</td>",
                    row_html,
                    flags=(
                        re.IGNORECASE
                        | re.DOTALL
                    ),
                )
            ]

            if len(cells) < 2 or not cells[1]:
                continue

            try:
                observation_date = (
                    datetime.strptime(
                        _clean_html_cell(
                            date_match.group(1)
                        ),
                        "%b-%y",
                    )
                )

                trend_rate = (
                    float(cells[0])
                    if cells[0]
                    else None
                )

                unemployment_rate = float(
                    cells[1]
                )

            except (ValueError, TypeError):
                continue

            observations.append(
                {
                    "date": observation_date,
                    "trend_rate": trend_rate,
                    "value": unemployment_rate,
                }
            )

        if not observations:
            raise ValueError(
                "No valid ABS unemployment "
                "observations found."
            )

        latest = max(
            observations,
            key=lambda item: item["date"],
        )

        result = {
            "name": "Unemployment Rate",
            "value": round(
                latest["value"],
                2,
            ),
            "trend_rate": (
                round(
                    latest["trend_rate"],
                    2,
                )
                if latest["trend_rate"] is not None
                else None
            ),
            "unit": "percent",
            "frequency": "monthly",
            "observation_date": (
                latest["date"].strftime(
                    "%Y-%m"
                )
            ),
            "month": (
                latest["date"].strftime(
                    "%B"
                )
            ),
            "year": latest["date"].year,
            "adjustment": (
                "Seasonally Adjusted"
            ),
            "population": "Total",
            "geography": "Australia",
            "source": (
                "Australian Bureau of Statistics"
            ),
            "resource_id": (
                "Labour Force, Australia"
            ),
            "is_fallback": False,
            "is_cached": False,
        }

        save_macro_cache(
            "AU",
            "unemployment",
            result,
        )

        return result

    except Exception as error:
        print(
            "ABS unemployment request failed: "
            f"{error}"
        )

        cached = get_macro_cache(
            "AU",
            "unemployment",
        )

        if cached:
            cached["is_fallback"] = False
            return cached

        return None

# ======================================================
# Australia GDP Growth - ABS
# ======================================================

ABS_NATIONAL_ACCOUNTS_RELEASE_URL = (
    "https://www.abs.gov.au/statistics/economy/"
    "national-accounts/"
    "australian-national-accounts-national-income-"
    "expenditure-and-product/latest-release"
)

ABS_GDP_TABLE_CAPTION = (
    "Gross domestic product, chain volume measures, "
    "seasonally adjusted"
)


def fetch_australia_gdp_growth():
    """
    Fetch Australia's latest quarterly real GDP growth.

    Priority:
    1. Official ABS National Accounts table
    2. Cached official ABS value
    """

    try:
        response = browser_requests.get(
            ABS_NATIONAL_ACCOUNTS_RELEASE_URL,
            impersonate="chrome",
            headers={
                "Accept": "text/html",
            },
            timeout=30,
        )

        response.raise_for_status()

        page_html = response.text

        caption_marker = (
            f"<caption>{ABS_GDP_TABLE_CAPTION}"
            "</caption>"
        )

        table_start = page_html.find(
            caption_marker
        )

        if table_start < 0:
            raise ValueError(
                "ABS real GDP table not found."
            )

        table_end = page_html.find(
            "</table>",
            table_start,
        )

        if table_end < 0:
            raise ValueError(
                "ABS real GDP table is incomplete."
            )

        table_html = page_html[
            table_start:table_end
        ]

        observations = []

        rows = re.findall(
            r"<tr[^>]*>(.*?)</tr>",
            table_html,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )

        for row_html in rows:
            date_match = re.search(
                (
                    r'<th[^>]*class="row-header"'
                    r"[^>]*>(.*?)</th>"
                ),
                row_html,
                flags=(
                    re.IGNORECASE
                    | re.DOTALL
                ),
            )

            if date_match is None:
                continue

            cells = [
                _clean_html_cell(cell)
                for cell in re.findall(
                    r"<td[^>]*>(.*?)</td>",
                    row_html,
                    flags=(
                        re.IGNORECASE
                        | re.DOTALL
                    ),
                )
            ]

            if (
                len(cells) < 2
                or not cells[0]
                or not cells[1]
            ):
                continue

            try:
                observation_date = (
                    datetime.strptime(
                        _clean_html_cell(
                            date_match.group(1)
                        ),
                        "%b-%y",
                    )
                )

                quarterly_growth = float(
                    cells[0]
                )

                annual_growth = float(
                    cells[1]
                )

            except (ValueError, TypeError):
                continue

            observations.append(
                {
                    "date": observation_date,
                    "quarterly_growth": (
                        quarterly_growth
                    ),
                    "annual_growth": (
                        annual_growth
                    ),
                }
            )

        if not observations:
            raise ValueError(
                "No valid ABS real GDP "
                "observations found."
            )

        latest = max(
            observations,
            key=lambda item: item["date"],
        )

        quarter = (
            (latest["date"].month - 1)
            // 3
            + 1
        )

        result = {
            "name": "Real GDP Growth",
            "value": round(
                latest["quarterly_growth"],
                2,
            ),
            "annual_growth": round(
                latest["annual_growth"],
                2,
            ),
            "unit": "percent",
            "frequency": "quarterly",
            "observation_date": (
                f"{latest['date'].year}-Q"
                f"{quarter}"
            ),
            "year": latest["date"].year,
            "quarter": quarter,
            "growth_type": (
                "Quarter-on-Quarter"
            ),
            "measure": (
                "Chain Volume Measures"
            ),
            "adjustment": (
                "Seasonally Adjusted"
            ),
            "geography": "Australia",
            "source": (
                "Australian Bureau of Statistics"
            ),
            "resource_id": (
                "Australian National Accounts: "
                "National Income, Expenditure "
                "and Product"
            ),
            "is_fallback": False,
            "is_cached": False,
        }

        save_macro_cache(
            "AU",
            "gdp_growth",
            result,
        )

        return result

    except Exception as error:
        print(
            "ABS GDP request failed: "
            f"{error}"
        )

        cached = get_macro_cache(
            "AU",
            "gdp_growth",
        )

        if cached:
            cached["is_fallback"] = False
            return cached

        return None

# ======================================================
# Australia Macro Snapshot
# ======================================================

def fetch_australia_macro_snapshot():
    """
    Fetch Australia's latest macroeconomic snapshot.

    Each indicator independently uses its official
    source and cached official-data fallback.
    """

    return {
        "country": "Australia",
        "market_code": "AU",

        "inflation": (
            fetch_australia_inflation()
        ),

        "policy_rate": (
            fetch_australia_policy_rate()
        ),

        "gdp_growth": (
            fetch_australia_gdp_growth()
        ),

        "unemployment": (
            fetch_australia_unemployment()
        ),

        "retrieved_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }

# ======================================================
# Automatic Country Macro Router
# ======================================================

def fetch_macro_snapshot_for_symbol(
    stock_symbol: str,
):
    """
    Detect the stock's market and fetch the appropriate
    country-specific macroeconomic snapshot.

    Examples:
        AAPL         -> United States
        RELIANCE.NS  -> India
        D05.SI       -> Singapore
        BHP.AX       -> Australia
    """

    from src.data.macro.country_config import (
        detect_market,
    )

    if not stock_symbol:
        raise ValueError(
            "Stock symbol is required."
        )

    normalized_symbol = (
        stock_symbol
        .strip()
        .upper()
    )

    market_code = detect_market(
        normalized_symbol
    )

    snapshot_fetchers = {
        "US": fetch_us_macro_snapshot,
        "IN": fetch_india_macro_snapshot,
        "SG": fetch_singapore_macro_snapshot,
        "AU": fetch_australia_macro_snapshot,
    }

    fetcher = snapshot_fetchers.get(
        market_code
    )

    if fetcher is None:
        raise ValueError(
            f"Unsupported market: {market_code}"
        )

    snapshot = fetcher()

    return {
        "stock_symbol": normalized_symbol,
        **snapshot,
    }