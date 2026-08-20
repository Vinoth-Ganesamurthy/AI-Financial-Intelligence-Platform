"""
Dynamic company lookup service.

Resolves a company name into a stock symbol.
"""

import os
import re

import requests
from dotenv import load_dotenv


load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

IGNORED_COMPANY_WORDS = {
    "and",
    "co",
    "company",
    "corp",
    "corporation",
    "group",
    "holding",
    "holdings",
    "inc",
    "incorporated",
    "limited",
    "ltd",
    "of",
    "plc",
    "the",
}


def _build_search_queries(company: str):
    """
    Create alternative Finnhub search queries.

    Example:
    Tata Consultancy Services
    -> Tata Consultancy Services
    -> TCS
    -> Tata
    """

    cleaned = " ".join(
        company.strip().split()
    )

    words = re.findall(
        r"[A-Za-z0-9]+",
        cleaned,
    )

    meaningful_words = [
        word
        for word in words
        if word.lower()
        not in IGNORED_COMPANY_WORDS
    ]

    candidates = [cleaned]

    simplified_name = " ".join(
        meaningful_words
    )

    if simplified_name:
        candidates.append(
            simplified_name
        )

    if len(meaningful_words) > 1:
        acronym = "".join(
            word[0]
            for word in meaningful_words
        )

        if len(acronym) >= 2:
            candidates.append(acronym)

    if meaningful_words:
        candidates.append(
            meaningful_words[0]
        )

    unique_queries = []
    seen = set()

    for candidate in candidates:
        key = candidate.upper()

        if candidate and key not in seen:
            seen.add(key)
            unique_queries.append(candidate)

    return unique_queries


def _select_symbol(
    query: str,
    results: list,
):
    """
    Select the most appropriate supported symbol.
    """

    preferred_suffixes = [
        ".NS",
        ".SI",
        ".AX",
    ]

    for suffix in preferred_suffixes:
        for result in results:
            symbol = (
                result.get("symbol", "")
                .strip()
                .upper()
            )

            if symbol.endswith(suffix):
                return symbol

    query_upper = query.upper()

    for result in results:
        symbol = (
            result.get("symbol", "")
            .strip()
            .upper()
        )

        display_symbol = (
            result.get(
                "displaySymbol",
                "",
            )
            .strip()
            .upper()
        )

        if (
            symbol == query_upper
            or display_symbol == query_upper
        ):
            return symbol

    for result in results:
        symbol = (
            result.get("symbol", "")
            .strip()
            .upper()
        )

        if symbol:
            return symbol

    return None


def get_stock_symbol(company: str):
    """
    Resolve a company name to a stock symbol.

    Multi-word names are retried using a cleaned
    name, acronym, and first meaningful word.
    """

    if not company or not company.strip():
        return None

    if not FINNHUB_API_KEY:
        print("FINNHUB_API_KEY is missing.")
        return None

    url = "https://finnhub.io/api/v1/search"

    last_error = None

    for query in _build_search_queries(
        company
    ):
        params = {
            "q": query,
            "token": FINNHUB_API_KEY,
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=10,
            )

        except requests.RequestException as error:
            last_error = str(error)
            continue

        if response.status_code != 200:
            last_error = (
                f"HTTP {response.status_code}"
            )
            continue

        data = response.json()
        results = data.get(
            "result",
            [],
        )

        if not results:
            continue

        symbol = _select_symbol(
            query,
            results,
        )

        if symbol:
            return symbol

    if last_error:
        print(
            "Company lookup failed: "
            f"{last_error}"
        )

    return None