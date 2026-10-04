"""Generate research observations and forward-return targets."""

import numpy as np
import pandas as pd

from src.research.config import (
    DATASET_VERSION,
    FAVOURABLE_RETURN_THRESHOLD,
    OBSERVATION_STEP_TRADING_DAYS,
    RESEARCH_END,
    RESEARCH_START,
    TARGET_HORIZON_TRADING_DAYS,
    TEST_START,
    TRAINING_END,
    UNFAVOURABLE_RETURN_THRESHOLD,
    VALIDATION_END,
    VALIDATION_START,
)


def classify_forward_return(return_decimal: float) -> str:
    """Classify a decimal return using the frozen thresholds."""
    if not np.isfinite(return_decimal):
        raise ValueError("Forward return must be finite.")

    # Tolerance prevents floating-point noise at exact boundaries.
    if (
        return_decimal > FAVOURABLE_RETURN_THRESHOLD
        and not np.isclose(
            return_decimal,
            FAVOURABLE_RETURN_THRESHOLD,
            rtol=0,
            atol=1e-12,
        )
    ):
        return "favourable"

    if (
        return_decimal < UNFAVOURABLE_RETURN_THRESHOLD
        and not np.isclose(
            return_decimal,
            UNFAVOURABLE_RETURN_THRESHOLD,
            rtol=0,
            atol=1e-12,
        )
    ):
        return "unfavourable"

    return "neutral"


def observation_split(observation_date: pd.Timestamp) -> str:
    """Assign a split by observation date."""
    day = observation_date.date()

    if RESEARCH_START <= day <= TRAINING_END:
        return "train"
    if VALIDATION_START <= day <= VALIDATION_END:
        return "validation"
    if TEST_START <= day <= RESEARCH_END:
        return "test"

    raise ValueError("Observation date is outside the research period.")


def build_targets(
    prices: pd.DataFrame,
    *,
    symbol: str,
    market: str,
) -> pd.DataFrame:
    """
    Sample every 20 trading rows from the first research date.

    Boundary-crossing training and validation labels are retained
    for auditing but marked ineligible for model fitting/evaluation.
    Test observations may finish their target horizon in early 2026.
    """
    if prices.empty or "Close" not in prices.columns:
        raise ValueError("Nonempty prices with a Close column are required.")

    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("Prices must have a DatetimeIndex.")

    if prices.index.tz is not None:
        raise ValueError("Price dates must be timezone-naive local dates.")

    if prices.index.hasnans:
        raise ValueError("Price dates contain missing values.")

    if (
        not prices.index.is_unique
        or not prices.index.is_monotonic_increasing
    ):
        raise ValueError("Price dates must be unique and sorted.")

    close = pd.to_numeric(prices["Close"], errors="coerce")

    if not np.isfinite(close.to_numpy()).all() or (close <= 0).any():
        raise ValueError("Closing prices must be finite and positive.")

    positions = np.flatnonzero(
        (prices.index >= pd.Timestamp(RESEARCH_START))
        & (prices.index <= pd.Timestamp(RESEARCH_END))
    )

    records = []

    for position in positions[::OBSERVATION_STEP_TRADING_DAYS]:
        observation_date = prices.index[position]
        split = observation_split(observation_date)
        target_position = position + TARGET_HORIZON_TRADING_DAYS

        target_date = pd.NaT
        forward_return = np.nan
        target_class = None
        eligible = False
        exclusion_reason = "incomplete_forward_horizon"

        if target_position < len(prices):
            target_date = prices.index[target_position]
            return_decimal = (
                float(close.iloc[target_position])
                / float(close.iloc[position])
                - 1
            )
            forward_return = return_decimal * 100
            target_class = classify_forward_return(return_decimal)

            crosses_boundary = (
                split == "train"
                and target_date.date() > TRAINING_END
            ) or (
                split == "validation"
                and target_date.date() > VALIDATION_END
            )

            eligible = not crosses_boundary
            exclusion_reason = (
                "target_crosses_split_boundary"
                if crosses_boundary
                else ""
            )

        records.append(
            {
                "dataset_version": DATASET_VERSION,
                "market": market,
                "symbol": symbol.strip().upper(),
                "observation_date": observation_date,
                "target_date": target_date,
                "split": split,
                "observation_close": float(close.iloc[position]),
                "forward_return_20d": forward_return,
                "target_class": target_class,
                "target_available": pd.notna(target_date),
                "eligible": eligible,
                "exclusion_reason": exclusion_reason,
            }
        )

    return pd.DataFrame(
        records,
        columns=[
            "dataset_version",
            "market",
            "symbol",
            "observation_date",
            "target_date",
            "split",
            "observation_close",
            "forward_return_20d",
            "target_class",
            "target_available",
            "eligible",
            "exclusion_reason",
        ],
    )