# Data sources

Committed before any pulling/cleaning code, per this project's own guardrail against the university-project failure mode (a silently swapped data source, an undetected bad aggregation). Any later change to either source is a dated append below, never a silent edit.

## TTF gas price (EUR/MWh)

- **Source:** ACER (Agency for the Cooperation of Energy Regulators), data item 1083, sourced from ICIS. ACER republishes ICIS's data — not ACER's own primary collection.
- **Access path (human, reproducible):** `acer.europa.eu/key-developments-european-gas-wholesale-markets-winter-2025-2026` → "Additional information" → "Access the underlying datasets" → CHEST category 70 list → "TTF price (EUR/MWh)" → "Download whole data" → CSV. **Do not bookmark or direct-link the data item page itself** (`aegis.acer.europa.eu/chest/dataitems/1083/view`) — confirmed to break the download flow when reached that way; always go in through the report page.
- **File:** `data/raw/TTF price _EUR_MWh_ - 20260421 (1).csv`
- **Format:** CSV, columns `Date` (DD.MM.YYYY) / `Price, EUR/MWh`, one row per day.
- **Range:** 01.01.2021–08.04.2026, **1,924 rows**.
- **Units:** EUR/MWh, daily.
- **Timezone:** not stated on the source; treated as a plain calendar date, no time-of-day component to convert.
- **Downloaded:** 2026-09-08.

## German day-ahead electricity price (EUR/MWh)

- **Source:** SMARD (Bundesnetzagentur), series id 4169, filter DE.
- **Endpoint:** `smard.de/app/chart_data/4169/DE/4169_DE_day_{timestamp}.json`. **The `{timestamp}` is not arbitrary** — despite "_day_" in the filename, each timestamp identifies a year-bucket of daily points, not a single day. Valid timestamps must come from `smard.de/app/chart_data/4169/DE/index_day.json`'s own list; a guessed value 404s.
- **Pull script:** `scripts/pull_smard.py` — fetches every bucket the index lists (cheap, avoids re-deriving which buckets are needed), then filters to the target date range after parsing.
- **File:** `data/raw/smard_electricity_de_2021_2026.csv`
- **Format:** CSV, columns `date` (YYYY-MM-DD) / `price_eur_mwh`, one row per day.
- **Range:** 2021-01-01–2026-04-08, **1,924 rows** — matches the TTF series exactly.
- **Units:** EUR/MWh, daily.
- **Timezone — the real gotcha, worth keeping documented:** SMARD's raw timestamps mark local German midnight, not UTC midnight, and Germany isn't a fixed UTC offset (CET = UTC+1 in winter, CEST = UTC+2 in summer under daylight saving). A naive UTC read of the raw epoch timestamp mislabels the date — e.g. Jan 1 2021 00:00 CET is Dec 31 2020 23:00 UTC. The pull script converts to `Europe/Berlin` before extracting the calendar date; comparing raw UTC timestamps against a UTC-implied date range silently drops the Jan 1 row every year. Two real bugs hit and fixed during this pull (2026-09-08): a UTC-year mislabeling that dropped the entire 2021 bucket, then this same-shape boundary issue dropping one row.
- **Downloaded:** 2026-09-08.

## Join note (for session 0's own decision, not yet made)

Both series are now daily and span the identical range (2021-01-01 to 2026-04-08, 1,924 rows each) — but gas trades on weekdays only in some conventions while electricity has a price every day. Confirm whether that's actually true of these two specific pulls (row-count parity suggests it might not be, but that needs checking against the actual weekday/weekend pattern, not assumed) before deciding forward-fill vs. inner-join-on-trading-days.
