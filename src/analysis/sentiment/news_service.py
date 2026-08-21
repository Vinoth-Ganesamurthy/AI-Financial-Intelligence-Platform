"""
Financial News Service

Fetches recent company-related news using NewsAPI,
scores relevance, removes duplicates, and filters
generic list-style articles.
"""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

NEWS_API_RETRY_DELAYS = (
    0,
    1,
    3,
)

NEWS_API_RETRY_STATUSES = {
    429,
    500,
    502,
    503,
    504,
}


def _request_newsapi(
    url,
    params,
):
    """
    Request NewsAPI with retries for temporary
    connection and server failures.
    """

    last_error = None
    last_response = None

    for delay in NEWS_API_RETRY_DELAYS:
        if delay:
            time.sleep(delay)

        try:
            response = requests.get(
                url,
                params=params,
                timeout=20,
            )

        except requests.RequestException as error:
            last_error = error
            continue

        last_response = response

        if response.status_code == 200:
            return response

        if (
            response.status_code
            not in NEWS_API_RETRY_STATUSES
        ):
            break

    if last_response is not None:
        raise RuntimeError(
            "NewsAPI request failed after retries: "
            f"HTTP {last_response.status_code}"
        )

    error_name = (
        type(last_error).__name__
        if last_error
        else "UnknownError"
    )

    raise RuntimeError(
        "NewsAPI connection failed after "
        f"{len(NEWS_API_RETRY_DELAYS)} attempts "
        f"({error_name})."
    )

# ======================================================
# Company Search Names
# ======================================================

COMPANY_SEARCH_NAMES = {
    "TSLA": "Tesla",
    "NVDA": "NVIDIA",
    "RELIANCE.NS": "Reliance Industries",
    "INFY.NS": "Infosys",
    "D05.SI": "DBS Group",
    "CBA.AX": "Commonwealth Bank",
    "S63.SI": "ST Engineering",
}


# ======================================================
# Company Matching Terms
# ======================================================

COMPANY_TERMS = {
    "TSLA": [
        "tesla",
        "tsla",
    ],
    "NVDA": [
        "nvidia",
        "nvda",
    ],
    "RELIANCE.NS": [
        "reliance industries",
        "reliance retail",
        "reliance jio",
        "ril",
    ],
    "INFY.NS": [
        "infosys",
        "infy",
    ],
    "D05.SI": [
        "dbs group",
        "dbs bank",
    ],
    "CBA.AX": [
        "commonwealth bank",
        "commonwealth bank of australia",
        "cba",
    ],
    "S63.SI": [
        "st engineering",
        "singapore technologies engineering",
    ],
}


# ======================================================
# Helpers
# ======================================================

def get_company_search_name(
    symbol: str,
    company_name: str | None = None,
):
    """
    Return the preferred company name for NewsAPI search.
    """

    if symbol in COMPANY_SEARCH_NAMES:
        return COMPANY_SEARCH_NAMES[symbol]

    if company_name:
        return company_name.strip()

    return symbol


def get_company_terms(
    symbol: str,
    company_name: str | None = None,
):
    """
    Return clean matching terms used for relevance scoring.
    """

    if symbol in COMPANY_TERMS:
        return COMPANY_TERMS[symbol]

    if company_name:
        return [company_name.strip().lower()]

    return [symbol.lower()]


def is_low_quality_headline(title: str):
    """
    Reject generic list-style or broad market articles.
    """

    title = title.lower()

    blocked_phrases = [
        "stocks to watch",
        "stocks in focus",
        "shares to watch",
        "day trading guide",
        "market wrap",
        "top gainers",
        "top losers",
        "stock market today",
        "best stocks",
        "top stocks",
    ]

    return any(
        phrase in title
        for phrase in blocked_phrases
    )


def calculate_relevance_score(
    article: dict,
    terms: list[str],
):
    """
    Score article relevance.

    Headline match    = strongest
    Description match = medium
    Content match     = weak fallback
    """

    title = (
        article.get("title") or ""
    ).lower()

    description = (
        article.get("description") or ""
    ).lower()

    content = (
        article.get("content") or ""
    ).lower()

    score = 0

    for term in terms:
        term = term.lower()

        if term in title:
            score += 10

        if term in description:
            score += 4

        if term in content:
            score += 1

    return score


# ======================================================
# Main News Function
# ======================================================

def fetch_company_news(
    symbol: str,
    company_name: str | None = None,
    limit: int = 10,
):
    """
    Fetch recent relevant company news.

    Returns up to `limit` high-quality,
    deduplicated articles.
    """

    if not NEWS_API_KEY:
        raise ValueError(
            "NEWS_API_KEY is missing."
        )

    search_name = get_company_search_name(
        symbol,
        company_name,
    )

    terms = get_company_terms(
        symbol,
        company_name,
    )

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": f'"{search_name}"',
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 100,
        "apiKey": NEWS_API_KEY,
    }

    response = _request_newsapi(
        url=url,
        params=params,
    )

    payload = response.json()

    if payload.get("status") != "ok":
        raise RuntimeError(
            payload.get(
                "message",
                "NewsAPI returned an error.",
            )
        )

    articles = payload.get(
        "articles",
        []
    )

    scored_articles = []

    for article in articles:

        title = (
            article.get("title") or ""
        ).strip()

        if not title:
            continue

        if is_low_quality_headline(title):
            continue

        score = calculate_relevance_score(
            article,
            terms,
        )

        # Require a reasonably strong match.
        # Usually this means company in headline
        # or a combination of description/content matches.
        if score < 8:
            continue

        scored_articles.append(
            (
                score,
                article,
            )
        )

    # Higher relevance first
    scored_articles.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    results = []

    seen_titles = set()
    seen_urls = set()

    for score, article in scored_articles:

        title = (
            article.get("title") or ""
        ).strip()

        url_value = (
            article.get("url") or ""
        ).strip()

        title_key = title.lower()

        if not url_value:
            continue

        if title_key in seen_titles:
            continue

        if url_value in seen_urls:
            continue

        seen_titles.add(title_key)
        seen_urls.add(url_value)

        results.append(
            {
                "headline": title,
                "description": (
                    article.get("description")
                    or ""
                ).strip(),
                "source": (
                    article
                    .get("source", {})
                    .get("name")
                ),
                "published_at": article.get(
                    "publishedAt"
                ),
                "url": url_value,
                "relevance_score": score,
            }
        )

        if len(results) >= limit:
            break

    return results