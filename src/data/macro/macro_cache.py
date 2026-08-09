"""
Cache utilities for macroeconomic data.

Stores the latest successful official macro observations so the
application can continue operating when an external data source
is temporarily unavailable.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]

CACHE_DIR = BASE_DIR / "data" / "cache"
CACHE_FILE = CACHE_DIR / "macro_cache.json"


def _load_cache():
    """Load the complete macro cache."""

    if not CACHE_FILE.exists():
        return {}

    try:
        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return {}


def _save_cache(cache):
    """Write the complete macro cache."""

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            cache,
            file,
            indent=4,
        )


def save_macro_cache(
    country_code,
    indicator,
    data,
):
    """
    Save a successful macro observation.
    """

    if not data:
        return

    cache = _load_cache()

    country_cache = cache.setdefault(
        country_code,
        {},
    )

    country_cache[indicator] = {
        "data": data,
        "cached_at_utc": (
            datetime.now(timezone.utc)
            .isoformat()
        ),
    }

    _save_cache(cache)


def get_macro_cache(
    country_code,
    indicator,
):
    """
    Retrieve a cached macro observation.

    Cached observations retain their original
    observation date and source.
    """

    cache = _load_cache()

    cached = (
        cache
        .get(country_code, {})
        .get(indicator)
    )

    if not cached:
        return None

    result = dict(
        cached.get("data", {})
    )

    if not result:
        return None

    result["is_cached"] = True
    result["cached_at_utc"] = (
        cached.get("cached_at_utc")
    )

    return result