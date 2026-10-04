# Reproducing the Research

## Scope

This study evaluates four-market price baselines and US fundamental
and macroeconomic extensions.

Read `SCOPE_AMENDMENT.md`, `FINAL_EVALUATION_PROTOCOL.md`, and
`RESEARCH_REPORT.md` before interpreting the outputs.

Historical sentiment and the complete five-module production framework
were not validated.

## Environment

From the repository root, activate the project's Python environment.
Install the main dependencies and the plotting dependency:

```powershell
python -m pip install -r requirements.txt
python -m pip install -r research/requirements.txt
```

Recorded research versions include:

- scikit-learn 1.9.0
- pandas 3.0.5
- NumPy 2.5.1
- Matplotlib 3.11.2

Consult experiment metadata for the Python version and model settings.
These files do not constitute a complete dependency lockfile.

Run tests:

```powershell
python -m pytest -q
```

## Data and Credentials

Raw and processed datasets are excluded from Git. A fresh clone does
not contain the complete local research inputs.

The original local snapshots are required for exact reproduction.
Provider updates, revisions, and changed coverage may cause fresh
downloads to differ.

Historical US macro collection requires `FRED_API_KEY` in the local
environment or `.env`.

SEC collection uses `SEC_USER_AGENT`; consult the collector for its
required format. Do not commit credentials or print API keys.

NewsAPI is not required for the final scoped experiments.

## Pipeline Map

| Script | Purpose |
|---|---|
| `01_validate_universe.py` | Check historical price availability |
| `02_collect_prices.py` | Collect and cache research prices |
| `03_validate_prices.py` | Validate prices and record anomalies |
| `04_build_targets.py` | Build labels and split eligibility |
| `05_build_price_features.py` | Build price indicators and rule scores |
| `06_price_baselines.py` | Four-market validation benchmarks |
| `07_collect_sec_fundamentals.py` | Build historical US fundamentals |
| `08_us_fundamental_baselines.py` | US fundamentals validation comparison |
| `09_collect_fred_macro.py` | Collect historical US macro vintages |
| `10_us_macro_baselines.py` | US macro validation comparison |
| `11_evaluate_holdout.py` | Evaluate frozen models on 2025 |
| `12_analyze_holdout.py` | Analyze saved predictions and uncertainty |
| `13_make_figures.py` | Render saved results |

Scripts are under `research/experiments/`.
Run commands from the repository root.

## Recreate Analysis from Saved Predictions

This route does not retrain models or call external data services:

```powershell
python research/experiments/12_analyze_holdout.py
python research/experiments/13_make_figures.py
```

These commands overwrite their derived analysis and figure outputs.
Review the resulting Git diff. Preserve the original predictions and
evaluation manifest.

Analysis outputs are in `research/results/holdout_analysis/`.
Figures are in `research/figures/`, in PNG and PDF formats.

## Check the Holdout Runner Without Evaluation

```powershell
python research/experiments/11_evaluate_holdout.py
```

Without `--evaluate`, the runner checks preparation and syntax only.
It does not load datasets or generate holdout predictions.

## Reproducing the Frozen Holdout

The holdout has already been evaluated. Re-running it is a reproduction
attempt, not a new untouched test.

Required local inputs:

- `data/processed/research/price_features.csv`
- `data/interim/research/sec_annual_features.csv`
- `data/interim/research/us_macro_features.csv`

Compare their SHA-256 hashes against
`research/results/final_holdout/evaluation_manifest.json`.

Use a separate checkout and output location to reproduce results.
Do not delete or overwrite the preserved final-holdout artifacts.

The runner intentionally refuses to evaluate into a nonempty
`research/results/final_holdout/` directory.

The original evaluation command was:

```powershell
python research/experiments/11_evaluate_holdout.py --evaluate
```

## Frozen Design

- Training: eligible 2021–2023 observations.
- Validation: eligible 2024 observations.
- Holdout: eligible 2025 observations.
- Models and preprocessing fitted on training data only.
- No validation refit for holdout evaluation.
- No tuning after viewing holdout predictions.
- Seed: 42.
- Bootstrap: 2,000 paired replicates, three-round blocks.

Expected eligible counts:

| Experiment | Training | Validation | Holdout |
|---|---:|---:|---:|
| Four-market price | 1,480 | 470 | 490 |
| US extensions | 370 | 120 | 120 |

## Audit Artifacts

- Price and SEC collection manifests record source provenance.
- FRED caches record requested vintage dates and response hashes.
- Holdout manifests record inputs and executed scripts.
- Saved predictions permit metrics and bootstrap analysis without fitting.
- Analysis metadata records the bootstrap settings and input hashes.
- The original plan, scope amendment, and final protocol preserve
  the study's design history.

## Known Limitations

- Exact reproduction requires local snapshots absent from Git.
- The environment is documented but not fully locked.
- Historical data may change when downloaded again.
- Bootstrap intervals are approximate with only 12–13 holdout rounds.
- Price-source anomalies and partial accounting coverage remain.
- The study does not establish trading profitability.