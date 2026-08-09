"""
Dynamic company lookup service.

Resolves a company name into a stock symbol.
"""

import os
import requests

from dotenv import load_dotenv

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")


def get_stock_symbol(company: str):
    """
    Resolve a company name to a stock symbol.

    Preference order:
    1. NSE
    2. Singapore
    3. Australia
    4. Exact symbol match
    5. First available result
    """

    if not company or not company.strip():
        return None

    if not FINNHUB_API_KEY:
        print("FINNHUB_API_KEY is missing.")
        return None

    company = company.strip()

    url = "https://finnhub.io/api/v1/search"

    params = {
        "q": company,
        "token": FINNHUB_API_KEY,
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10,
        )

        if response.status_code != 200:
            print(
                f"Company lookup failed: "
                f"HTTP {response.status_code}"
            )
            return None

        data = response.json()

    except requests.RequestException as error:
        print(
            f"Company lookup request failed: "
            f"{error}"
        )
        return None

    results = data.get("result", [])

    if not results:
        return None

    preferred_suffixes = [
        ".NS",
        ".SI",
        ".AX",
    ]

    for suffix in preferred_suffixes:
        for result in results:
            symbol = (
                result.get("symbol", "")
                .upper()
            )

            if symbol.endswith(suffix):
                return result.get("symbol")

    company_upper = company.upper()

    for result in results:
        symbol = (
            result.get("symbol", "")
            .upper()
        )

        if symbol == company_upper:
            return result.get("symbol")

    return results[0].get("symbol")