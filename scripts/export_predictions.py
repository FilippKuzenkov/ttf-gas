"""Export ship #2's test-set predictions to a CSV, for the combined Tableau
dashboard. fit_model.py only prints results - this reuses its exact fitting
logic and writes the same numbers to a file instead of stdout.

Uses the winning feature set (gas_lag1 + electricity_lag1) - the only one
that beat baseline, per fit_model.py's own comparison. Not all three sets;
a dashboard reader needs one real model to evaluate, not three to choose
between.
"""
import pandas as pd

from analyze_correlation import JOINED_PATH, PROJECT_ROOT
from build_features import build_lagged_daily, chronological_split
from fit_model import fit_linear_model, predict, TARGET

OUTPUT_PATH = PROJECT_ROOT / "data" / "clean" / "predictions.csv"
FEATURES = ["gas_lag1", "electricity_lag1"]


def main():
    joined = pd.read_csv(JOINED_PATH)
    daily = build_lagged_daily(joined)
    train, test = chronological_split(daily)

    coeffs = fit_linear_model(train, FEATURES)
    model_pred = predict(test, coeffs, FEATURES)

    out = test[["date", TARGET, "gas_lag1", "electricity_lag1"]].copy()
    out = out.rename(columns={
        TARGET: "actual_electricity_eur_mwh",
        "electricity_lag1": "baseline_pred_eur_mwh",
    })
    out["model_pred_eur_mwh"] = model_pred
    out["baseline_error_eur_mwh"] = out["baseline_pred_eur_mwh"] - out["actual_electricity_eur_mwh"]
    out["model_error_eur_mwh"] = out["model_pred_eur_mwh"] - out["actual_electricity_eur_mwh"]

    out.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {len(out)} test-set rows to {OUTPUT_PATH}")
    print(f"Date range: {out['date'].min()} to {out['date'].max()}")


if __name__ == "__main__":
    main()
