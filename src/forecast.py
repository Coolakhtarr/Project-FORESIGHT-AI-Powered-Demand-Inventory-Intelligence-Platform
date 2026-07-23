"""
FORESIGHT — Demand Forecast Model (D3)
========================================
Weekly, SKU-level demand forecasting.

Methodology (per the engagement brief, Section 07):
  1. Frame & metric   -> WAPE (weighted absolute percentage error)
  2. Baseline         -> seasonal-naive (same week, 52 weeks prior)
  3. Features         -> lags, rolling stats, calendar, promo
  4. Model            -> LightGBM (gradient-boosted trees), global panel model
  5. Backtest         -> rolling-origin cross-validation (never random split)
  6. Evaluate & select -> compare model vs baseline WAPE, report honestly
  7. Forecast          -> recursive multi-step, 8-week horizon, with an
                           80% prediction interval via quantile regression

Run:
    python src/forecast.py
"""

import numpy as np
import pandas as pd
import lightgbm as lgb
import json

HORIZON_WEEKS = 8
N_BACKTEST_FOLDS = 6
RANDOM_SEED = 42


def wape(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Weighted Absolute Percentage Error. Robust to low-volume SKUs."""
    actual = np.asarray(actual, dtype=float)
    forecast = np.asarray(forecast, dtype=float)
    denom = np.sum(np.abs(actual))
    if denom == 0:
        return np.nan
    return np.sum(np.abs(actual - forecast)) / denom


def bias(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Mean signed error — checks systematic over/under-forecasting."""
    return float(np.mean(np.asarray(forecast) - np.asarray(actual)))


def load_weekly_panel():
    sd = pd.read_csv("data/processed/sales_daily.csv", parse_dates=["date"])
    sm = pd.read_csv("data/processed/sku_master.csv")
    cal = pd.read_csv("data/processed/calendar.csv", parse_dates=["date"])

    sd = sd.merge(cal[["date", "is_holiday"]], on="date", how="left")

    sd["week"] = sd["date"].dt.to_period("W-SUN").dt.start_time
    weekly = (
        sd.groupby(["sku_id", "week"])
        .agg(
            units_sold=("units_sold", "sum"),
            promo_flag=("promo_flag", "max"),
            is_holiday=("is_holiday", "max"),
            unit_price=("unit_price", "mean"),
        )
        .reset_index()
    )
    weekly = weekly.merge(sm[["sku_id", "category"]], on="sku_id", how="left")
    weekly["month"] = weekly["week"].dt.month
    weekly["season"] = weekly["month"].map({
        12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1,
        6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3,
    })
    weekly["cat_code"] = weekly["category"].astype("category").cat.codes
    return weekly.sort_values(["sku_id", "week"]).reset_index(drop=True)


def add_features(weekly: pd.DataFrame) -> pd.DataFrame:
    """
    Lag and rolling features. Computed strictly from PAST values only
    (shift() before any rolling/window op) — no future information ever
    enters a feature, per the brief's non-negotiable rule.
    """
    df = weekly.copy()
    g = df.groupby("sku_id")["units_sold"]

    for lag in [1, 2, 4, 8, 52]:
        df[f"lag_{lag}"] = g.shift(lag)

    df["roll_mean_4"] = g.shift(1).rolling(4, min_periods=2).mean().reset_index(level=0, drop=True)
    df["roll_mean_8"] = g.shift(1).rolling(8, min_periods=2).mean().reset_index(level=0, drop=True)
    df["roll_std_4"] = g.shift(1).rolling(4, min_periods=2).std().reset_index(level=0, drop=True)

    return df


FEATURES = [
    "lag_1", "lag_2", "lag_4", "lag_8", "lag_52",
    "roll_mean_4", "roll_mean_8", "roll_std_4",
    "month", "season", "is_holiday", "promo_flag", "cat_code",
]


def seasonal_naive_predict(df: pd.DataFrame) -> pd.Series:
    """Baseline: this week's demand = same week 52 weeks ago.
    Falls back to the 4-week rolling mean when a full year of history
    isn't yet available (only affects the first year of the series)."""
    return df["lag_52"].fillna(df["roll_mean_4"]).fillna(0)


def rolling_origin_backtest(weekly: pd.DataFrame):
    """
    Rolling-origin CV: repeatedly train on the past, forecast the next
    HORIZON_WEEKS, roll the origin forward, repeat. Never a random split.
    """
    feat = add_features(weekly)
    all_weeks = sorted(feat["week"].unique())

    # leave enough history for lag_52 to be meaningful in at least the
    # later folds; start folds after week 60 so most SKUs have real lag_52
    fold_starts = np.linspace(60, len(all_weeks) - HORIZON_WEEKS - 1, N_BACKTEST_FOLDS).astype(int)

    fold_results = []
    for fold_i, start_idx in enumerate(fold_starts):
        origin_week = all_weeks[start_idx]
        horizon_weeks = all_weeks[start_idx + 1: start_idx + 1 + HORIZON_WEEKS]
        if len(horizon_weeks) < HORIZON_WEEKS:
            continue

        train = feat[feat["week"] <= origin_week].dropna(subset=["lag_1"])
        test = feat[feat["week"].isin(horizon_weeks)].copy()

        if len(train) < 500 or len(test) == 0:
            continue

        model = lgb.LGBMRegressor(
            n_estimators=300, learning_rate=0.05, max_depth=6,
            num_leaves=31, random_state=RANDOM_SEED, verbosity=-1,
        )
        model.fit(train[FEATURES].fillna(0), train["units_sold"])

        test_model_pred = model.predict(test[FEATURES].fillna(0)).clip(min=0)
        test_baseline_pred = seasonal_naive_predict(test)

        fold_wape_model = wape(test["units_sold"], test_model_pred)
        fold_wape_baseline = wape(test["units_sold"], test_baseline_pred)

        fold_results.append({
            "fold": fold_i,
            "origin_week": str(origin_week.date()),
            "wape_model": round(fold_wape_model, 4),
            "wape_baseline": round(fold_wape_baseline, 4),
            "bias_model": round(bias(test["units_sold"], test_model_pred), 3),
            "bias_baseline": round(bias(test["units_sold"], test_baseline_pred), 3),
            "n_obs": len(test),
        })

    return pd.DataFrame(fold_results)


def train_final_model(weekly: pd.DataFrame):
    """Train the production model on all available history."""
    feat = add_features(weekly)
    train = feat.dropna(subset=["lag_1"])

    model = lgb.LGBMRegressor(
        n_estimators=300, learning_rate=0.05, max_depth=6,
        num_leaves=31, random_state=RANDOM_SEED, verbosity=-1,
    )
    model.fit(train[FEATURES].fillna(0), train["units_sold"])

    # quantile models for an 80% prediction interval
    model_lo = lgb.LGBMRegressor(
        objective="quantile", alpha=0.1, n_estimators=300, learning_rate=0.05,
        max_depth=6, num_leaves=31, random_state=RANDOM_SEED, verbosity=-1,
    )
    model_hi = lgb.LGBMRegressor(
        objective="quantile", alpha=0.9, n_estimators=300, learning_rate=0.05,
        max_depth=6, num_leaves=31, random_state=RANDOM_SEED, verbosity=-1,
    )
    model_lo.fit(train[FEATURES].fillna(0), train["units_sold"])
    model_hi.fit(train[FEATURES].fillna(0), train["units_sold"])

    return model, model_lo, model_hi, feat


def recursive_forecast(weekly: pd.DataFrame, model, model_lo, model_hi):
    """
    Produce an 8-week-ahead forecast per SKU, recursively feeding each
    week's prediction back in as the next week's lag features.
    """
    feat = add_features(weekly)
    last_week = feat["week"].max()
    future_weeks = [last_week + pd.Timedelta(weeks=i) for i in range(1, HORIZON_WEEKS + 1)]

    working = feat.copy()
    forecasts = []

    for wk in future_weeks:
        latest = (
            working.sort_values("week")
            .groupby("sku_id")
            .tail(1)
            .copy()
        )
        # roll lag features forward by one week using the most recent actual/forecast
        new_rows = latest.copy()
        new_rows["week"] = wk
        new_rows["month"] = wk.month
        new_rows["season"] = {12:0,1:0,2:0,3:1,4:1,5:1,6:2,7:2,8:2,9:3,10:3,11:3}[wk.month]
        new_rows["is_holiday"] = 0  # unknown for future; conservative default
        new_rows["promo_flag"] = 0

        g = working.groupby("sku_id")["units_sold"]
        hist_tail = working.sort_values("week").groupby("sku_id").tail(52)

        lag_map = {1: [], 2: [], 4: [], 8: [], 52: []}
        roll_mean4, roll_mean8, roll_std4 = [], [], []
        for sku_id in new_rows["sku_id"]:
            series = working[working["sku_id"] == sku_id].sort_values("week")["units_sold"].values
            for lag in [1, 2, 4, 8, 52]:
                lag_map[lag].append(series[-lag] if len(series) >= lag else np.nan)
            roll_mean4.append(series[-4:].mean() if len(series) >= 2 else np.nan)
            roll_mean8.append(series[-8:].mean() if len(series) >= 2 else np.nan)
            roll_std4.append(series[-4:].std() if len(series) >= 2 else np.nan)

        for lag in [1, 2, 4, 8, 52]:
            new_rows[f"lag_{lag}"] = lag_map[lag]
        new_rows["roll_mean_4"] = roll_mean4
        new_rows["roll_mean_8"] = roll_mean8
        new_rows["roll_std_4"] = roll_std4

        X = new_rows[FEATURES].fillna(0)
        pred = model.predict(X).clip(min=0)
        pred_lo = model_lo.predict(X).clip(min=0)
        pred_hi = model_hi.predict(X).clip(min=0)

        new_rows["units_sold"] = pred  # feed forecast back in as pseudo-actual
        new_rows["forecast"] = pred
        new_rows["forecast_lo"] = np.minimum(pred_lo, pred)
        new_rows["forecast_hi"] = np.maximum(pred_hi, pred)

        forecasts.append(new_rows[["sku_id", "week", "forecast", "forecast_lo", "forecast_hi"]].copy())
        working = pd.concat([working, new_rows], ignore_index=True)

    return pd.concat(forecasts, ignore_index=True)


def main():
    print("[1/4] Loading weekly panel...")
    weekly = load_weekly_panel()
    print(f"      {weekly['sku_id'].nunique()} SKUs x {weekly['week'].nunique()} weeks = {len(weekly):,} rows")

    print("[2/4] Running rolling-origin backtest (model vs seasonal-naive baseline)...")
    backtest = rolling_origin_backtest(weekly)
    backtest.to_csv("reports/backtest_results.csv", index=False)
    print(backtest.to_string(index=False))

    avg_wape_model = backtest["wape_model"].mean()
    avg_wape_baseline = backtest["wape_baseline"].mean()
    improvement = (avg_wape_baseline - avg_wape_model) / avg_wape_baseline * 100

    summary = {
        "avg_wape_model": round(float(avg_wape_model), 4),
        "avg_wape_baseline": round(float(avg_wape_baseline), 4),
        "improvement_pct": round(float(improvement), 1),
        "beats_baseline": bool(avg_wape_model < avg_wape_baseline),
        "n_folds": len(backtest),
        "horizon_weeks": HORIZON_WEEKS,
    }
    with open("reports/backtest_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=== BACKTEST SUMMARY ===")
    print(json.dumps(summary, indent=2))

    print("\n[3/4] Training final model on full history...")
    model, model_lo, model_hi, feat = train_final_model(weekly)
    model.booster_.save_model("data/processed/model_forecast.txt")

    print("[4/4] Generating 8-week-ahead forecast for all SKUs...")
    forecast = recursive_forecast(weekly, model, model_lo, model_hi)
    forecast.to_csv("data/processed/forecast.csv", index=False)
    print(f"      {len(forecast):,} forecast rows -> data/processed/forecast.csv")

    print("\nDone.")


if __name__ == "__main__":
    main()
