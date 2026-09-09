"""Pull SMARD day-ahead electricity prices (Germany, series 4169) at hourly
resolution for 2021-01-01 through 2026-04-08.

Endpoint: smard.de/app/chart_data/4169/DE/4169_DE_hour_{timestamp}.json

Each ``{timestamp}`` identifies a week-bucket of 168 hourly points, not a
single hour, and is not arbitrary: valid values come only from
``index_hour.json``, a guessed value returns 404.
"""
import pandas as pd
import requests
from pathlib import Path

BASE = "https://www.smard.de/app/chart_data/4169/DE"
START_DATE = "2021-01-01"
END_DATE = "2026-04-08"  # matches the TTF CSV's last row
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = (
    PROJECT_ROOT / "data" / "raw" / "smard_electricity_de_2021_2026_hourly.csv"
)


def get_valid_timestamps():
    """Return the list of valid week-bucket timestamps from SMARD's index."""
    r = requests.get(f"{BASE}/index_hour.json")
    r.raise_for_status()
    return r.json()["timestamps"]


def pull_week_bucket(timestamp):
    """Return the [timestamp_ms, price] series for one week-bucket."""
    r = requests.get(f"{BASE}/4169_DE_hour_{timestamp}.json")
    r.raise_for_status()
    return r.json()["series"]


def main():
    """Pull, clean, and save the full hourly SMARD price series to CSV."""
    # Fetch every bucket, then filter by date afterward rather than by the
    # bucket's own timestamp - the timestamp marks a week in CET, and a
    # UTC-based pre-filter can mislabel buckets near a year boundary.
    timestamps = get_valid_timestamps()

    all_rows = []
    for ts in timestamps:
        series = pull_week_bucket(ts)
        all_rows.extend(series)
        print(f"Pulled bucket (timestamp {ts}): {len(series)} points")

    df = pd.DataFrame(all_rows, columns=["timestamp_ms", "price_eur_mwh"])
    # Germany's UTC offset changes with daylight saving (CET/CEST), so the
    # date must be read after converting to Europe/Berlin, not from the raw
    # UTC timestamp - otherwise Jan 1 lands one day early.
    df["timestamp_local"] = (
        pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
        .dt.tz_convert("Europe/Berlin")
    )
    df["date"] = df["timestamp_local"].dt.date.astype(str)
    df = df.dropna(subset=["price_eur_mwh"])
    df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)]
    df = df.sort_values("timestamp_local")
    df = df.drop_duplicates(subset="timestamp_local")

    ts_min = df["timestamp_local"].min()
    ts_max = df["timestamp_local"].max()
    print(f"\nTotal rows after filtering to {START_DATE}..{END_DATE}: {len(df)}")
    print(f"Timestamp range in data: {ts_min} to {ts_max}")
    print("\nFirst 3 rows (cross-check against smard.de's own chart):")
    print(df[["timestamp_local", "price_eur_mwh"]].head(3).to_string(index=False))
    print(
        "\nExpected row count is roughly 46,000 (168 hours/week x ~275 "
        "weeks) - if far off, stop and check before using this data."
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df[["timestamp_local", "price_eur_mwh"]].to_csv(OUT_PATH, index=False)
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()
