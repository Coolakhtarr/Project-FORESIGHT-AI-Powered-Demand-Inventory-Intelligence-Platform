# Project FORESIGHT — Demand & Inventory Intelligence

AI-powered demand forecasting and inventory risk platform, built for the
NorthBay Living engagement brief (Zidio Development, Data Science &
Analytics track).

**Live dashboard:** _[add your deployed Streamlit URL here]_
**Live scoring API:** _[add your deployed FastAPI URL here]_
**Demo video:** _[add your 3–5 min walkthrough link here]_

---

## The problem

NorthBay Living (a D2C home & lifestyle brand, ~200 active SKUs) plans
inventory on gut feel and spreadsheets. They lose money two ways at once:
best-sellers stock out (lost sales), slow movers pile up (locked capital,
eventual markdown losses).

## What this delivers

1. A weekly, SKU-level demand forecast that **beats a seasonal-naive
   baseline by 29.7% on WAPE**, honestly backtested with rolling-origin
   cross-validation.
2. Stockout / overstock risk scoring for every SKU, with a recommended
   action and £ value at stake.
3. A self-serve planning dashboard for the operations team.
4. A deployed scoring API returning forecast + risk for any SKU.

## Data

**Source:** the public UCI *Online Retail II* dataset — real UK online
retailer transactions, Dec 2009 – Dec 2011 (~1.07M rows). Used in place of
a proprietary NorthBay extract because it provides genuine, sufficiently
long transaction history for real seasonality analysis and honest
backtesting.

> **Raw data file note:** `data/raw/online_retail_II.xlsx` (44MB) is not
> committed to this repository — GitHub's web upload UI caps individual
> files at 25MB (git push via command line allows up to 100MB, so this
> only affects drag-and-drop uploads). Download it directly from the
> [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
> or [Kaggle](https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci)
> and place it at `data/raw/online_retail_II.xlsx` before running
> `python src/pipeline.py`. All processed outputs (`data/processed/*.csv`)
> **are** committed, so the dashboard, API, forecast, and risk scoring all
> run immediately without needing the raw file at all.

**Important, stated plainly:** the source data has no inventory records.
`inventory_snapshots` (stock levels, lead time, reorder point) is
**simulated** using a standard reorder-point formula (95% service level,
category-specific lead times). This is a documented modelling assumption —
see `reports/eda_memo.md` §1 for the exact method — and should be replaced
with NorthBay's real inventory feed before this system drives live
purchase orders. It does not affect the demand model, which trains
entirely on real transaction history.

The catalog was narrowed to the **top 200 SKUs by revenue**, matching the
brief's stated NorthBay scale.

## Setup & run (reproduces end-to-end from raw data)

```bash
git clone <your-repo-url>
cd foresight
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1. Clean raw data -> the 4 analysis-ready tables
python src/pipeline.py

# 2. Backtest + train the forecast model + generate the 8-week forecast
python src/forecast.py

# 3. Score stockout/overstock risk for every SKU
python src/risk.py

# 4. Launch the dashboard
streamlit run app/streamlit_app.py

# 5. Launch the scoring API (separate terminal)
uvicorn service.main:app --reload --port 8000
```

Random seeds are fixed throughout (`RANDOM_SEED = 42`) so results are
reproducible run to run.

## Backtest result (the honest number)

| | WAPE (lower is better) |
|---|---|
| Seasonal-naive baseline | 0.875 |
| FORESIGHT model (LightGBM) | 0.615 |
| **Improvement** | **29.7%** |

Averaged over 6 rolling-origin backtest folds, 8-week horizon each. Full
fold-by-fold results: `reports/backtest_results.csv`. Methodology: expanding
training window, strict past-only features (verified no future data enters
any lag/rolling feature), reported honestly whether the model won or lost
each fold — it won every fold.

## Key assumptions

- Inventory positions (`inventory_snapshots`) are simulated — see above.
- `unit_cost` assumed at 55% of list price (45% gross margin) — no real
  cost data available in the source.
- `promo_flag` inferred from price drops ≥15% below a SKU's trailing
  28-day median price — the source data has no explicit promotion field.
- Catalog restricted to the top 200 SKUs by revenue to match the brief's
  stated NorthBay scale.

Full rationale for every decision: `reports/eda_memo.md`.

## Repository structure

```
foresight/
├── data/
│   ├── raw/              # original Online Retail II extract
│   └── processed/        # sales_daily, sku_master, calendar,
│                          # inventory_snapshots, forecast, risk_scores
├── src/
│   ├── pipeline.py        # D1 — ingest, clean, build 4 tables
│   ├── forecast.py        # D3 — baseline, features, model, backtest
│   └── risk.py             # D4 — stockout/overstock risk scoring
├── app/
│   └── streamlit_app.py   # D5 — planning dashboard
├── service/
│   └── main.py             # D6 — FastAPI scoring service
├── reports/
│   ├── eda_memo.md              # D2 — data-quality & EDA memo
│   ├── executive_readout.pptx   # D7 — executive readout deck
│   ├── backtest_results.csv     # fold-by-fold backtest numbers
│   ├── backtest_summary.json
│   └── figures/                 # EDA charts
├── requirements.txt
└── README.md
```

## Deployment notes

- **Dashboard**: deploy `app/streamlit_app.py` on Streamlit Community Cloud
  — point it at this repo, set the main file path, done.
- **API**: deploy `service/main.py` on Render / Hugging Face Spaces /
  Railway with start command `uvicorn service.main:app --host 0.0.0.0 --port $PORT`.
- Both read from `data/processed/*.csv`, which must be committed to the
  repo (or regenerated by running the pipeline as part of the build step)
  for the deployed apps to have data.

## Scope

Built strictly to the brief's scope: SKU-level weekly demand forecasting,
stockout/overstock risk scoring, a planning dashboard, and a scoring API.
Explicitly out of scope (per the brief): live system integrations, price
optimization, real-time pipelines, automated purchase-order placement.
