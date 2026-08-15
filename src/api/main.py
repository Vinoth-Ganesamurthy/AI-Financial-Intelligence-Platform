"""
FastAPI entry point for the
AI Financial Intelligence Platform.
"""

import logging

from fastapi import FastAPI, HTTPException, Query

from src.analysis.intelligence.intelligence_engine import (
    build_financial_intelligence,
)


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


app = FastAPI(
    title="AI Financial Intelligence Platform",
    description=(
        "Multi-source financial intelligence API "
        "combining fundamental, technical, historical, "
        "sentiment, and macroeconomic analysis."
    ),
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "name": "AI Financial Intelligence Platform",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }


@app.get(
    "/api/v1/intelligence/{stock_symbol}"
)
def get_financial_intelligence(
    stock_symbol: str,
    news_limit: int = Query(
        default=5,
        ge=1,
        le=20,
        description=(
            "Maximum number of relevant news articles."
        ),
    ),
):
    """
    Generate complete financial intelligence for a
    Yahoo Finance stock symbol.
    """

    normalized_symbol = (
        stock_symbol.strip().upper()
    )

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Stock symbol is required.",
        )

    try:
        return build_financial_intelligence(
            stock_symbol=normalized_symbol,
            news_limit=news_limit,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception(
            "Financial intelligence analysis failed "
            "for %s",
            normalized_symbol,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Financial intelligence analysis "
                "failed. Check the server logs for "
                "details."
            ),
        ) from error