"""Diagnostic: does staling weekday gas price by one day (mimicking what weekends structurally do)
drop weekday correlation toward the weekend's, suggesting staleness?
"""
import pandas as pd
from analyze_correlation import build_daily_aggregates, correlate, JOINED_PATH

joined = pd.read_csv(JOINED_PATH)
daily = build_daily_aggregates(joined).sort_values("date").copy()
daily["gas_price_lagged"] = daily["gas_price_eur_mwh"].shift(1)
daily["is_weekday"] = pd.to_datetime(daily["date"]).dt.dayofweek < 5

weekday = daily[daily["is_weekday"]].dropna(subset=["gas_price_lagged"])
real = correlate(weekday["gas_price_eur_mwh"].to_numpy(), weekday["electricity_mean_eur_mwh"].to_numpy())
staled = correlate(weekday["gas_price_lagged"].to_numpy(), weekday["electricity_mean_eur_mwh"].to_numpy())

print(f"Weekday, real gas price:        r={real['r']:.3f}")
print(f"Weekday, gas price staled 1 day: r={staled['r']:.3f}")
print(f"Weekend, for reference:          r=0.837")