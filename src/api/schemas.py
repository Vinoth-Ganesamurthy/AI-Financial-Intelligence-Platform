"""
Pydantic response models for the Financial
Intelligence API.
"""

from typing import Any

from pydantic import BaseModel, Field


class ModuleScore(BaseModel):
    score: float = Field(
        description="Normalized module score from -1 to 1."
    )
    is_available: bool
    quality_factor: float = Field(
        ge=0,
        le=1,
    )
    weight: float = Field(
        ge=0,
        le=1,
    )
    weighted_contribution: float | None = None

    signal: str | None = None
    net_score: float | None = None

    article_count: int | None = None
    overall_sentiment: str | None = None

    risk_penalty: float | None = None
    classification: str | None = None

    metric_scores: dict[str, float] | None = None


class ModuleScores(BaseModel):
    fundamental: ModuleScore
    technical: ModuleScore
    sentiment: ModuleScore
    historical: ModuleScore
    sector_macro: ModuleScore


class FinancialIntelligenceResponse(BaseModel):
    stock_symbol: str
    company_name: str | None = None
    sector: str | None = None

    intelligence_score: float = Field(
        ge=-1,
        le=1,
        description=(
            "Combined intelligence score from -1 to 1."
        ),
    )
    classification: str
    summary: str

    coverage_ratio: float = Field(
        ge=0,
        le=1,
        description=(
            "Share of scoring-module weights that "
            "were available."
        ),
    )
    confidence_score: float = Field(
        ge=0,
        le=1,
        description=(
            "Data-quality and availability confidence."
        ),
    )

    module_scores: ModuleScores

    analysis: dict[str, Any]
    errors: dict[str, str]

    generated_at_utc: str
    disclaimer: str