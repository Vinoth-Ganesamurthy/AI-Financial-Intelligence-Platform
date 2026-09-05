"""
Frozen configuration for the historical research pipeline.

Changing these values after viewing final test results
would invalidate the pre-registered experiment.
"""

from datetime import date


DATASET_VERSION = "1.0.0"
RANDOM_SEED = 42

EXPECTED_MARKETS = (
    "India",
    "United States",
    "Singapore",
    "Australia",
)

COMPANIES_PER_MARKET = 10
EXPECTED_COMPANY_COUNT = 40

# Extra history is required before the first research
# observation for two-year risk calculations.
PRICE_DOWNLOAD_START = date(2019, 1, 1)

# The download end is exclusive and extends beyond the
# study period so late-2025 observations receive their
# complete 20-trading-day forward targets.
PRICE_DOWNLOAD_END = date(2026, 3, 1)

RESEARCH_START = date(2021, 1, 1)
RESEARCH_END = date(2025, 12, 31)

TRAINING_END = date(2023, 12, 31)
VALIDATION_START = date(2024, 1, 1)
VALIDATION_END = date(2024, 12, 31)
TEST_START = date(2025, 1, 1)
TEST_END = date(2025, 12, 31)

OBSERVATION_STEP_TRADING_DAYS = 20
TARGET_HORIZON_TRADING_DAYS = 20

FAVOURABLE_RETURN_THRESHOLD = 0.02
UNFAVOURABLE_RETURN_THRESHOLD = -0.02

MINIMUM_TECHNICAL_HISTORY = 200
MINIMUM_HISTORICAL_HISTORY = 252
TRAILING_RISK_WINDOW = 504

NEWS_LOOKBACK_CALENDAR_DAYS = 30
MAXIMUM_NEWS_ARTICLES = 5
MINIMUM_NEWS_RELEVANCE_SCORE = 8