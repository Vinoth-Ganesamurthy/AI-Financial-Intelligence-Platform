# Research Scope Amendment

Date: 2026-10-03

## Final research scope

Cross-Market Equity Classification Using Price Indicators,
with US Fundamental and Macroeconomic Extensions.

1. Compare price-based rules and machine-learning baselines
   across 40 selected companies in four markets.
2. Compare price-only, price-plus-fundamentals, and
   price-plus-fundamentals-plus-macro models for 10 US companies.
3. Use 2021-2023 for training, 2024 for validation, and
   2025 for final holdout evaluation.

## Reason for amendment

The current NewsAPI plan does not provide the historical articles
required for the study. Point-in-time non-US fundamental and macro
coverage has not been established. These components are deferred.

This amendment follows inspection of 2024 validation results.
It is not an original pre-registration. The 2025 holdout prediction
results have not been evaluated.

## Claims and limitations

- The complete five-module production framework is not validated.
- Historical sentiment is excluded, not treated as neutral.
- US enrichment results cannot be generalized to other markets.
- The selected company universe may introduce survivorship bias.
- Classification performance does not establish trading profitability.
- Mixed or negative findings will be reported.

## Next step

Freeze model settings, feature sets, evaluation procedures, and
uncertainty methods in a separate protocol before running the holdout.
No further model tuning will use 2025 prediction results.
