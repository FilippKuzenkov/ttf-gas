"""Lag features and the chronological train/test split.

Reuses the earlier daily aggregation (analyze_correlation.build_daily_aggregates)
so this step can't disagree with the correlation analysis on what a "day" is.

Lag features: gas price from 1/3/7 days back, predicting the same day's mean
electricity price. The naive baseline uses a separate lag - yesterday's
electricity price - not a gas-based feature.

The first 7 rows have no valid lag-7 value and are dropped.
"""
import pandas as pd
from analyze_correlation import build_daily_aggregates, JOINED_PATH

TEST_DAYS = 385  # last ~20% chronologically, roughly a full year


def build_lagged_daily(joined):
    """Daily aggregates plus gas lag-1/3/7 and electricity lag-1 (baseline)."""
    daily = (
        build_daily_aggregates(joined)
        .sort_values("date")
        .reset_index(drop=True)
    )

    for lag in (1, 3, 7):
        daily[f"gas_lag{lag}"] = daily["gas_price_eur_mwh"].shift(lag)

    daily["electricity_lag1"] = daily["electricity_mean_eur_mwh"].shift(1)

    before = len(daily)
    daily = daily.dropna(
        subset=["gas_lag7", "electricity_lag1"]
    ).reset_index(drop=True)
    print(f"Dropped {before - len(daily)} leading rows with no valid lag (of {before})")

    return daily


def chronological_split(daily, test_days=TEST_DAYS):
    """Last `test_days` rows as test, everything before as train."""
    train = daily.iloc[:-test_days].reset_index(drop=True)
    test = daily.iloc[-test_days:].reset_index(drop=True)
    return train, test


def main():
    joined = pd.read_csv(JOINED_PATH)
    daily = build_lagged_daily(joined)
    train, test = chronological_split(daily)

    print(f"\nTotal usable days: {len(daily):,}")
    print(f"Train: {len(train):,}  ({train['date'].min()} to {train['date'].max()})")
    print(f"Test:  {len(test):,}  ({test['date'].min()} to {test['date'].max()})")


if __name__ == "__main__":
    main()
