"""Ship #1 core analysis: does TTF gas price track German day-ahead
electricity price?

Part 1: aggregate the joined hourly data to one row per day, so gas
(one real value per day) and electricity are compared at matching
grains. Correlating gas directly against all hourly rows would treat
each day's repeated gas value as ~24 independent observations
(pseudo-replication).

Part 2: correlation, a simple linear fit, and a scatter plot for both
the mean and peak daily electricity series against gas.

Part 3: does the relationship hold evenly, or does it vary by
hour-of-day, weekday/weekend, or season? Three independent single-
dimension segment cuts (never combined), each re-aggregated to daily
grain before correlating, for the same pseudo-replication reason as
Part 1.

Caveat, stated explicitly rather than implied: correlation and R² here
say nothing about causation. No other driver of electricity price
(demand, renewable output, carbon price) is controlled for.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JOINED_PATH = PROJECT_ROOT / "data" / "clean" / "joined_ttf_electricity.csv"
CHARTS_DIR = PROJECT_ROOT / "charts"

MONTH_TO_SEASON = {
    12: "winter", 1: "winter", 2: "winter",
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn",
}


def correlate(x, y):
    """Return correlation, a linear fit, R², and sample size for x vs y."""
    correlation = np.corrcoef(x, y)[0, 1]
    slope, intercept = np.polyfit(x, y, deg=1)
    return {
        "r": correlation,
        "slope": slope,
        "intercept": intercept,
        "r_squared": correlation ** 2,
        "n": len(x),
    }


def build_daily_aggregates(joined):
    """Collapse hourly rows to one row per day (mean and peak electricity)."""
    daily = joined.groupby("date").agg(
        electricity_mean_eur_mwh=("electricity_price_eur_mwh", "mean"),
        electricity_peak_eur_mwh=("electricity_price_eur_mwh", "max"),
        gas_price_eur_mwh=("gas_price_eur_mwh", "mean"),
    ).reset_index()
    return daily


def fit_and_plot(daily, electricity_col, label, filename):
    """Correlate, fit a line, plot, and save one gas-vs-electricity chart."""
    x = daily["gas_price_eur_mwh"].to_numpy()
    y = daily[electricity_col].to_numpy()
    fit = correlate(x, y)

    print(f"\n{label}:")
    print(f"  correlation (r): {fit['r']:.3f}")
    print(
        f"  fit: electricity = {fit['slope']:.3f} * gas + "
        f"{fit['intercept']:.3f}"
    )
    print(f"  r-squared: {fit['r_squared']:.3f}")

    fig, ax = plt.subplots()
    ax.scatter(x, y, alpha=0.3, s=10)
    fit_x = np.array([x.min(), x.max()])
    ax.plot(fit_x, fit["slope"] * fit_x + fit["intercept"], color="red")
    ax.set_xlabel("Gas price (EUR/MWh)")
    ax.set_ylabel(f"{label} (EUR/MWh)")
    ax.set_title(f"{label} vs. gas price (r={fit['r']:.2f})")

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CHARTS_DIR / filename
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved: {out_path}")


def build_segment_table(joined, daily):
    """Correlate gas vs. mean electricity within each of 3 segment cuts."""
    rows = []

    # Hour-of-day: daytime (08-19) vs nighttime, across all days. A
    # simplified single-dimension version of the industry peak/off-peak
    # convention (which also restricts peak to weekdays) - kept to hour
    # only so this stays one clean dimension, not two blended together.
    hourly = joined.copy()
    # timestamp_local round-trips through CSV as a string with a mixed
    # UTC offset (CET/CEST), so it must be parsed as UTC first, then
    # converted back to local time before reading the hour - matching
    # the same fix already required in pull_smard.py.
    local_ts = pd.to_datetime(hourly["timestamp_local"], utc=True)
    hourly["hour"] = local_ts.dt.tz_convert("Europe/Berlin").dt.hour
    hourly["time_of_day"] = np.where(
        hourly["hour"].between(8, 19), "daytime", "nighttime"
    )
    for segment_value, group in hourly.groupby("time_of_day"):
        segment_daily = group.groupby("date").agg(
            electricity_mean_eur_mwh=("electricity_price_eur_mwh", "mean"),
            gas_price_eur_mwh=("gas_price_eur_mwh", "mean"),
        )
        fit = correlate(
            segment_daily["gas_price_eur_mwh"].to_numpy(),
            segment_daily["electricity_mean_eur_mwh"].to_numpy(),
        )
        row = {"dimension": "hour-of-day", "segment": segment_value, **fit}
        rows.append(row)

    # Weekday vs weekend - reuses the daily table Part 1 already built,
    # just filtered by day of week.
    daily_days = daily.copy()
    dates = pd.to_datetime(daily_days["date"])
    daily_days["is_weekday"] = dates.dt.dayofweek < 5
    for segment_value, is_weekday in [("weekday", True), ("weekend", False)]:
        group = daily_days[daily_days["is_weekday"] == is_weekday]
        fit = correlate(
            group["gas_price_eur_mwh"].to_numpy(),
            group["electricity_mean_eur_mwh"].to_numpy(),
        )
        row = {"dimension": "weekday/weekend", "segment": segment_value, **fit}
        rows.append(row)

    # Season - meteorological, from the calendar month.
    daily_seasons = daily.copy()
    months = pd.to_datetime(daily_seasons["date"]).dt.month
    daily_seasons["season"] = months.map(MONTH_TO_SEASON)
    for segment_value, group in daily_seasons.groupby("season"):
        fit = correlate(
            group["gas_price_eur_mwh"].to_numpy(),
            group["electricity_mean_eur_mwh"].to_numpy(),
        )
        rows.append({"dimension": "season", "segment": segment_value, **fit})

    return pd.DataFrame(rows)


def plot_segment_comparison(segment_table, filename):
    """Save a grouped bar chart comparing r across all segment cuts."""
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = {
        "hour-of-day": "tab:blue",
        "weekday/weekend": "tab:orange",
        "season": "tab:green",
    }
    bar_colors = segment_table["dimension"].map(colors)
    bars = ax.bar(segment_table["segment"], segment_table["r"], color=bar_colors)
    for bar, r_value in zip(bars, segment_table["r"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
            f"{r_value:.3f}", ha="center", va="bottom", fontsize=8,
        )

    ax.set_ylabel("Correlation (r) with gas price")
    ax.set_title("Gas-electricity correlation by segment")
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_locator(plt.MultipleLocator(0.1))
    ax.axhline(0, color="black", linewidth=0.5)
    ax.grid(axis="y", linestyle=":", alpha=0.5)

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CHARTS_DIR / filename
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nSaved: {out_path}")


def main():
    """Aggregate to daily grain, then correlate/fit/plot mean and peak."""
    joined = pd.read_csv(JOINED_PATH)
    print(f"Hourly joined rows: {len(joined):,}")

    daily = build_daily_aggregates(joined)
    print(f"Daily rows after aggregation: {len(daily):,}")
    print("Expected: close to 1,924 (one per calendar day in range)")

    fit_and_plot(
        daily, "electricity_mean_eur_mwh", "Daily mean electricity price",
        "gas_vs_electricity_mean.png",
    )
    fit_and_plot(
        daily, "electricity_peak_eur_mwh", "Daily peak electricity price",
        "gas_vs_electricity_peak.png",
    )

    segment_table = build_segment_table(joined, daily)
    print("\nSegment comparison (mean electricity vs. gas):")
    print(segment_table.to_string(index=False))
    plot_segment_comparison(segment_table, "correlation_by_segment.png")

    print(
        "\nCaveat: correlation/R-squared above say nothing about "
        "causation - demand, renewable output, and carbon price are "
        "all unaccounted-for drivers of electricity price."
    )


if __name__ == "__main__":
    main()
