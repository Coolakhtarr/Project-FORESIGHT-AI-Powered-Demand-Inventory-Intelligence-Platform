"""
FORESIGHT — Planning Dashboard (D5)
======================================
Streamlit app for NorthBay Living's operations team.

Run locally:
    streamlit run app/streamlit_app.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# allow running from repo root or app/ dir
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "processed")
REPORTS_DIR = os.path.join(ROOT, "reports")

st.set_page_config(
    page_title="FORESIGHT — NorthBay Living",
    page_icon="📦",
    layout="wide",
)

QUADRANT_COLORS = {
    "Reorder Now": "#E74C3C",
    "Markdown / Clear": "#8E7CC3",
    "Watch / Volatile": "#F5B041",
    "Healthy": "#2ECC71",
}


@st.cache_data
def load_data():
    if not os.path.exists(os.path.join(DATA_DIR, "risk_scores.csv")):
        return None
    sales = pd.read_csv(os.path.join(DATA_DIR, "sales_daily.csv"), parse_dates=["date"])
    sku = pd.read_csv(os.path.join(DATA_DIR, "sku_master.csv"))
    forecast = pd.read_csv(os.path.join(DATA_DIR, "forecast.csv"), parse_dates=["week"])
    risk = pd.read_csv(os.path.join(DATA_DIR, "risk_scores.csv"))
    backtest_path = os.path.join(REPORTS_DIR, "backtest_summary.json")
    backtest = json.load(open(backtest_path)) if os.path.exists(backtest_path) else None
    return sales, sku, forecast, risk, backtest


def empty_state():
    st.title("📦 FORESIGHT — NorthBay Living")
    st.warning(
        "No processed data found yet. Run the pipeline first:\n\n"
        "```\npython src/pipeline.py\npython src/forecast.py\npython src/risk.py\n```"
    )


def main():
    data = load_data()
    if data is None:
        empty_state()
        return

    sales, sku, forecast, risk, backtest = data

    st.title("📦 FORESIGHT — Demand & Inventory Intelligence")
    st.caption("NorthBay Living · Planning Dashboard · powered by Project FORESIGHT")

    # ---------------- Sidebar filters ----------------
    st.sidebar.header("Filters")
    categories = ["All"] + sorted(sku["category"].unique().tolist())
    sel_category = st.sidebar.selectbox("Category", categories)

    sku_options = risk.merge(sku[["sku_id", "category"]], on="sku_id", how="left", suffixes=("", "_m"))
    if sel_category != "All":
        sku_options = sku_options[sku_options["category"] == sel_category]

    sku_display = ["All"] + [
        f"{row.sku_id} — {row.description[:35]}" for row in sku_options.itertuples()
    ]
    sel_sku_display = st.sidebar.selectbox("SKU", sku_display)
    sel_sku = sel_sku_display.split(" — ")[0] if sel_sku_display != "All" else None

    quadrant_filter = st.sidebar.multiselect(
        "Risk quadrant", options=list(QUADRANT_COLORS.keys()), default=list(QUADRANT_COLORS.keys())
    )

    # ---------------- Top KPI row ----------------
    filtered_risk = risk.copy()
    if sel_category != "All":
        cat_skus = sku[sku["category"] == sel_category]["sku_id"]
        filtered_risk = filtered_risk[filtered_risk["sku_id"].isin(cat_skus)]
    if sel_sku:
        filtered_risk = filtered_risk[filtered_risk["sku_id"].astype(str) == str(sel_sku)]
    filtered_risk = filtered_risk[filtered_risk["quadrant"].isin(quadrant_filter)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SKUs in view", len(filtered_risk))
    c2.metric("Revenue at risk (stockouts)", f"£{filtered_risk['revenue_at_risk'].sum():,.0f}")
    c3.metric("Capital locked (overstock)", f"£{filtered_risk['capital_locked'].sum():,.0f}")
    if backtest:
        c4.metric(
            "Forecast accuracy vs baseline",
            f"{backtest['improvement_pct']:.0f}% better WAPE",
            help=f"Model WAPE {backtest['avg_wape_model']:.2f} vs baseline WAPE {backtest['avg_wape_baseline']:.2f}, "
                 f"averaged over {backtest['n_folds']} rolling-origin backtest folds.",
        )

    st.divider()

    tab1, tab2, tab3 = st.tabs(["🎯 Reorder / Markdown Priorities", "📈 Forecast vs Actual", "🗺️ Decisioning Grid"])

    # ---------------- Tab 1: prioritised action list ----------------
    with tab1:
        st.subheader("Prioritised action list")
        st.caption("Sorted by total value at stake (£ revenue at risk + £ capital locked). This is the list ops should work top-down.")

        if filtered_risk.empty:
            st.info("No SKUs match the current filters.")
        else:
            display_df = filtered_risk[[
                "sku_id", "description", "category", "quadrant",
                "on_hand_units", "reorder_point", "forecast_8wk",
                "revenue_at_risk", "capital_locked", "value_at_stake",
                "recommended_action",
            ]].rename(columns={
                "sku_id": "SKU", "description": "Product", "category": "Category",
                "quadrant": "Status", "on_hand_units": "On hand", "reorder_point": "Reorder pt",
                "forecast_8wk": "8-wk forecast", "revenue_at_risk": "Revenue at risk (£)",
                "capital_locked": "Capital locked (£)", "value_at_stake": "Value at stake (£)",
                "recommended_action": "Recommended action",
            })
            st.dataframe(
                display_df.style.format({
                    "8-wk forecast": "{:.0f}",
                    "Revenue at risk (£)": "£{:,.0f}",
                    "Capital locked (£)": "£{:,.0f}",
                    "Value at stake (£)": "£{:,.0f}",
                }),
                use_container_width=True,
                hide_index=True,
                height=500,
            )

    # ---------------- Tab 2: forecast vs actual ----------------
    with tab2:
        st.subheader("Demand: actual history vs forecast")
        if sel_sku:
            plot_sku = sel_sku
        else:
            plot_sku = str(filtered_risk.iloc[0]["sku_id"]) if not filtered_risk.empty else str(risk.iloc[0]["sku_id"])

        st.caption(f"Showing SKU {plot_sku}. Use the sidebar to pick a specific SKU.")

        hist = sales[sales["sku_id"].astype(str) == str(plot_sku)].copy()
        hist["week"] = hist["date"].dt.to_period("W-SUN").dt.start_time
        hist_weekly = hist.groupby("week")["units_sold"].sum().reset_index()

        fc = forecast[forecast["sku_id"].astype(str) == str(plot_sku)].sort_values("week")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist_weekly["week"], y=hist_weekly["units_sold"],
            mode="lines", name="Actual demand", line=dict(color="#2C3E50"),
        ))
        if not fc.empty:
            fig.add_trace(go.Scatter(
                x=fc["week"], y=fc["forecast"],
                mode="lines", name="Forecast", line=dict(color="#4B3FA6"),
            ))
            fig.add_trace(go.Scatter(
                x=pd.concat([fc["week"], fc["week"][::-1]]),
                y=pd.concat([fc["forecast_hi"], fc["forecast_lo"][::-1]]),
                fill="toself", fillcolor="rgba(75,63,166,0.15)",
                line=dict(color="rgba(255,255,255,0)"), name="80% interval",
                showlegend=True,
            ))
        fig.update_layout(
            height=450, xaxis_title="Week", yaxis_title="Units / week",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ---------------- Tab 3: decisioning grid ----------------
    with tab3:
        st.subheader("Stockout vs overstock risk — every SKU at a glance")
        st.caption("Bubble size = value at stake (£). Use this to triage the whole catalog in one view.")

        plot_df = filtered_risk.copy()
        if plot_df.empty:
            st.info("No SKUs match the current filters.")
        else:
            fig2 = px.scatter(
                plot_df, x="overstock_risk", y="stockout_risk",
                size="value_at_stake", color="quadrant",
                color_discrete_map=QUADRANT_COLORS,
                hover_data=["sku_id", "description", "value_at_stake"],
                labels={"overstock_risk": "Overstock risk →", "stockout_risk": "Stockout risk →"},
                height=550,
            )
            fig2.add_hline(y=0.5, line_dash="dot", line_color="grey")
            fig2.add_vline(x=0.5, line_dash="dot", line_color="grey")
            fig2.update_xaxes(range=[-0.05, 1.05])
            fig2.update_yaxes(range=[-0.05, 1.05])
            st.plotly_chart(fig2, use_container_width=True)


if __name__ == "__main__":
    main()
