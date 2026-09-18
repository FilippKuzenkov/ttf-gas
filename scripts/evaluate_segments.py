"""Check whether the model's edge over baseline holds evenly across
weekday/weekend and season, or is concentrated in a few days.
"""
import pandas as pd

from analyze_correlation import JOINED_PATH, MONTH_TO_SEASON
from build_features import build_lagged_daily, chronological_split
from fit_model import TARGET, fit_linear_model, mae_rmse, predict

FEATURES = ["gas_lag1", "electricity_lag1"]


def segment_errors(test, coeffs, mask, dimension, segment_name):
    subset = test[mask]
    if len(subset) == 0:
        return None

    y_true = subset[TARGET].to_numpy()
    baseline_pred = subset["electricity_lag1"].to_numpy()
    model_pred = predict(subset, coeffs, FEATURES)

    baseline_mae, baseline_rmse = mae_rmse(y_true, baseline_pred)
    model_mae, model_rmse = mae_rmse(y_true, model_pred)

    return {
        "dimension": dimension,
        "segment": segment_name,
        "n": len(subset),
        "baseline_mae": round(baseline_mae, 2),
        "model_mae": round(model_mae, 2),
        "improvement_mae": round(baseline_mae - model_mae, 2),
        "baseline_rmse": round(baseline_rmse, 2),
        "model_rmse": round(model_rmse, 2),
        "improvement_rmse": round(baseline_rmse - model_rmse, 2),
    }


def main():
    joined = pd.read_csv(JOINED_PATH)
    daily = build_lagged_daily(joined)
    train, test = chronological_split(daily)

    coeffs = fit_linear_model(train, FEATURES)

    dates = pd.to_datetime(test["date"])
    is_weekday = (dates.dt.dayofweek < 5).to_numpy()
    seasons = dates.dt.month.map(MONTH_TO_SEASON).to_numpy()

    rows = [
        segment_errors(test, coeffs, is_weekday, "weekday/weekend", "weekday"),
        segment_errors(test, coeffs, ~is_weekday, "weekday/weekend", "weekend"),
    ]
    for season in pd.unique(seasons):
        rows.append(segment_errors(test, coeffs, seasons == season, "season", season))

    table = pd.DataFrame([r for r in rows if r is not None])
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
