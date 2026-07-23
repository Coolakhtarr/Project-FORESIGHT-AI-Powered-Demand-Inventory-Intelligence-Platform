"""
FORESIGHT — Scoring Service (D6)
===================================
Returns forecast + risk for a given SKU (or a batch), built on the
outputs of src/pipeline.py -> src/forecast.py -> src/risk.py.

Run locally:
    uvicorn service.main:app --reload --port 8000

Then:
    GET  /
    GET  /sku/{sku_id}
    POST /batch          body: {"sku_ids": ["85123A", "22423"]}
"""

import os
from typing import List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "processed")

app = FastAPI(
    title="FORESIGHT Scoring Service",
    description="Returns 8-week demand forecast and stockout/overstock risk for NorthBay Living SKUs.",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

_risk_df: Optional[pd.DataFrame] = None
_forecast_df: Optional[pd.DataFrame] = None


def _load():
    global _risk_df, _forecast_df
    risk_path = os.path.join(DATA_DIR, "risk_scores.csv")
    forecast_path = os.path.join(DATA_DIR, "forecast.csv")
    if not os.path.exists(risk_path) or not os.path.exists(forecast_path):
        _risk_df, _forecast_df = None, None
        return
    _risk_df = pd.read_csv(risk_path)
    _risk_df["sku_id"] = _risk_df["sku_id"].astype(str)
    _forecast_df = pd.read_csv(forecast_path, parse_dates=["week"])
    _forecast_df["sku_id"] = _forecast_df["sku_id"].astype(str)


_load()


class BatchRequest(BaseModel):
    sku_ids: List[str]


def _sku_response(sku_id: str):
    if _risk_df is None:
        raise HTTPException(status_code=503, detail="Data not loaded. Run the pipeline first.")

    sku_id = str(sku_id)
    risk_row = _risk_df[_risk_df["sku_id"] == sku_id]
    if risk_row.empty:
        raise HTTPException(status_code=404, detail=f"SKU '{sku_id}' not found.")
    risk_row = risk_row.iloc[0]

    fc = _forecast_df[_forecast_df["sku_id"] == sku_id].sort_values("week")
    forecast_weeks = [
        {
            "week": row.week.date().isoformat(),
            "forecast": round(float(row.forecast), 1),
            "forecast_lo": round(float(row.forecast_lo), 1),
            "forecast_hi": round(float(row.forecast_hi), 1),
        }
        for row in fc.itertuples()
    ]

    return {
        "sku_id": sku_id,
        "description": risk_row["description"],
        "category": risk_row["category"],
        "forecast": forecast_weeks,
        "risk": {
            "quadrant": risk_row["quadrant"],
            "stockout_risk": round(float(risk_row["stockout_risk"]), 3),
            "overstock_risk": round(float(risk_row["overstock_risk"]), 3),
            "revenue_at_risk_gbp": float(risk_row["revenue_at_risk"]),
            "capital_locked_gbp": float(risk_row["capital_locked"]),
            "recommended_action": risk_row["recommended_action"],
        },
        "inventory": {
            "on_hand_units": int(risk_row["on_hand_units"]),
            "on_order_units": int(risk_row["on_order_units"]),
            "lead_time_days": int(risk_row["lead_time_days"]),
            "reorder_point": int(risk_row["reorder_point"]),
        },
    }


@app.get("/")
def root():
    return {
        "service": "FORESIGHT Scoring Service",
        "status": "ok" if _risk_df is not None else "no data loaded — run the pipeline",
        "n_skus": int(len(_risk_df)) if _risk_df is not None else 0,
        "endpoints": ["/sku/{sku_id}", "POST /batch"],
    }


@app.get("/sku/{sku_id}")
def get_sku(sku_id: str):
    """Returns forecast + risk for a single SKU. Handles unknown SKUs gracefully (404, not a crash)."""
    return _sku_response(sku_id)


@app.post("/batch")
def get_batch(req: BatchRequest):
    """Returns forecast + risk for a batch of SKUs. Skips unknown SKUs rather than failing the whole request."""
    if _risk_df is None:
        raise HTTPException(status_code=503, detail="Data not loaded. Run the pipeline first.")
    results, not_found = [], []
    for sku_id in req.sku_ids:
        try:
            results.append(_sku_response(sku_id))
        except HTTPException:
            not_found.append(sku_id)
    return {"results": results, "not_found": not_found}
