"""
FastAPI entry point for the
AI Financial Intelligence Platform.
"""

import logging
import os
from fastapi import FastAPI, HTTPException, Query

from src.analysis.intelligence.intelligence_engine import (
    build_financial_intelligence,
)
from src.api.schemas import (
    FinancialIntelligenceResponse,
)
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

LOCAL_FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

configured_frontend_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]

ALLOWED_FRONTEND_ORIGINS = list(
    dict.fromkeys(
        LOCAL_FRONTEND_ORIGINS
        + configured_frontend_origins
    )
)

app = FastAPI(
    title="AI Financial Intelligence Platform",
    description=(
        "Multi-source financial intelligence API "
        "combining fundamental, technical, historical, "
        "sentiment, and macroeconomic analysis."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    "/api/v1/intelligence/{stock_symbol}",
    response_model=FinancialIntelligenceResponse,
    summary="Generate financial intelligence",
    description=(
        "Combines historical, technical, fundamental, "
        "sentiment, and sector-adjusted macroeconomic "
        "analysis for a stock symbol."
    ),
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