# Research Plan

## Research Title

**An Explainable Multi-Factor Financial Intelligence Framework for Cross-Market Equity Analysis**

## 1. Research Objective

This research evaluates whether combining fundamental, technical, sentiment, historical-risk, and sector-aware macroeconomic indicators provides more reliable forward equity classifications than individual analysis modules, equal-weight scoring, and machine-learning baselines.

The study focuses on explainability, cross-market generalisation, reproducibility, and protection against data leakage.

## 2. Research Question

> Does an explainable multi-factor Financial Intelligence Score produce more accurate 20-trading-day forward equity classifications than individual analysis modules, an equal-weight model, and machine-learning baselines across multiple stock markets?

## 3. Hypotheses

### Primary hypothesis

**H1:** The combined Financial Intelligence Score will achieve a higher macro F1-score than every individual analysis module.

### Secondary hypotheses

* **H2:** The combined score will outperform an equal-weight baseline.
* **H3:** Higher Intelligence Scores will have a positive association with future 20-trading-day returns.
* **H4:** The model’s performance will remain reasonably consistent across India, the United States, Singapore, and Australia.
* **H5:** Sector-aware macroeconomic features will improve performance compared with a model that excludes macroeconomic information.

### Null hypothesis

**H0:** The combined Financial Intelligence Score provides no statistically significant improvement over the benchmark models.

## 4. Research Scope

| Item                  | Definition                                     |
| --------------------- | ---------------------------------------------- |
| Markets               | India, United States, Singapore, and Australia |
| Companies             | 40 companies—10 from each market               |
| Research period       | 1 January 2021 to 31 December 2025             |
| Observation frequency | Once every 20 trading days                     |
| Prediction horizon    | Next 20 trading days                           |
| Training period       | 2021–2023                                      |
| Validation period     | 2024                                           |
| Final test period     | 2025                                           |
| Primary task          | Three-class equity classification              |
| Secondary task        | Forward-return ranking                         |

The 2025 test dataset must remain untouched until model design, feature selection, thresholds, and hyperparameters have been finalised.

## 5. Company-Selection Rules

Companies will be selected using the following rules:

1. Ten companies will be selected from each market.
2. Selected companies must represent multiple economic sectors.
3. Each company should have sufficient price history between 2021 and 2025.
4. Companies should have adequate liquidity and reliable financial information.
5. The selection must not be based on future stock performance.
6. Selection criteria and excluded companies must be documented.
7. Delisted or missing-data cases must be reported instead of silently removed.

Where possible, company selection should use information available near the beginning of the research period to reduce survivorship bias.

## 6. Prediction Target

For stock \(i\) at observation date \(t\), the 20-trading-day forward return is:

$$
R_{i,t}^{20} = \frac{P_{i,t+20} - P_{i,t}}{P_{i,t}} \times 100
$$

where:

* \(P_{i,t}\) is the adjusted closing price on the observation date.
* \(P_{i,t+20}\) is the adjusted closing price 20 trading days later.

The target classes are:

| Forward return                 | Classification |
| ------------------------------ | -------------- |
| Greater than +2%               | Favourable     |
| Between −2% and +2%, inclusive | Neutral        |
| Less than −2%                  | Unfavourable   |

The fixed ±2% thresholds are the primary specification. Additional thresholds may be evaluated only as sensitivity analyses and must not replace the primary result after viewing test performance.

## 7. Input Modules

The research dataset will contain only information that was available on or before each observation date.

| Module          | Example information                                            |
| --------------- | -------------------------------------------------------------- |
| Fundamental     | Valuation, profitability, growth, leverage, and cash flow      |
| Technical       | Trend, momentum, moving averages, RSI, MACD, and volatility    |
| Sentiment       | Financial-news sentiment available before the observation date |
| Historical risk | Volatility, drawdown, beta, and return behaviour               |
| Macroeconomic   | Market- and sector-relevant economic indicators                |
| Sector context  | Sector-specific sensitivity and relative conditions            |

The final feature definitions, formulas, source, publication lag, transformation, and missing-value policy must be recorded in a separate data dictionary.

## 8. Models and Benchmarks

The following approaches will be evaluated:

1. Fundamental module only
2. Technical module only
3. Sentiment module only
4. Historical-risk module only
5. Macroeconomic module only
6. Current weighted Financial Intelligence Score
7. Equal-weight multi-factor score
8. Multi-factor score without macroeconomic features
9. Multinomial logistic-regression baseline
10. Tree-based machine-learning baseline

The current weighted model must be evaluated without changing its weights using the final test dataset.

## 9. Evaluation Metrics

### Primary metric

* Macro F1-score

Macro F1 is the primary metric because each target class should contribute equally even when the class distribution is imbalanced.

### Supporting classification metrics

* Balanced accuracy
* Precision by class
* Recall by class
* F1-score by class
* Confusion matrix
* Overall accuracy
* Class distribution

### Ranking and financial metrics

* Spearman rank correlation between score and future return
* Average forward return by score group
* Top-minus-bottom portfolio return
* Directional hit rate
* Annualised volatility
* Sharpe ratio
* Maximum drawdown
* Turnover and estimated transaction costs

Classification performance and economic performance will be reported separately.

## 10. Statistical Validation

Model comparisons will include:

* Confidence intervals obtained through block bootstrap sampling
* Paired comparisons using identical stock-date observations
* Statistical significance tests for differences between models
* Spearman correlation significance
* Market-level and sector-level performance analysis
* Robustness checks using alternative return thresholds
* Correction for multiple comparisons when necessary

Statistical significance alone will not be treated as proof of practical investment value. Effect sizes and confidence intervals will also be reported.

## 11. Data-Leakage Prevention

The following controls are mandatory:

1. Features at date \(t\) must use only information available on or before date \(t\).
2. Financial statements must be aligned using their publication or filing dates, not only their fiscal period-end dates.
3. News published after the observation timestamp must not enter sentiment features.
4. Macroeconomic values must respect their original release dates.
5. Technical indicators must use only historical prices through the observation date.
6. Missing values must be processed using rules learned from the training data.
7. Feature scaling must be fitted using training data only.
8. Hyperparameter tuning must use the validation period, never the test period.
9. Random train-test splitting must not be used for the primary experiment.
10. The final 2025 test results must be generated only after the research pipeline is frozen.

## 12. Experimental Design

The experiment will follow this sequence:

1. Define and freeze the company universe.
2. Create a complete data dictionary.
3. Collect raw historical data.
4. Preserve raw data without manual modification.
5. Align every feature to its actual availability date.
6. Generate observations at 20-trading-day intervals.
7. Calculate future-return targets.
8. Split the data chronologically.
9. Fit transformations and models using training data.
10. Select configurations using validation data.
11. Freeze the complete research pipeline.
12. Evaluate once on the final test dataset.
13. Run statistical and robustness analyses.
14. Generate tables, figures, and a research report.

## 13. Cross-Market Analysis

Results will be reported for:

* The complete dataset
* India
* United States
* Singapore
* Australia
* Individual sectors
* Different market conditions where sufficient data exists

Currency values may be normalised where necessary, but stock-return targets will be calculated in each stock’s local trading currency.

## 14. Reproducibility Requirements

The research must include:

* Fixed random seeds
* Version-controlled source code
* A dependency file with package versions
* Configuration-driven experiments
* Dataset metadata and retrieval dates
* Feature and target definitions
* Experiment logs
* Saved model parameters
* Git commit identifiers
* Reproducible tables and figures
* Clear instructions for rerunning the study

Large raw datasets, credentials, and generated model files should not be committed to the public repository.

## 15. Expected Research Outputs

The completed research project will produce:

* A validated cross-market historical dataset
* A formal data dictionary
* Reproducible experiment scripts
* Benchmark-comparison tables
* Confusion matrices
* Performance and calibration charts
* Market- and sector-level analyses
* Statistical significance results
* Ablation-study results
* A final research paper
* Updated technical documentation

## 16. Limitations to Report

The final study must discuss:

* Data-source availability and reliability
* Historical news coverage
* Point-in-time fundamental-data limitations
* Survivorship and selection bias
* Currency and market-calendar differences
* Class imbalance
* Transaction costs and liquidity
* API rate limits
* Model drift
* The difference between predictive association and causation

## 17. Ethical and Financial Disclaimer

This research is intended for educational and analytical purposes only. Its outputs do not constitute investment advice, financial recommendations, or guarantees of future performance.

Historical performance and statistically significant results do not ensure future profitability.
