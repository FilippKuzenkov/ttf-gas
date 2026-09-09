# Data sources

This file documents where the raw data comes from. It's written before any cleaning or analysis code, so anyone can reproduce the pull from scratch. If a source ever changes, add a new dated note below instead of editing the old description.

## TTF gas price (EUR/MWh)

**Source:** ACER (Agency for the Cooperation of Energy Regulators). The data itself originally comes from ICIS; ACER just republishes it.

**How to get it:**
1. Go to the ACER page: [Key developments in European gas wholesale markets (winter 2025-2026)](https://www.acer.europa.eu/key-developments-european-gas-wholesale-markets-winter-2025-2026)
2. Scroll down to "Additional information" and click "Access the underlying datasets"
3. Find "TTF price (EUR/MWh)" in the list and click it
4. Click "Download whole data" and export as CSV

**What's in the file:** one row per day, columns are `Date` (DD.MM.YYYY) and `Price, EUR/MWh`. Covers 01.01.2021 to 08.04.2026 — 1,924 rows.

## German day-ahead electricity price (EUR/MWh)

**Source:** SMARD, the official electricity market data platform run by Germany's Federal Network Agency (Bundesnetzagentur). We're using series 4169, filtered to Germany.

**How to get it:** run `scripts/pull_smard.py`. It calls SMARD's public JSON endpoint and saves a clean CSV.

A couple of things worth knowing if you ever touch that script:

- The URL needs a specific timestamp in it, and that timestamp isn't a real date — it's just an ID for a whole year's worth of data. You can't guess one, you have to ask SMARD's index endpoint which ones exist. The script already does this.
- The timestamps SMARD gives you are in UTC, but they're meant to represent midnight in Germany, and Germany's clock offset from UTC changes twice a year (daylight saving). If you're not careful, converting straight from UTC can quietly put a day on the wrong date — the Jan 1 reading for a whole year kept disappearing until this was fixed. The script converts to German local time first, then reads off the date, which fixes it.

**File:** `data/raw/smard_electricity_de_2021_2026.csv`

**What's in it:** one row per day, columns are `date` (YYYY-MM-DD) and `price_eur_mwh`. Covers 2021-01-01 to 2026-04-08 — 1,924 rows, same range and same count as the gas data above.

## Switched the electricity data to hourly resolution (2026-09-09)

The daily pull above (1,924 rows) turned out to be too small and too flat for a real portfolio project — a good rule of thumb from a data-analyst framework I checked this against is at least 50,000 rows, plus real categories to slice the data by (not just one row per day with nothing else to break it down by). SMARD actually publishes this same series at hourly resolution too, not just daily, so I switched to that instead.

`scripts/pull_smard.py` now pulls hourly prices instead of daily ones. That gets us to roughly 46,000 rows on its own, and — more usefully — gives us a real hour-of-day column to work with (is gas price a better predictor of electricity price during peak hours than overnight, for instance), which daily data just can't show.

**File:** `data/raw/smard_electricity_de_2021_2026_hourly.csv` — columns are `timestamp_local` (includes the hour) and `price_eur_mwh`. The old daily file and column layout above are kept as-is for reference; this hourly pull replaces it as the one actually used going forward.

**Confirmed 2026-09-09:** re-ran the script, got 46,175 rows — right where the ~46K estimate said it should land.

## One thing still to figure out before joining them

Gas price stays daily — one row per calendar day, no hourly gas data exists at this source. So the join to the new hourly electricity data will be a "broadcast" join: each day's single gas price gets repeated across all 24 (or fewer, if a DST-transition day) of that day's electricity rows, rather than matching row-for-row.

## Validation — 3-date spot check against independent sources (2026-09-09)

Picked three dates spread across the whole range and checked both series against a source that isn't SMARD or ACER/ICIS.

**Electricity**, checked against [energy-charts.info](https://energy-charts.info) (Fraunhofer ISE — an independent public source, not SMARD republished), same hour, same timezone:

| Date | Hour (local) | Our value | energy-charts.info | Match |
|---|---|---|---|---|
| 2021-03-15 | 12:00 | 47.98 | 47.98 | exact |
| 2022-08-15 | 12:00 | 402.31 | 402.31 | exact |
| 2025-05-12 | 12:00 | -25.00 | -25.00 | exact (yes, negative — real, midday solar oversupply, not an error) |

All three matched exactly. Real bonus finding: the 2025-05-12 negative price is a genuine, well-documented German market phenomenon (excess renewable output pushing day-ahead prices below zero at midday) — worth a line in the write-up as an example of realistic data messiness, not something to clean away.

**Gas**, checked against Yahoo Finance's `TTF=F` (ICE Dutch TTF front-month futures, delayed close):

| Date | Our value (ACER/ICIS) | Yahoo TTF=F close | Difference |
|---|---|---|---|
| 2021-03-15 | 18.40 | 17.93 | 2.6% |
| 2022-08-15 | 221.00 | 220.11 | 0.4% |
| 2025-05-12 | 35.31 | 35.39 | 0.2% |

Close but not identical, which is the expected result, not a red flag: Yahoo's number is a front-month **futures** close, ours is ICIS's own **day-ahead/spot** assessment — two related but genuinely different price series. A small, consistent gap confirms the data is real and correctly dated; an exact match would actually have been suspicious. This is the same futures-vs-spot distinction `ship-1-2-plan.md`'s own limitations section already names.

## Weekend gas prices — resolved, not just flagged (2026-09-09)

Checked 4 separate weekends spread across 2021, 2022, 2023, and 2025 (Friday/Saturday/Sunday values side by side). Every single time, Saturday and Sunday exactly repeat Friday's price, then Monday changes:

| Fri | Sat | Sun | Mon |
|---|---|---|---|
| 18.60 | 18.60 | 18.60 | 18.40 |
| 200.51 | 200.51 | 200.51 | 221.00 |
| 32.01 | 32.01 | 32.01 | 30.11 |
| 34.34 | 34.34 | 34.34 | 35.31 |

Confirmed, not suspected: TTF's weekend rows are a carried-forward Friday close, not real weekend settlement prices — gas markets genuinely don't trade on weekends. This explains why the daily gas and electricity files matched row-for-row (1,924 each) despite electricity pricing every single day. It's a real, documented limitation for the write-up (CLEAN framework: solvable? no — but it's a known, low-magnitude artifact of the source, not a data-quality bug), and it doesn't block the broadcast join: weekend electricity hours will correctly carry Friday's gas price, which is honestly the right behavior anyway, since Friday's close is the last real price the market had.
