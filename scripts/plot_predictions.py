"""Actual vs. predicted over time, error over time, and a hand-check of a
few individual prediction rows.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analyze_correlation import CHARTS_DIR, JOINED_PATH
from build_features import build_lagged_daily, chronological_split
from fit_model import TARGET, fit_linear_model, predict

FEATURES = ["gas_lag1", "electricity_lag1"]


def plot_actual_vs_predicted(test, y_true, baseline_pred, model_pred, filename):
    dates = pd.to_datetime(test["date"])
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(dates, y_true, label="Actual", color="black", linewidth=1)
    ax.plot(dates, baseline_pred, label="Baseline (persistence)",
            color="tab:orange", alpha=0.7, linewidth=1)
    ax.plot(dates, model_pred, label="Model (gas_lag1 + electricity_lag1)",
            color="tab:blue", alpha=0.7, linewidth=1)
    ax.set_ylabel("Electricity price (EUR/MWh)")
    ax.set_title("Actual vs. predicted, test period")
    ax.legend()

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CHARTS_DIR / filename
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_error_over_time(test, y_true, baseline_pred, model_pred, filename):
    dates = pd.to_datetime(test["date"])
    baseline_error = np.abs(baseline_pred - y_true)
    model_error = np.abs(model_pred - y_true)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(dates, baseline_error, label="Baseline error",
            color="tab:orange", alpha=0.7, linewidth=1)
    ax.plot(dates, model_error, label="Model error",
            color="tab:blue", alpha=0.7, linewidth=1)
    ax.set_ylabel("Absolute error (EUR/MWh)")
    ax.set_title("Absolute error over time, test period")
    ax.legend()

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CHARTS_DIR / filename
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


def hand_check(test, y_true, baseline_pred, model_pred, n=5):
    """Print n rows spread across the test period, not just the first n."""
    idx = np.linspace(0, len(test) - 1, n, dtype=int)
    print("\nHand-check rows - verify a couple of these against the raw "
          "CSV/joined data yourself before trusting the model output:")
    print(f"{'date':<12}{'gas_lag1':>10}{'elec_lag1':>11}{'actual':>9}"
          f"{'baseline':>10}{'model':>9}")
    for i in idx:
        row = test.iloc[i]
        print(
            f"{row['date']:<12}{row['gas_lag1']:>10.2f}"
            f"{row['electricity_lag1']:>11.2f}{y_true[i]:>9.2f}"
            f"{baseline_pred[i]:>10.2f}{model_pred[i]:>9.2f}"
        )


def main():
    joined = pd.read_csv(JOINED_PATH)
    daily = build_lagged_daily(joined)
    train, test = chronological_split(daily)

    coeffs = fit_linear_model(train, FEATURES)
    y_true = test[TARGET].to_numpy()
    baseline_pred = test["electricity_lag1"].to_numpy()
    model_pred = predict(test, coeffs, FEATURES)

    plot_actual_vs_predicted(
        test, y_true, baseline_pred, model_pred,
        "ship2_actual_vs_predicted.png",
    )
    plot_error_over_time(
        test, y_true, baseline_pred, model_pred,
        "ship2_error_over_time.png",
    )
    hand_check(test, y_true, baseline_pred, model_pred)


if __name__ == "__main__":
    main()
