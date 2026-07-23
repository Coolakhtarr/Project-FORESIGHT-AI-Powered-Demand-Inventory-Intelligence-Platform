"""
FORESIGHT — Data Pipeline (D1)
================================
Ingests the raw Online Retail II transaction extract and produces four
analysis-ready tables matching the schema specified in the NorthBay Living
engagement brief:

    sales_daily         one row per SKU per day
    sku_master           one row per SKU
    calendar              one row per date
    inventory_snapshots   weekly stock position per SKU (SIMULATED — see note)

IMPORTANT — DATA PROVENANCE
----------------------------
The source data is the public UCI "Online Retail II" dataset (real UK-based
online retailer transactions, Dec 2009 - Dec 2011). It was used in place of
the official NorthBay extracts because it provides genuine transactional
history at sufficient volume and duration to support real seasonality
analysis and rolling-origin backtesting.

The source data contains NO inventory records (no stock levels, lead times,
or reorder points). The `inventory_snapshots` table is therefore SIMULATED
using industry-standard assumptions, documented in `build_inventory_snapshots()`
below and in reports/eda_memo.md. This is flagged explicitly rather than
silently presented as real inventory data.

Run:
    python src/pipeline.py
"""

import os
import numpy as np
import pandas as pd

RAW_XLSX = "data/raw/online_retail_II.xlsx"
OUT_DIR = "data/processed"
N_TOP_SKUS = 200  # matches brief's stated NorthBay scale: "~200 active SKUs"
RANDOM_SEED = 42

# Non-product StockCodes present in the raw extract (postage, fees, manual
# adjustments, bank charges, etc.) — these are not sellable SKUs and must be
# excluded before any demand analysis.
NON_PRODUCT_CODES = {
    "POST", "DOT", "M", "MANUAL", "BANK CHARGES", "PADS", "AMAZONFEE",
    "CRUK", "C2", "D", "S", "TEST001", "TEST002", "ADJUST", "ADJUST2",
    "gift_0001_10", "gift_0001_20", "gift_0001_30", "gift_0001_40",
    "gift_0001_50", "SAMPLES",
}


def load_raw() -> pd.DataFrame:
    """Ingest both sheets of the raw extract exactly as provided."""
    xl = pd.ExcelFile(RAW_XLSX)
    frames = [pd.read_excel(xl, sheet_name=s) for s in xl.sheet_names]
    df = pd.concat(frames, ignore_index=True)
    df["Invoice"] = df["Invoice"].astype(str)
    df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleaning decisions (documented per D1 acceptance criteria):

    1. Drop exact duplicate rows (34,335 found on profiling) — almost
       certainly re-exported/double-logged invoice lines.
    2. Exclude cancelled orders (Invoice starting with 'C') — these are
       refunds, not demand signal, and would distort unit sales if summed
       alongside positive-quantity purchases.
    3. Exclude non-positive Quantity or Price — remaining stray adjustment
       rows not caught by the cancellation flag.
    4. Exclude non-product StockCodes (postage, bank charges, manual entries).
    5. Fill missing Description using the most common description on record
       for that StockCode (a SKU's name is stable; a few rows had it blank).
    6. Drop rows where a StockCode has no description anywhere in the data
       (cannot be meaningfully classified into a SKU).
    """
    before = len(df)
    df = df.drop_duplicates()

    df = df[~df["Invoice"].str.startswith("C")]
    df = df[(df["Quantity"] > 0) & (df["Price"] > 0)]
    df = df[~df["StockCode"].isin(NON_PRODUCT_CODES)]

    desc_mode = (
        df.dropna(subset=["Description"])
        .groupby("StockCode")["Description"]
        .agg(lambda s: s.mode().iat[0] if not s.mode().empty else np.nan)
    )
    df["Description"] = df["StockCode"].map(desc_mode)
    df = df.dropna(subset=["Description"])

    after = len(df)
    print(f"[clean] {before:,} -> {after:,} rows ({before - after:,} removed)")
    return df


def select_top_skus(df: pd.DataFrame, n=N_TOP_SKUS) -> list:
    """
    Select the top-N SKUs by total revenue, matching the brief's stated
    NorthBay scale of ~200 active SKUs. Restricting scope also keeps the
    simulated inventory layer (Step below) computationally and narratively
    coherent — every modelled SKU has genuine, sufficient sales history.
    """
    df = df.copy()
    df["revenue"] = df["Quantity"] * df["Price"]
    top = df.groupby("StockCode")["revenue"].sum().sort_values(ascending=False)
    return top.head(n).index.tolist()


def build_sales_daily(df: pd.DataFrame, sku_ids: list) -> pd.DataFrame:
    """One row per SKU per day: units_sold, revenue, unit_price, promo_flag."""
    d = df[df["StockCode"].isin(sku_ids)].copy()
    d["date"] = d["InvoiceDate"].dt.date
    d["revenue"] = d["Quantity"] * d["Price"]

    daily = (
        d.groupby(["date", "StockCode"])
        .agg(units_sold=("Quantity", "sum"),
             revenue=("revenue", "sum"),
             unit_price=("Price", "mean"))
        .reset_index()
        .rename(columns={"StockCode": "sku_id"})
    )

    # Fill in zero-sales days so every SKU has a continuous daily series —
    # required for correct lag/rolling features and honest backtesting later.
    full_dates = pd.date_range(daily["date"].min(), daily["date"].max(), freq="D")
    idx = pd.MultiIndex.from_product([full_dates.date, sku_ids], names=["date", "sku_id"])
    daily = (
        daily.set_index(["date", "sku_id"])
        .reindex(idx)
        .reset_index()
    )
    daily["units_sold"] = daily["units_sold"].fillna(0).astype(int)
    daily["revenue"] = daily["revenue"].fillna(0.0)
    daily["unit_price"] = daily.groupby("sku_id")["unit_price"].transform(
        lambda s: s.ffill().bfill()
    )

    # promo_flag: heuristic — a day is flagged promotional if unit_price is
    # notably below that SKU's trailing 28-day median price (>=15% discount).
    # Documented assumption: the source data has no explicit promo field.
    daily = daily.sort_values(["sku_id", "date"])
    daily["price_baseline"] = (
        daily.groupby("sku_id")["unit_price"]
        .transform(lambda s: s.rolling(28, min_periods=7).median())
    )
    daily["promo_flag"] = (
        (daily["unit_price"] < 0.85 * daily["price_baseline"])
        & daily["price_baseline"].notna()
    ).astype(int)
    daily = daily.drop(columns=["price_baseline"])

    return daily.reset_index(drop=True)


def build_sku_master(df: pd.DataFrame, sku_ids: list) -> pd.DataFrame:
    """One row per SKU: category/subcategory, launch_date, unit_cost, list_price."""
    d = df[df["StockCode"].isin(sku_ids)].copy()

    KEYWORD_CATEGORY = [
        (["LIGHT", "LAMP", "CANDLE", "LANTERN"], "Lighting & Candles"),
        (["MUG", "CUP", "TEAPOT", "KITCHEN", "BOWL", "PLATE", "TIN"], "Kitchen & Dining"),
        (["BAG", "APRON", "PURSE"], "Bags & Accessories"),
        (["CARD", "GIFT", "WRAP", "PAPER"], "Cards & Gift Wrap"),
        (["FRAME", "SIGN", "DECOR", "HANGING", "HEART"], "Home Decor"),
        (["CHRISTMAS", "XMAS"], "Seasonal & Christmas"),
        (["BOX", "STORAGE"], "Storage"),
        (["GARDEN", "PLANT"], "Garden"),
        (["TOY", "GAME"], "Toys & Games"),
    ]

    def categorize(desc: str) -> str:
        desc_u = str(desc).upper()
        for keywords, cat in KEYWORD_CATEGORY:
            if any(k in desc_u for k in keywords):
                return cat
        return "General Home & Lifestyle"

    agg = (
        d.groupby("StockCode")
        .agg(
            description=("Description", lambda s: s.mode().iat[0]),
            launch_date=("InvoiceDate", "min"),
            list_price=("Price", "median"),
        )
        .reset_index()
        .rename(columns={"StockCode": "sku_id"})
    )
    agg["category"] = agg["description"].apply(categorize)
    agg["subcategory"] = agg["description"].str.split().str[0].str.title()
    # unit_cost assumption: documented — assume a 55% cost-of-goods ratio
    # (i.e. 45% gross margin), a reasonable D2C home-goods benchmark absent
    # real cost data.
    agg["unit_cost"] = (agg["list_price"] * 0.55).round(2)
    agg["launch_date"] = agg["launch_date"].dt.date

    return agg[["sku_id", "description", "category", "subcategory",
                "launch_date", "unit_cost", "list_price"]]


def build_calendar(sales_daily: pd.DataFrame) -> pd.DataFrame:
    """One row per date: week/month/season, holiday flag, promo_event."""
    dates = pd.to_datetime(sorted(sales_daily["date"].unique()))
    cal = pd.DataFrame({"date": dates})
    cal["week"] = cal["date"].dt.isocalendar().week
    cal["month"] = cal["date"].dt.month
    cal["season"] = cal["month"].map({
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Spring", 4: "Spring", 5: "Spring",
        6: "Summer", 7: "Summer", 8: "Summer",
        9: "Autumn", 10: "Autumn", 11: "Autumn",
    })

    # UK public holidays relevant to the source retailer, 2009-2011.
    uk_holidays = pd.to_datetime([
        "2009-12-25", "2009-12-26", "2010-01-01",
        "2010-04-02", "2010-04-05", "2010-05-03", "2010-05-31",
        "2010-08-30", "2010-12-25", "2010-12-27", "2010-12-28",
        "2011-01-01", "2011-01-03", "2011-04-22", "2011-04-25",
        "2011-04-29", "2011-05-02", "2011-05-30", "2011-08-29",
        "2011-12-25", "2011-12-26", "2011-12-27",
    ])
    cal["is_holiday"] = cal["date"].isin(uk_holidays).astype(int)

    # promo_event: named around known peak retail periods.
    def event(d):
        if d.month == 11 and d.day >= 24:
            return "Black Friday"
        if d.month == 12 and d.day <= 20:
            return "Christmas Run-up"
        if d.month == 1 and d.day <= 15:
            return "New Year Sale"
        return None

    cal["promo_event"] = cal["date"].apply(event)
    cal["date"] = cal["date"].dt.date
    return cal


def build_inventory_snapshots(sales_daily: pd.DataFrame, sku_master: pd.DataFrame) -> pd.DataFrame:
    """
    SIMULATED weekly inventory position per SKU.

    Documented assumptions (source data has no real inventory records):
      - lead_time_days: assigned by category (12-30 days), reflecting
        typical D2C replenishment lead times for imported home goods vs.
        faster-moving categories.
      - Starting stock: 4 weeks of trailing average demand (a common
        starting-cover heuristic).
      - Reorder point: (avg daily demand x lead_time_days) + safety stock,
        where safety stock = 1.65 x demand_std x sqrt(lead_time_days)
        (95% service level, standard reorder-point formula).
      - Simple discrete simulation: stock depletes with daily sales; when
        projected stock falls below the reorder point, a replenishment
        order is placed and arrives after lead_time_days, sized to bring
        stock back to a 6-week cover target.
      - Snapshots are recorded weekly (matching the brief's "periodic stock
        position" grain).
    """
    rng = np.random.default_rng(RANDOM_SEED)

    category_lead_time = {
        "Lighting & Candles": 18, "Kitchen & Dining": 21,
        "Bags & Accessories": 24, "Cards & Gift Wrap": 12,
        "Home Decor": 21, "Seasonal & Christmas": 30,
        "Storage": 21, "Garden": 24, "Toys & Games": 24,
        "General Home & Lifestyle": 18,
    }

    sd = sales_daily.copy()
    sd["date"] = pd.to_datetime(sd["date"])
    sku_cat = sku_master.set_index("sku_id")["category"].to_dict()

    records = []
    for sku_id, g in sd.groupby("sku_id"):
        g = g.sort_values("date").reset_index(drop=True)
        cat = sku_cat.get(sku_id, "General Home & Lifestyle")
        lead_time = category_lead_time.get(cat, 18)

        avg_demand = g["units_sold"].head(28).mean() or 1.0
        std_demand = g["units_sold"].head(28).std() or (avg_demand * 0.5)
        safety_stock = 1.65 * std_demand * np.sqrt(lead_time)
        reorder_point = round(avg_demand * lead_time + safety_stock)
        target_cover_units = round(avg_demand * 42)  # 6-week cover target

        on_hand = round(avg_demand * 28)
        on_order = 0
        pending_orders = []  # list of (arrival_day_idx, qty)

        for i, row in g.iterrows():
            # receive any orders arriving today
            arrived = [q for (day, q) in pending_orders if day == i]
            if arrived:
                on_hand += sum(arrived)
                on_order -= sum(arrived)
                pending_orders = [(d, q) for (d, q) in pending_orders if d != i]

            on_hand = max(0, on_hand - row["units_sold"])

            # place a reorder if projected position falls below reorder point
            projected_position = on_hand + on_order
            if projected_position < reorder_point:
                order_qty = max(0, target_cover_units - projected_position)
                if order_qty > 0:
                    pending_orders.append((i + lead_time, order_qty))
                    on_order += order_qty

            if i % 7 == 0:  # weekly snapshot
                records.append({
                    "date": row["date"].date(),
                    "sku_id": sku_id,
                    "on_hand_units": int(on_hand),
                    "on_order_units": int(on_order),
                    "lead_time_days": lead_time,
                    "reorder_point": int(reorder_point),
                })

    return pd.DataFrame(records)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print("[1/6] Loading raw extract...")
    raw = load_raw()
    print(f"      {len(raw):,} raw rows loaded")

    print("[2/6] Cleaning...")
    clean_df = clean(raw)

    print(f"[3/6] Selecting top {N_TOP_SKUS} SKUs by revenue...")
    sku_ids = select_top_skus(clean_df, N_TOP_SKUS)

    print("[4/6] Building sales_daily...")
    sales_daily = build_sales_daily(clean_df, sku_ids)
    sales_daily.to_csv(f"{OUT_DIR}/sales_daily.csv", index=False)
    print(f"      {len(sales_daily):,} rows -> {OUT_DIR}/sales_daily.csv")

    print("[5/6] Building sku_master and calendar...")
    sku_master = build_sku_master(clean_df, sku_ids)
    sku_master.to_csv(f"{OUT_DIR}/sku_master.csv", index=False)
    print(f"      {len(sku_master):,} rows -> {OUT_DIR}/sku_master.csv")

    calendar = build_calendar(sales_daily)
    calendar.to_csv(f"{OUT_DIR}/calendar.csv", index=False)
    print(f"      {len(calendar):,} rows -> {OUT_DIR}/calendar.csv")

    print("[6/6] Building inventory_snapshots (SIMULATED — see docstring)...")
    inventory = build_inventory_snapshots(sales_daily, sku_master)
    inventory.to_csv(f"{OUT_DIR}/inventory_snapshots.csv", index=False)
    print(f"      {len(inventory):,} rows -> {OUT_DIR}/inventory_snapshots.csv")

    print("\nPipeline complete. Analysis-ready dataset written to data/processed/")


if __name__ == "__main__":
    main()
