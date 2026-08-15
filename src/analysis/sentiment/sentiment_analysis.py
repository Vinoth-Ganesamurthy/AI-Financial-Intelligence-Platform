"""
Sentiment Analysis Module

Converts financial news sentiment into
structured ML-ready features.
"""
from src.analysis.sentiment.news_service import fetch_company_news
from src.analysis.sentiment.model_predictor import predict_sentiment
from src.analysis.sentiment.news_service import fetch_company_news
from src.analysis.sentiment.model_predictor import predict_sentiment

def normalize_sentiment(
    sentiment: str,
):
    """
    Normalize model output.
    """

    value = (
        str(sentiment)
        .strip()
        .lower()
    )

    if value == "positive":
        return "positive"

    if value == "negative":
        return "negative"

    return "neutral"


def calculate_sentiment_features(
    classified_articles: list[dict],
):
    """
    Convert article-level sentiment results
    into aggregate sentiment features.
    """

    total = len(
        classified_articles
    )

    if total == 0:
        return {
            "article_count": 0,
            "positive_count": 0,
            "neutral_count": 0,
            "negative_count": 0,
            "positive_ratio": 0.0,
            "neutral_ratio": 0.0,
            "negative_ratio": 0.0,
            "sentiment_score": 0.0,
            "overall_sentiment": "NEUTRAL",
        }

    positive = 0
    neutral = 0
    negative = 0

    for article in classified_articles:

        sentiment = normalize_sentiment(
            article.get(
                "sentiment",
                "neutral",
            )
        )

        if sentiment == "positive":
            positive += 1

        elif sentiment == "negative":
            negative += 1

        else:
            neutral += 1

    positive_ratio = (
        positive / total
    )

    neutral_ratio = (
        neutral / total
    )

    negative_ratio = (
        negative / total
    )

    # Range:
    # -1.0 = entirely negative
    #  0.0 = balanced / neutral
    # +1.0 = entirely positive

    sentiment_score = (
        positive - negative
    ) / total

    if sentiment_score > 0.2:
        overall = "POSITIVE"

    elif sentiment_score < -0.2:
        overall = "NEGATIVE"

    else:
        overall = "NEUTRAL"

    return {
        "article_count": total,
        "positive_count": positive,
        "neutral_count": neutral,
        "negative_count": negative,

        "positive_ratio": round(
            positive_ratio,
            4,
        ),
        "neutral_ratio": round(
            neutral_ratio,
            4,
        ),
        "negative_ratio": round(
            negative_ratio,
            4,
        ),

        "sentiment_score": round(
            sentiment_score,
            4,
        ),

        "overall_sentiment": overall,
    }

def analyze_company_sentiment(
    symbol: str,
    company_name: str | None = None,
    limit: int = 10,
):
    """
    Fetch company news, classify each article,
    and return aggregate sentiment features.
    """

    articles = fetch_company_news(
        symbol=symbol,
        company_name=company_name,
        limit=limit,
    )

    classified_articles = []

    for article in articles:

        sentiment = predict_sentiment(
            article["headline"]
        )

        classified_articles.append(
            {
                **article,
                "sentiment": sentiment,
            }
        )

    features = calculate_sentiment_features(
        classified_articles
    )

    return {
        "features": features,
        "articles": classified_articles,
    }
