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

## One thing still to figure out before joining them

Both files have exactly 1,924 rows covering the same dates, which is a little suspicious — gas markets are usually closed on weekends, so I'd have expected fewer rows there than for electricity, which has a price every single day. Worth checking whether the gas file actually has real weekend values or just repeats Friday's price, before deciding how to join the two datasets.
