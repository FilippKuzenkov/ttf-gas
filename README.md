# TTF Gas Price vs. German Day-Ahead Electricity Price

A two-part analysis on public energy-market data, framed as if delivered to an energy trading/risk desk: does TTF gas price track German day-ahead electricity price, and can it help predict it?

**What it answers:** whether gas price is a reliable leading indicator for electricity price exposure, under what conditions that signal should be trusted more or less, and whether a simple model using gas price can beat a naive "tomorrow looks like today" baseline. Full write-up, findings, and charts: [`ANALYSIS.md`](ANALYSIS.md).

**Interactive dashboard:** [TTF Gas Price as a Predictor of German Electricity Price — Tableau Public](https://public.tableau.com/app/profile/filipp.kuzenkov/viz/TTFGasPriceasaPredictorofGermanElectricityPrice/TTFGasPriceasaPredictorofGermanElectricityPrice?publish=yes). Headline finding (model beats a naive baseline by 8.5% MAE) with the underlying Model MAE/Baseline MAE numbers available on hover, so the number can be checked rather than taken on faith; an error-comparison chart with reference lines for both MAE values; and the single largest shared miss (Nov 25, 2025) annotated with its real cause on hover, not left as an unexplained outlier.

## Data

Two public sources, both daily-to-hourly resolution:

- **TTF gas price** (ACER/ICIS) — daily, EUR/MWh.
- **German day-ahead electricity price** (SMARD) — hourly, EUR/MWh.

Full acquisition steps, join strategy, and validation against independent references: [`DATA_SOURCES.md`](DATA_SOURCES.md).

## Repo layout

```
scripts/     ingestion, join, correlation and prediction analysis
data/        raw pulls and the joined clean dataset
charts/      exported analysis charts
excel/       pivot-table workbook, a second-tool cut of the joined data
dashboard/   Tableau workbook synthesizing both parts into one interactive view
```

## Reproducing this

Run the scripts in this order:

```
scripts/pull_smard.py
scripts/join_data.py
scripts/analyze_correlation.py
scripts/build_features.py
scripts/fit_model.py
scripts/evaluate_segments.py
scripts/plot_predictions.py
```

Each step's row counts and a hand-traced sample can be checked against the raw inputs, please see the scripts themselves.

## Tool stack

Python (pandas, scikit-learn) for the analysis; [`excel/ttf_electricity.xlsx`](excel/ttf_electricity.xlsx) is a second-tool addition - a pivot-table view of the same joined data, plus Issues Log and Insights Log tabs.
