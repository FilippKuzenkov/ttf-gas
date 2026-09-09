"""Join TTF gas price (daily) onto SMARD electricity price (hourly).

Uses a broadcast join: each day's single gas price is repeated across
every hourly electricity row for that date, since the two series do not
share a time grain (gas has no intraday data).
"""
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
GAS_PATH = DATA_RAW / "TTF price _EUR_MWh_ - 20260421 (1).csv"
ELECTRICITY_PATH = DATA_RAW / "smard_electricity_de_2021_2026_hourly.csv"
OUT_PATH = PROJECT_ROOT / "data" / "clean" / "joined_ttf_electricity.csv"


def main():
    """Load both raw series, broadcast-join them, and save the result."""
    gas = pd.read_csv(GAS_PATH)
    gas.columns = ["date", "gas_price_eur_mwh"]
    gas["date"] = pd.to_datetime(gas["date"], format="%d.%m.%Y").dt.date

    elec = pd.read_csv(ELECTRICITY_PATH)
    elec.columns = ["timestamp_local", "electricity_price_eur_mwh"]
    elec["timestamp_local"] = (
        pd.to_datetime(elec["timestamp_local"], utc=True)
        .dt.tz_convert("Europe/Berlin")
    )
    elec["date"] = elec["timestamp_local"].dt.date

    print(f"Gas rows (daily):        {len(gas):,}")
    print(f"Electricity rows (hourly): {len(elec):,}")

    # Left join on electricity so no hourly row is ever lost; a date
    # missing from gas should surface as a gap, not be silently dropped.
    joined = elec.merge(gas, on="date", how="left")

    missing_gas = joined["gas_price_eur_mwh"].isna().sum()
    print(f"Joined rows:              {len(joined):,}")
    print(f"Electricity rows with no matching gas price: {missing_gas:,}")

    if len(joined) != len(elec):
        raise ValueError(
            f"Row count changed during the join ({len(elec)} -> "
            f"{len(joined)}) - the merge is duplicating rows, investigate."
        )

    # Hand-trace a few rows against the raw inputs rather than trusting
    # the join blindly.
    print("\nHand-trace sample - check these against the raw CSVs by eye:")
    for _, row in joined.sample(3, random_state=42).iterrows():
        print(
            f"  {row['timestamp_local']}  "
            f"electricity={row['electricity_price_eur_mwh']}  "
            f"date={row['date']}  gas={row['gas_price_eur_mwh']}"
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_columns = [
        "timestamp_local", "date", "electricity_price_eur_mwh",
        "gas_price_eur_mwh",
    ]
    joined[out_columns].to_csv(OUT_PATH, index=False)
    print(f"\nSaved to {OUT_PATH}")


if __name__ == "__main__":
    main()
