# Data sources

This file documents where the raw data comes from and how to reproduce the pull from scratch.

## TTF gas price (EUR/MWh)

**Source:** ACER (Agency for the Cooperation of Energy Regulators). The data itself originates with ICIS; ACER republishes it.

**How to get it:**
1. Go to the ACER page: [Key developments in European gas wholesale markets (winter 2025-2026)](https://www.acer.europa.eu/key-developments-european-gas-wholesale-markets-winter-2025-2026)
2. Scroll down to "Additional information" and click "Access the underlying datasets"
3. Find "TTF price (EUR/MWh)" in the list and click it
4. Click "Download whole data" and export as CSV

**What's in the file:** one row per day, columns are `Date` (DD.MM.YYYY) and `Price, EUR/MWh`. Covers 01.01.2021 to 08.04.2026 - 1,924 rows.

Gas has no intraday resolution at this source - one settlement price per calendar day, no hourly breakdown.

## German day-ahead electricity price (EUR/MWh)

**Source:** SMARD, the official electricity market data platform run by Germany's Federal Network Agency (Bundesnetzagentur). Series 4169, filtered to Germany, pulled at hourly resolution.

**How to get it:** run `scripts/pull_smard.py`. It calls SMARD's public JSON endpoint and saves a clean CSV.

A couple of things worth knowing if you touch that script:

- The URL needs a specific timestamp, and that timestamp isn't a real date - it's an ID for a whole week's worth of hourly data. You can't guess one, you have to ask SMARD's index endpoint which ones exist. The script does this.
- SMARD's timestamps are in UTC, but represent local German time, and Germany's UTC offset changes twice a year (daylight saving). Converting straight from UTC without accounting for this can silently shift readings onto the wrong date. The script converts to German local time first, then reads off the date and hour.

**File:** `data/raw/smard_electricity_de_2021_2026_hourly.csv` - columns are `timestamp_local` (includes the hour) and `price_eur_mwh`. Covers 2021-01-01 to 2026-04-08 - 46,175 rows.

## Join strategy

Gas price is daily; electricity price is hourly. The join is a broadcast join: each day's single gas price is repeated across all 24 (or fewer, on a DST-transition day) of that day's electricity rows, rather than matching row-for-row. This is the correct join given the data - gas genuinely has no finer-grained price to join against.

## Validation

Both series were checked against independent references before any analysis - not against each other, and not against a source that just republishes the same upstream data.

**Electricity**, checked against [energy-charts.info](https://energy-charts.info) (Fraunhofer ISE), same hour, same timezone:

| Date | Hour (local) | Our value | energy-charts.info | Match |
|---|---|---|---|---|
| 2021-03-15 | 12:00 | 47.98 | 47.98 | exact |
| 2022-08-15 | 12:00 | 402.31 | 402.31 | exact |
| 2025-05-12 | 12:00 | -25.00 | -25.00 | exact (real - midday solar oversupply, not an error) |

**Gas**, checked against Yahoo Finance's `TTF=F` (ICE Dutch TTF front-month futures):

| Date | Our value (ACER/ICIS) | Yahoo `TTF=F` close | Difference |
|---|---|---|---|
| 2021-03-15 | 18.40 | 17.93 | 2.6% |
| 2022-08-15 | 221.00 | 220.11 | 0.4% |
| 2025-05-12 | 35.31 | 35.39 | 0.2% |

## Weekend gas prices

TTF gas genuinely does not trade on weekends. Saturday and Sunday rows carry Friday's closing price forward rather than reflecting real weekend settlement - confirmed across four separate weekends spanning the full date range:

| Fri | Sat | Sun | Mon |
|---|---|---|---|
| 18.60 | 18.60 | 18.60 | 18.40 |
| 200.51 | 200.51 | 200.51 | 221.00 |
| 32.01 | 32.01 | 32.01 | 30.11 |
| 34.34 | 34.34 | 34.34 | 35.31 |

This is a known, documented source limitation, not a data-quality bug - the broadcast join correctly carries Friday's price into weekend electricity rows, since Friday's close is the last real price the market had. Its effect on weekday-vs-weekend analysis is checked directly in the main write-up (`README.md`).
