# Final Holdout Evaluation Protocol

Frozen: 2026-10-03, before evaluating 2025 prediction performance.

## Data and training

- Training: eligible 2021-2023 observations.
- Validation: eligible 2024 observations, already inspected.
- Final holdout: eligible 2025 observations.
- Fit models, imputers, and scalers on training rows only.
- Do not refit on validation rows for this evaluation.
- Use the existing eligibility rules and 20-trading-day targets.
- Preserve all frozen features, model settings, and seed 42.

## Experiment A: Four-market price study

Evaluate the six existing experiment-06 baselines:
majority class, technical only, historical only, equal-weight price,
logistic regression, and random forest.

The ML models remain pooled across the four markets.
Report overall and per-market performance.
Random forest is the validation-selected ML candidate.

## Experiment B: US feature comparison

Evaluate the seven existing experiment-10 baselines:
majority class, and logistic regression/random forest with each of:
price only; price plus fundamentals; price plus fundamentals plus macro.

Use identical eligible US holdout observations for every model.
Random forest with price plus fundamentals is the
validation-selected candidate. Report all comparisons regardless
of whether additional features help.

## Metrics

- Primary: macro-F1 over favourable, neutral, and unfavourable.
- Secondary: balanced accuracy, accuracy, and prediction coverage.
- Report class counts and confusion matrices.
- Retain neutral fallback predictions for unavailable rule scores,
  while reporting their actual input coverage.

## Uncertainty and comparisons

Use 2,000 paired bootstrap replicates with seed 42.
Resample contiguous blocks of three observation rounds.
A round is each company's chronological observation ordinal.
Keep all companies together within each sampled round block
to retain cross-company dependence approximately.

Report percentile 95% intervals for macro-F1 and these differences:
- Pooled price random forest minus majority class.
- US random forest with fundamentals minus US price random forest.
- US random forest with fundamentals and macro minus
  US random forest with fundamentals.

The bootstrap is approximate: market calendars differ and the
holdout has few rounds. Intervals are descriptive, not proof of
generalization. Do not treat company rows as independent samples.

## Reporting

- Do not tune after inspecting holdout results.
- Report unfavorable findings and limitations.
- No trading-profitability claim or full-platform validation claim.
- Record input and script hashes, package versions, and row counts.
- If an implementation defect is found, document the correction
  and any rerun; do not describe the rerun as an untouched holdout.
