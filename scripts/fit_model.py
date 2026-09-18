"""Fit the naive baseline and the lagged-gas regression, then compare them
on the held-out test set.

Baseline: today's electricity price = yesterday's (electricity_lag1).
Model: linear regression, electricity_mean ~ features, fit on train only,
evaluated on test only.

Plain numpy (np.linalg.lstsq) rather than scikit-learn - a few predictors
don't need a modeling library.
"""
import numpy as np
import pandas as pd

from analyze_correlation import JOINED_PATH
from build_features import build_lagged_daily, chronological_split

TARGET = "electricity_mean_eur_mwh"

# gas_lag1/3/7 are highly correlated with each other, which can make a
# least-squares fit unstable - comparing against gas_lag1 alone checks
# whether that instability, not an absence of signal, explains a loss to
# baseline. gas_lag1 + electricity_lag1 tests the fairer question: does gas
# add anything once yesterday's price is already a feature.
FEATURE_SETS = {
    "3-lag (lag1+lag3+lag7)": ["gas_lag1", "gas_lag3", "gas_lag7"],
    "1-lag (lag1 only)": ["gas_lag1"],
    "gas_lag1 + electricity_lag1": ["gas_lag1", "electricity_lag1"],
}


def mae_rmse(y_true, y_pred):
    errors = y_pred - y_true
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors ** 2))
    return mae, rmse


def fit_linear_model(train, features):
    """Least-squares fit: TARGET ~ intercept + features, train rows only."""
    X = np.column_stack([np.ones(len(train)), train[features].to_numpy()])
    y = train[TARGET].to_numpy()
    coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coeffs  # [intercept, *one weight per feature, in order]


def predict(rows, coeffs, features):
    X = np.column_stack([np.ones(len(rows)), rows[features].to_numpy()])
    return X @ coeffs


def main():
    joined = pd.read_csv(JOINED_PATH)
    daily = build_lagged_daily(joined)
    train, test = chronological_split(daily)

    y_true = test[TARGET].to_numpy()

    baseline_pred = test["electricity_lag1"].to_numpy()
    baseline_mae, baseline_rmse = mae_rmse(y_true, baseline_pred)
    print(f"Baseline (persistence)  MAE: {baseline_mae:.2f}  RMSE: {baseline_rmse:.2f}")

    for label, features in FEATURE_SETS.items():
        coeffs = fit_linear_model(train, features)
        model_pred = predict(test, coeffs, features)
        model_mae, model_rmse = mae_rmse(y_true, model_pred)

        print(f"\n{label}:")
        print("  coefficients (intercept, " + ", ".join(features) + "):")
        print("  " + ", ".join(f"{c:.4f}" for c in coeffs))
        print(f"  MAE: {model_mae:.2f}  RMSE: {model_rmse:.2f}")
        print(f"  Improvement over baseline (MAE):  {baseline_mae - model_mae:+.2f} EUR/MWh")
        print(f"  Improvement over baseline (RMSE): {baseline_rmse - model_rmse:+.2f} EUR/MWh")


if __name__ == "__main__":
    main()
