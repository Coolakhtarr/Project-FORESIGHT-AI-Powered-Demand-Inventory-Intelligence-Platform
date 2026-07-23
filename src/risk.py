"""
FORESIGHT — Stockout / Overstock Risk Scoring (D4)
=====================================================
Combines the demand forecast with current inventory position to produce,
for every SKU, a risk level and a recommended action — transparent and
explainable, per the brief's Section 08.

Run:
    python src/risk.py
"""

import numpy as np
import pandas as pd

FORWARD_WINDOW_WEEKS = 8  # overstock evaluation window


def load_inputs():
    forecast = pd.read_csv("data/processed/forecast.csv", parse_dates=["week"])
    inventory = pd.read_csv("data/processed/inventory_snapshots.csv", parse_dates=["date"])
    sku_master = pd.read_csv("data/processed/sku_master.csv")
    return forecast, inventory, sku_master


def latest_inventory_position(inventory: pd.DataFrame) -> pd.DataFrame:
    """Most recent snapshot per SKU — the current stock position to plan from."""
    latest = (
        inventory.sort_values("date")
        .groupby("sku_id")
        .tail(1)
        .reset_index(drop=True)
    )
    return latest


def score_risk(forecast: pd.DataFrame, inventory: pd.DataFrame, sku_master: pd.DataFrame) -> pd.DataFrame:
    latest_inv = latest_inventory_position(inventory)

    # forecast demand per SKU over the full 8-week horizon
    fc_total = forecast.groupby("sku_id")["forecast"].sum().rename("forecast_8wk")
    fc_daily_avg = (fc_total / (FORWARD_WINDOW_WEEKS * 7)).rename("forecast_daily_avg")

    df = latest_inv.merge(fc_total, on="sku_id", how="left")
    df = df.merge(fc_daily_avg, on="sku_id", how="left")
    df = df.merge(sku_master[["sku_id", "description", "category", "unit_cost", "list_price"]],
                  on="sku_id", how="left")

    df["forecast_8wk"] = df["forecast_8wk"].fillna(0)
    df["forecast_daily_avg"] = df["forecast_daily_avg"].fillna(0)

    # --- Stockout risk ---
    # demand expected over the SKU's own replenishment lead time
    df["demand_over_leadtime"] = df["forecast_daily_avg"] * df["lead_time_days"]
    df["available_position"] = df["on_hand_units"] + df["on_order_units"]
    df["stockout_shortfall_units"] = (
        (df["demand_over_leadtime"] - df["available_position"]).clip(lower=0)
    )
    # normalised 0-1 score: shortfall as a share of lead-time demand
    df["stockout_risk"] = np.where(
        df["demand_over_leadtime"] > 0,
        (df["stockout_shortfall_units"] / df["demand_over_leadtime"]).clip(0, 1),
        0.0,
    )

    # --- Overstock risk ---
    df["overstock_excess_units"] = (df["on_hand_units"] - df["forecast_8wk"]).clip(lower=0)
    df["overstock_risk"] = np.where(
        df["on_hand_units"] > 0,
        (df["overstock_excess_units"] / df["on_hand_units"]).clip(0, 1),
        0.0,
    )

    # --- Rupee (here: GBP, matching source data currency) impact ---
    df["revenue_at_risk"] = (df["stockout_shortfall_units"] * df["list_price"]).round(2)
    df["capital_locked"] = (df["overstock_excess_units"] * df["unit_cost"]).round(2)

    # --- Quadrant / decisioning ---
    def quadrant(row):
        high_stockout = row["stockout_risk"] >= 0.5
        high_overstock = row["overstock_risk"] >= 0.5
        if high_stockout and high_overstock:
            return "Watch / Volatile"
        if high_stockout:
            return "Reorder Now"
        if high_overstock:
            return "Markdown / Clear"
        return "Healthy"

    ACTION_MAP = {
        "Reorder Now": "Raise a replenishment order before stock runs out.",
        "Markdown / Clear": "Promote or discount to free up capital.",
        "Watch / Volatile": "Investigate — demand is erratic; review manually.",
        "Healthy": "No action needed; leave as is.",
    }

    df["quadrant"] = df.apply(quadrant, axis=1)
    df["recommended_action"] = df["quadrant"].map(ACTION_MAP)
    df["value_at_stake"] = df["revenue_at_risk"] + df["capital_locked"]

    cols = [
        "sku_id", "description", "category",
        "on_hand_units", "on_order_units", "lead_time_days", "reorder_point",
        "forecast_daily_avg", "forecast_8wk", "demand_over_leadtime",
        "stockout_risk", "overstock_risk", "quadrant",
        "revenue_at_risk", "capital_locked", "value_at_stake",
        "recommended_action",
    ]
    return df[cols].sort_values("value_at_stake", ascending=False).reset_index(drop=True)


def main():
    print("[1/2] Loading forecast + inventory + SKU master...")
    forecast, inventory, sku_master = load_inputs()

    print("[2/2] Scoring stockout / overstock risk for every SKU...")
    risk = score_risk(forecast, inventory, sku_master)
    risk.to_csv("data/processed/risk_scores.csv", index=False)

    print(f"\n{len(risk)} SKUs scored -> data/processed/risk_scores.csv\n")
    print("Quadrant breakdown:")
    print(risk["quadrant"].value_counts())
    print()
    print(f"Total revenue at risk (stockouts): £{risk['revenue_at_risk'].sum():,.2f}")
    print(f"Total capital locked (overstock):  £{risk['capital_locked'].sum():,.2f}")
    print()
    print("Top 5 highest-priority SKUs (by value at stake):")
    print(risk[["sku_id", "description", "quadrant", "value_at_stake"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
