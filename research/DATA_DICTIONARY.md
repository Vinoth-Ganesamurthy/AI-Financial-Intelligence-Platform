# Research Data Dictionary

## 1. Purpose

This document defines the variables, calculations, sources, units, timing rules, missing-value behaviour, and scoring logic used in the cross-market Financial Intelligence research dataset.

All research implementations must follow these definitions. Any later change must be documented, justified, version-controlled, and made without examining the final 2025 test results.

## 2. Dataset Granularity

Each dataset row represents:

> One company observed on one predefined observation date.

Observations are generated once every 20 trading days for each company.

The prediction target is the company’s adjusted-price return over the following 20 trading days.

## 3. Identification and Time Fields

| Field                | Type      | Definition                                              |
| -------------------- | --------- | ------------------------------------------------------- |
| `market`             | Category  | India, United States, Singapore, or Australia           |
| `market_code`        | Category  | IN, US, SG, or AU                                       |
| `symbol`             | String    | Yahoo Finance-compatible stock symbol                   |
| `company`            | String    | Company name from the frozen research universe          |
| `research_sector`    | Category  | Standardised sector stored in `company_universe.csv`    |
| `platform_sector`    | Category  | Sector name mapped to the production scoring categories |
| `currency`           | Category  | Stock’s local trading currency                          |
| `observation_date`   | Date      | Date on which features are measured                     |
| `feature_cutoff_utc` | Timestamp | Latest timestamp allowed for any feature                |
| `target_date`        | Date      | Twentieth trading day following the observation date    |
| `split`              | Category  | `train`, `validation`, or `test`                        |
| `data_version`       | String    | Dataset-generation version                              |
| `generated_at_utc`   | Timestamp | Dataset-row generation time                             |

### Chronological split

| Split      | Period    | Permitted use                             |
| ---------- | --------- | ----------------------------------------- |
| Training   | 2021–2023 | Model fitting and transformation fitting  |
| Validation | 2024      | Model selection and hyperparameter tuning |
| Test       | 2025      | One-time final evaluation                 |

## 4. Price-Data Rules

Research price data must:

* Use adjusted prices to account for stock splits and dividends.
* Contain only records available on or before the observation date.
* Include sufficient warm-up history for 200- and 252-day calculations.
* Start no later than 1 January 2020 for observations beginning in 2021.
* Use each exchange’s actual trading calendar.
* Never forward-fill prices across non-trading days.

| Field    | Unit           | Definition             |
| -------- | -------------- | ---------------------- |
| `open`   | Local currency | Adjusted opening price |
| `high`   | Local currency | Adjusted daily high    |
| `low`    | Local currency | Adjusted daily low     |
| `close`  | Local currency | Adjusted closing price |
| `volume` | Shares         | Daily trading volume   |

Primary source: Yahoo Finance through `yfinance`.

## 5. Technical Features

Technical features are calculated using prices through the observation date only.

### Production indicators

| Field              | Unit or range  | Definition                                      |
| ------------------ | -------------- | ----------------------------------------------- |
| `current_price`    | Local currency | Latest adjusted close                           |
| `sma_20`           | Local currency | 20-day simple moving average                    |
| `sma_50`           | Local currency | 50-day simple moving average                    |
| `sma_200`          | Local currency | 200-day simple moving average                   |
| `ema_12`           | Local currency | 12-day exponential moving average               |
| `ema_26`           | Local currency | 26-day exponential moving average               |
| `rsi_14`           | 0–100          | 14-day Relative Strength Index                  |
| `macd`             | Local currency | EMA(12) minus EMA(26)                           |
| `macd_signal`      | Local currency | Nine-period EMA of MACD                         |
| `macd_histogram`   | Local currency | MACD minus MACD signal                          |
| `bollinger_upper`  | Local currency | SMA(20) plus two 20-day standard deviations     |
| `bollinger_middle` | Local currency | SMA(20)                                         |
| `bollinger_lower`  | Local currency | SMA(20) minus two 20-day standard deviations    |
| `atr_14`           | Local currency | 14-day average true range                       |
| `current_volume`   | Shares         | Volume on observation date                      |
| `volume_ma_20`     | Shares         | 20-day average volume                           |
| `relative_volume`  | Ratio          | Current volume divided by 20-day average volume |

### Scale-independent research features

These fields are used by machine-learning baselines so companies with different currencies and prices remain comparable.

| Field                | Definition                                      |
| -------------------- | ----------------------------------------------- |
| `price_to_sma_20`    | `current_price / sma_20 - 1`                    |
| `price_to_sma_50`    | `current_price / sma_50 - 1`                    |
| `price_to_sma_200`   | `current_price / sma_200 - 1`                   |
| `ema_spread`         | `ema_12 / ema_26 - 1`                           |
| `macd_pct`           | `macd / current_price × 100`                    |
| `macd_histogram_pct` | `macd_histogram / current_price × 100`          |
| `bollinger_position` | `(current_price - lower) / (upper - lower)`     |
| `atr_pct`            | `atr_14 / current_price × 100`                  |
| `relative_volume`    | Current volume divided by 20-day average volume |

## 6. Technical Rule-Based Score

Bullish and bearish points are calculated as follows:

| Rule                  | Bullish point          | Bearish point           |
| --------------------- | ---------------------- | ----------------------- |
| Price versus SMA(20)  | Price above SMA        | Price at or below SMA   |
| Price versus SMA(50)  | Price above SMA        | Price at or below SMA   |
| Price versus SMA(200) | Price above SMA        | Price at or below SMA   |
| RSI(14)               | RSI below 30           | RSI above 70            |
| MACD                  | MACD above signal      | MACD at or below signal |
| Bollinger position    | Price below lower band | Price above upper band  |

RSI between 30 and 70 produces no point. A price inside the Bollinger Bands produces no point.

$$
TechnicalNetScore = BullishPoints - BearishPoints
$$

| Field                      | Definition                                                     |
| -------------------------- | -------------------------------------------------------------- |
| `technical_bullish_points` | Total bullish-rule points                                      |
| `technical_bearish_points` | Total bearish-rule points                                      |
| `technical_net_score`      | Bullish points minus bearish points                            |
| `technical_signal`         | Bullish if score ≥ 2; bearish if score ≤ −2; otherwise neutral |
| `technical_module_score`   | Net score divided by 6 and clamped to [−1, 1]                  |
| `technical_quality_factor` | 1 when the net score is available; otherwise 0                 |

## 7. Historical Performance and Risk Features

The production platform uses a trailing two-year market-data window.

| Field                   | Unit           | Definition                                            |
| ----------------------- | -------------- | ----------------------------------------------------- |
| `return_5d`             | Percent        | Return over five trading days                         |
| `return_21d`            | Percent        | Return over 21 trading days                           |
| `return_63d`            | Percent        | Return over 63 trading days                           |
| `return_126d`           | Percent        | Return over 126 trading days                          |
| `return_252d`           | Percent        | Return over 252 trading days                          |
| `annualized_volatility` | Percent        | Standard deviation of daily returns × √252 × 100      |
| `maximum_drawdown`      | Percent        | Minimum decline from the running historical peak      |
| `period_high`           | Local currency | Highest adjusted high in the trailing window          |
| `period_low`            | Local currency | Lowest adjusted low in the trailing window            |
| `price_range_position`  | 0–1            | Position of current price between period low and high |

### Historical module score

| Return         | Weight | Normalisation scale |
| -------------- | -----: | ------------------: |
| 21-day return  |    20% |        Divide by 20 |
| 63-day return  |    30% |        Divide by 30 |
| 126-day return |    25% |        Divide by 40 |
| 252-day return |    25% |        Divide by 50 |

Every normalised return is clamped to [−1, 1]. Missing periods are excluded and the remaining weights are renormalised.

Risk penalties:

| Condition                       |                Penalty |
| ------------------------------- | ---------------------: |
| Annualised volatility above 50% |                  −0.10 |
| Annualised volatility above 75% | −0.20 instead of −0.10 |
| Maximum drawdown below −30%     |                  −0.10 |
| Maximum drawdown below −50%     | −0.20 instead of −0.10 |

| Field                       | Definition                                                    |
| --------------------------- | ------------------------------------------------------------- |
| `historical_module_score`   | Weighted return score plus risk penalties, clamped to [−1, 1] |
| `historical_risk_penalty`   | Sum of volatility and drawdown penalties                      |
| `historical_quality_factor` | Sum of available return weights                               |

## 8. Point-in-Time Fundamental Features

The live production function returns current fundamentals. It must not be called directly when generating historical research rows.

For research, every fundamental value must come from the most recent financial statement published on or before `feature_cutoff_utc`.

| Field                      | Unit           | Definition                                                                               |
| -------------------------- | -------------- | ---------------------------------------------------------------------------------------- |
| `statement_period_end`     | Date           | Fiscal period represented by the statement                                               |
| `statement_available_date` | Date           | Publication or filing date used for point-in-time alignment                              |
| `fundamental_source`       | Category       | Historical fundamental-data provider                                                     |
| `market_cap`               | Local currency | Observation-date price × latest available shares outstanding                             |
| `total_revenue`            | Local currency | Latest point-in-time trailing or annual revenue                                          |
| `trailing_pe`              | Ratio          | Market capitalisation divided by trailing net income                                     |
| `forward_pe`               | Ratio          | Historical analyst forward P/E, only when genuinely available as of the observation date |
| `price_to_book`            | Ratio          | Market capitalisation divided by stockholders’ equity                                    |
| `profit_margin`            | Percent        | Net income divided by revenue × 100                                                      |
| `return_on_equity`         | Percent        | Net income divided by stockholders’ equity × 100                                         |
| `return_on_assets`         | Percent        | Net income divided by total assets × 100                                                 |
| `revenue_growth`           | Percent        | Year-over-year revenue growth                                                            |
| `earnings_growth`          | Percent        | Year-over-year net-income or EPS growth                                                  |
| `debt_to_equity`           | Percent        | Total debt divided by stockholders’ equity × 100                                         |
| `free_cash_flow`           | Local currency | Operating cash flow minus capital expenditure                                            |
| `free_cash_flow_positive`  | Binary         | 1 when free cash flow is positive; otherwise 0                                           |

### Publication-lag rules

* Use the actual filing or publication date whenever available.
* Never use the fiscal period-end date as the availability date.
* If an annual filing date is unavailable, apply a conservative 120-calendar-day lag.
* If a quarterly filing date is unavailable, apply a conservative 60-calendar-day lag.
* Record whether a lag was estimated.
* Do not backward-fill a later statement into an earlier observation.

## 9. Fundamental Rule-Based Score

| Metric          | Condition                    | Score |
| --------------- | ---------------------------- | ----: |
| Profit margin   | ≥10%                         |  1.00 |
| Profit margin   | >0% and <10%                 |  0.50 |
| Profit margin   | ≤0%                          | −1.00 |
| ROE             | ≥15%                         |  1.00 |
| ROE             | 5% to <15%                   |  0.50 |
| ROE             | 0% to <5%                    |  0.00 |
| ROE             | <0%                          | −1.00 |
| Revenue growth  | ≥10%                         |  1.00 |
| Revenue growth  | >0% and <10%                 |  0.50 |
| Revenue growth  | >−10% and ≤0%                | −0.50 |
| Revenue growth  | ≤−10%                        | −1.00 |
| Earnings growth | Same rules as revenue growth |     — |
| Forward P/E     | >0 and ≤25                   |  1.00 |
| Forward P/E     | >25 and ≤40                  |  0.25 |
| Forward P/E     | >40                          | −0.50 |
| Forward P/E     | ≤0                           | −1.00 |
| Debt-to-equity  | ≤100%                        |  0.50 |
| Debt-to-equity  | >100% and ≤200%              |  0.00 |
| Debt-to-equity  | >200%                        | −0.50 |
| Free cash flow  | Positive                     |  1.00 |
| Free cash flow  | Zero or negative             | −1.00 |

The fundamental module score is the mean of available metric scores and is clamped to [−1, 1].

$$
FundamentalQuality = \min\left(\frac{AvailableMetricCount}{7}, 1\right)
$$

If historical forward P/E is unavailable, it remains missing and is excluded. It must not be replaced with the current forward P/E.

## 10. Sentiment Features

The production classifier uses:

* A saved TF-IDF vectorizer
* A trained sentiment classification model
* A saved label encoder
* Positive, neutral, and negative classes

The research collector must use only headlines published on or before the observation cutoff.

### Historical news window

* Lookback: Previous 30 calendar days
* Language: English
* Maximum selected articles: Five
* Ordering: Relevance first, then most recent
* Duplicate headlines and URLs removed
* Generic list-style market articles excluded
* Minimum relevance score: Eight

| Field               | Unit     | Definition                                          |
| ------------------- | -------- | --------------------------------------------------- |
| `article_count`     | Count    | Number of selected articles                         |
| `positive_count`    | Count    | Positive headlines                                  |
| `neutral_count`     | Count    | Neutral headlines                                   |
| `negative_count`    | Count    | Negative headlines                                  |
| `positive_ratio`    | 0–1      | Positive count divided by article count             |
| `neutral_ratio`     | 0–1      | Neutral count divided by article count              |
| `negative_ratio`    | 0–1      | Negative count divided by article count             |
| `sentiment_score`   | −1 to 1  | `(positive_count - negative_count) / article_count` |
| `sentiment_class`   | Category | Positive, neutral, or negative                      |
| `sentiment_source`  | String   | Historical news-data source                         |
| `news_window_start` | Date     | Beginning of the permitted news window              |
| `news_window_end`   | Date     | Observation-date cutoff                             |

Sentiment classification thresholds:

* Positive: score above 0.20
* Negative: score below −0.20
* Neutral: score from −0.20 through 0.20

$$
SentimentQuality = \min\left(\frac{ArticleCount}{5}, 1\right)
$$

If no valid articles are available, the sentiment module is unavailable. A zero score must not be treated as observed neutral sentiment when the article count is zero.

## 11. Macroeconomic Features

| Field                          | Unit    | Definition                                        |
| ------------------------------ | ------- | ------------------------------------------------- |
| `inflation_rate`               | Percent | Latest inflation value available by the cutoff    |
| `monetary_rate`                | Percent | Policy rate or documented market-rate proxy       |
| `gdp_growth_rate`              | Percent | Latest GDP growth value available by the cutoff   |
| `unemployment_rate`            | Percent | Latest unemployment value available by the cutoff |
| `monetary_rate_is_policy_rate` | Binary  | 1 for official policy rate; 0 for proxy           |
| `macro_observation_date`       | Date    | Period represented by the indicator               |
| `macro_publication_date`       | Date    | Date the value became publicly available          |
| `macro_source`                 | String  | Official or fallback provider                     |
| `macro_is_fallback`            | Binary  | 1 when a fallback source is used                  |
| `macro_is_cached`              | Binary  | 1 when a cached observation is used               |

Primary providers represented in the platform include:

* FRED for the United States
* RBI and MoSPI for India
* Singapore Department of Statistics and MAS for Singapore
* RBA and Australian Bureau of Statistics for Australia
* World Bank only as a documented fallback

### Point-in-time macro rule

For each observation, use the most recently published value whose publication date is on or before `feature_cutoff_utc`.

If an explicit release date is unavailable, apply a conservative publication lag:

| Frequency                   |       Default lag |
| --------------------------- | ----------------: |
| Monthly CPI or unemployment |  30 calendar days |
| Quarterly GDP               |  60 calendar days |
| Annual World Bank fallback  | 180 calendar days |
| Policy-rate decision        | Announcement date |

Revised values must not be treated as original point-in-time values when vintage data is unavailable. This limitation must be recorded in the research paper.

### General macro weights

| Component            | Weight |
| -------------------- | -----: |
| Inflation            |    30% |
| GDP growth           |    30% |
| Unemployment         |    20% |
| Monetary environment |    20% |

Raw macro scores are normalised as follows:

| Raw score | Normalised score |
| --------: | ---------------: |
|         2 |             1.00 |
|         1 |             1.00 |
|         0 |             0.00 |
|        −1 |            −0.50 |
|        −2 |            −1.00 |

## 12. Sector-Aware Macro Weights

| Platform sector        | Inflation | GDP | Unemployment | Monetary |
| ---------------------- | --------: | --: | -----------: | -------: |
| Technology             |       15% | 30% |          15% |      40% |
| Financial Services     |       15% | 30% |          20% |      35% |
| Energy                 |       10% | 45% |          15% |      30% |
| Basic Materials        |       15% | 45% |          15% |      25% |
| Consumer Cyclical      |       20% | 35% |          30% |      15% |
| Consumer Defensive     |       35% | 20% |          25% |      20% |
| Real Estate            |       15% | 20% |          15% |      50% |
| Utilities              |       20% | 15% |          15% |      50% |
| Healthcare             |       25% | 20% |          30% |      25% |
| Industrials            |       15% | 40% |          25% |      20% |
| Communication Services |       20% | 30% |          20% |      30% |
| Unmapped sector        |       25% | 25% |          25% |      25% |

| Field                         | Definition                                                    |
| ----------------------------- | ------------------------------------------------------------- |
| `sector_macro_score`          | Sector-weighted mean of available normalised macro components |
| `sector_macro_quality_factor` | General macro confidence score                                |
| `sector_macro_used_default`   | 1 when equal default weights are used                         |

## 13. Overall Financial Intelligence Score

### Module weights

| Module             | Weight |
| ------------------ | -----: |
| Fundamental        |    30% |
| Technical          |    20% |
| Sentiment          |    15% |
| Historical         |    15% |
| Sector-aware macro |    20% |

For the available module set \(A\):

$$
IntelligenceScore =
\frac{\sum_{m \in A} ModuleScore_m \times Weight_m}
{\sum_{m \in A} Weight_m}
$$

The score is clamped conceptually to the range [−1, 1].

| Field                         | Definition                                            |
| ----------------------------- | ----------------------------------------------------- |
| `intelligence_score`          | Weighted score after available-weight renormalisation |
| `coverage_ratio`              | Sum of weights belonging to available modules         |
| `confidence_score`            | Sum of module weight × module quality factor          |
| `intelligence_classification` | Production score classification                       |
| `available_module_count`      | Number of modules included in the score               |

### Intelligence classifications

| Score             | Classification      |
| ----------------- | ------------------- |
| ≥0.50             | Strongly favourable |
| ≥0.20 and <0.50   | Favourable          |
| >−0.20 and <0.20  | Neutral             |
| >−0.50 and ≤−0.20 | Cautious            |
| ≤−0.50            | Unfavourable        |

These classifications describe the model’s contemporaneous analysis. They are different from the future-return target classes.

## 14. Prediction Target

$$
ForwardReturn_{20} =
\left(\frac{AdjustedClose_{t+20}}{AdjustedClose_t} - 1\right)
\times 100
$$

| Field                | Definition                                          |
| -------------------- | --------------------------------------------------- |
| `forward_return_20d` | Adjusted-price return over the next 20 trading days |
| `target_class`       | Favourable, neutral, or unfavourable                |
| `target_available`   | 1 when the complete forward horizon exists          |

Target labels:

| Forward return             | Target class |
| -------------------------- | ------------ |
| Greater than +2%           | Favourable   |
| −2% through +2%, inclusive | Neutral      |
| Less than −2%              | Unfavourable |

Target fields must be generated only after all feature calculations are complete.

## 15. Missing-Value Rules

* Never replace unavailable information with future data.
* Never use backward filling.
* Do not automatically convert missing modules into neutral scores.
* Preserve explicit availability indicators.
* Production rule-based scores renormalise over available components.
* Machine-learning imputers must be fitted using training data only.
* Add missingness indicators for imputed machine-learning features.
* Report coverage by module, company, market, sector, and year.
* Rows with missing targets must be excluded from supervised evaluation.
* Any row-exclusion rule must be defined before final test evaluation.

## 16. Pre-Experiment Corrections

The following corrections must be implemented and unit-tested on the research branch before the scoring pipeline is frozen:

1. Standardise debt-to-equity as a percentage across all fundamental providers.
2. Treat non-positive forward P/E as −1.00 in the corrected research score.
3. Create an explicit mapping from research-sector names to platform-sector names.
4. Add `as_of_date` support through separate research collectors.
5. Prevent production “latest value” functions from being used in historical rows.
6. Add explicit publication-date and source metadata.
7. Remove duplicate sentiment imports without changing behaviour.
8. Preserve a legacy-score output when practical so corrected and original formulas can be compared transparently.

The corrected, pre-registered score will be the primary research specification. The legacy score will be reported only as a sensitivity comparison.

## 17. Reproducibility Metadata

Every generated dataset must record:

* Retrieval timestamp
* Source name
* Source record date
* Publication or availability date
* Fallback status
* Code version or Git commit
* Configuration version
* Random seed where applicable
* Row count
* Missing-value summary
* File hash

Raw source data must remain immutable after collection.
