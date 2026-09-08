"""
Pull SMARD day-ahead electricity price data (Germany, series 4169) for
01.01.2021-08.04.2026, matching the TTF gas price CSV's date range.

Endpoint confirmed live 2026-09-08:
    smard.de/app/chart_data/4169/DE/4169_DE_day_{timestamp}.json

IMPORTANT: the {timestamp} is NOT arbitrary. Despite "_day_" in the filename,
each timestamp identifies a *year-bucket* of daily data points, not a single
day. Valid timestamps must come from index_day.json's own list - a guessed
value 404s (confirmed the hard way before writing this).
"""
import requests
import pandas as pd
from pathlib import Path

BASE = "https://www.smard.de/app/chart_data/4169/DE"
START_DATE = "2021-01-01"
END_DATE = "2026-04-08"  # matches the TTF CSV's last row
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = PROJECT_ROOT / "data" / "raw" / "smard_electricity_de_2021_2026.csv"


def get_valid_timestamps():
    r = requests.get(f"{BASE}/index_day.json")
    r.raise_for_status()
    return r.json()["timestamps"]


def pull_year_bucket(timestamp):
    r = requests.get(f"{BASE}/4169_DE_day_{timestamp}.json")
    r.raise_for_status()
    return r.json()["series"]


def main():
    # Pull every bucket the index lists - don't pre-filter by timestamp-derived
    # year. SMARD's bucket timestamps mark the start of the year in CET, and
    # converting to a UTC year mislabels every single one by one year (the
    # "2022" bucket's timestamp lands on Dec 31 2021 23:00 UTC). Simpler and
    # correct: fetch everything, filter by the actual parsed date afterward.
    timestamps = get_valid_timestamps()

    all_rows = []
    for ts in timestamps:
        series = pull_year_bucket(ts)
        all_rows.extend(series)
        print(f"Pulled bucket (timestamp {ts}): {len(series)} points")

    df = pd.DataFrame(all_rows, columns=["timestamp_ms", "price_eur_mwh"])
    # SMARD's timestamps mark local German midnight, not UTC midnight - and
    # Germany isn't a fixed UTC offset (CET = UTC+1 winter, CEST = UTC+2
    # summer/DST). Converting to Europe/Berlin before taking the date is what
    # actually recovers the intended calendar date; comparing raw UTC
    # timestamps against a UTC-implied START_DATE silently drops the Jan 1
    # row every year (it lands at Dec 31 23:00 UTC the year before).
    df["date"] = (
        pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
        .dt.tz_convert("Europe/Berlin")
        .dt.date
    )
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["price_eur_mwh"])
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)]
    df = df.sort_values("date").drop_duplicates(subset="date")

    print(f"\nTotal rows after filtering to {START_DATE}..{END_DATE}: {len(df)}")
    print(f"Date range in data: {df['date'].min()} to {df['date'].max()}")
    print("\nFirst 3 rows (cross-check these against smard.de's own chart manually):")
    print(df[["date", "price_eur_mwh"]].head(3).to_string(index=False))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df[["date", "price_eur_mwh"]].to_csv(OUT_PATH, index=False)
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()
