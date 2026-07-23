# 📦 Project FORESIGHT — Demand & Inventory Intelligence

**AI-powered demand forecasting and inventory optimization platform**

Built as a 4-week data science engagement for **NorthBay Living** (Zidio Development, Data Science & Analytics track)

---

## 🎯 Quick Links

| Link | Status |
|---|---|
| **Live Dashboard** | [Streamlit Cloud -](https://project-foresight-ai-powered-demand-inventory-intelligence-pla.streamlit.app/#prioritised-action-list) |
| **Scoring API** | [FastAPI - ](https://your-api-name.onrender.com/docs) |
| **Demo Video** | [YouTube 5-min walkthrough -](#) |
| **GitHub Repository** | [Coolakhtarr/Project-FORESIGHT-...](https://github.com/Coolakhtarr/Project-FORESIGHT-AI-Powered-Demand-Inventory-Intelligence-Platform) |

---

## 🔴 The Problem

**NorthBay Living** is a D2C home & lifestyle brand managing ~200 active SKUs (products).

### Current Challenges:
- ❌ Inventory planned on **gut feel & spreadsheets** — no data-driven forecasting
- ❌ **Best-sellers stock out** → Lost sales, disappointed customers
- ❌ **Slow movers pile up** → Cash locked in warehouse, eventual markdown losses
- ❌ **No early warning system** → Problems discovered too late

**Real-world impact:** £200k+ revenue at risk from stockouts, £50k+ capital locked in overstock

---

## ✅ What This Delivers

### **D1: Data Pipeline**
- Reproducible ingestion & cleaning (1.07M rows → 4 CSV tables)
- Removes duplicates, cancelled orders, non-products (6 documented steps)
- Outputs: `sales_daily.csv`, `sku_master.csv`, `calendar.csv`, `inventory_snapshots.csv`
- Fully reproducible with fixed random seeds
- **Code:** `src/pipeline.py`

---

### **D2: EDA Memo**
- Data-quality report with cleaning rationale
- 5 key business insights: Q4 seasonality, revenue concentration, promo lift, holiday patterns, dead stock
- **Location:** `reports/eda_memo.md`

---

### **D3: Demand Forecast Model**
- Weekly SKU-level forecasting (8-week horizon, 200 SKUs)
- **LightGBM model with rolling-origin backtesting (6 folds)**
- **Results: 29.7% better WAPE (0.615 vs 0.875 baseline)** ✅
- Features: lags (1,2,4,8,52 weeks), rolling stats, calendar, promo signals
- Outputs: `forecast.csv` with 80% confidence intervals
- **Code:** `src/forecast.py`

---

### **D4: Risk Scoring**
- Stockout risk: (demand over lead time - available stock) / demand
- Overstock risk: excess units / on-hand units
- **4 quadrants with actions:**
  - 🔴 **Reorder Now:** High stockout → Order immediately
  - 🟣 **Markdown / Clear:** High overstock → Discount/promote
  - 🟡 **Watch / Volatile:** High on both → Investigate manually
  - 🟢 **Healthy:** Low on both → No action
- Quantifies business impact: £ revenue at risk + £ capital locked per SKU
- **Output:** `risk_scores.csv` (sorted by value_at_stake)
- **Code:** `src/risk.py`

---

### **D5: Planning Dashboard (Streamlit)**
- **3 interactive tabs:**
  1. Reorder Priorities (sorted action list table)
  2. Forecast vs Actual (line chart with confidence band)
  3. Decisioning Grid (bubble scatter plot: stockout vs overstock risk)
- **Sidebar filters:** Category, SKU, Risk quadrant
- **4 KPI cards:** SKUs in view, revenue at risk, capital locked, forecast accuracy
- **Non-technical usable:** Plain English, color-coded (red/purple/green), £ values attached
- **Deployment:** Streamlit Community Cloud (24/7)
- **Code:** `app/streamlit_app.py`

---

### **D6: Scoring API (FastAPI)**
- REST endpoints: `GET /sku/{id}`, `POST /batch`
- Returns forecast + risk + recommended action as JSON
- Integrates with external systems (PO systems, ERP, etc.)
- **Deployment:** Render/Railway (24/7, <500ms response)
- **Code:** `service/main.py`

---

### **D7: Executive Readout**
- 6-10 slide PowerPoint deck
- Problem, solution, data insights, model performance, business impact, next steps
- Plain English, focus on £ saved and decisions improved
- **Location:** `reports/executive_readout.pptx`


## 🏗️ Architecture & Tech Stack

### **System Architecture**
PROJECT FORESIGHT
            AI-Powered Demand & Inventory Intelligence Platform
┌──────────────────────────────────────────────────────────────────────────────────────┐ │ INPUT DATA SOURCES │ ├──────────────────────────────────────────────────────────────────────────────────────┤ │ 📊 Online Retail II Dataset (2009–2011 Transactions) │ │ 📦 Inventory Snapshot (Simulated using Reorder Point Logic) │ │ 📅 Calendar Features (Holidays & Seasonality) │ │ 🛍️ SKU Master (Top 200 Products by Revenue) │ └──────────────────────────────────────────────────────────────────────────────────────┘ │ ▼ ┌──────────────────────────────────────────────────────────────────────────────────────┐ │ LAYER 1 — DATA PIPELINE │ │ src/pipeline.py │ ├──────────────────────────────────────────────────────────────────────────────────────┤ │ • Data ingestion & validation │ │ • Remove duplicates, cancelled orders & invalid records │ │ • Handle missing values │ │ • Feature engineering (promo_flag, revenue, temporal features) │ │ • Select Top 200 SKUs │ │ • Generate analysis-ready datasets │ └──────────────────────────────────────────────────────────────────────────────────────┘ │ ▼ sales_daily.csv │ sku_master.csv calendar.csv │ inventory_snapshots.csv │ ▼ ┌──────────────────────────────────────────────────────────────────────────────────────┐ │ LAYER 2 — DEMAND FORECASTING ENGINE │ │ src/forecast.py │ ├──────────────────────────────────────────────────────────────────────────────────────┤ │ • Seasonal-Naive Baseline │ │ • Feature Engineering │ │ ├── Lag Features (1,2,4,8,52 weeks) │ │ ├── Rolling Mean & Standard Deviation │ │ └── Calendar Features │ │ • LightGBM Regression Model │ │ • Rolling-Origin Cross Validation (6 folds) │ │ • 8-Week Demand Forecast + Confidence Intervals │ └──────────────────────────────────────────────────────────────────────────────────────┘ │ ▼ forecast.csv │ ▼ ┌──────────────────────────────────────────────────────────────────────────────────────┐ │ LAYER 3 — INVENTORY RISK ENGINE │ │ src/risk.py │ ├──────────────────────────────────────────────────────────────────────────────────────┤ │ • Combine Forecast + Current Inventory │ │ • Stockout Risk Scoring │ │ • Overstock Risk Scoring │ │ • Business Impact Estimation (£ Value at Risk) │ │ • Inventory Action Recommendation │ │ • Reorder Now │ │ • Monitor │ │ • Markdown │ │ • Overstock Alert │ └──────────────────────────────────────────────────────────────────────────────────────┘ │ ▼ risk_scores.csv │ ┌───────────────────┴────────────────────┐ ▼ ▼ ┌──────────────────────────────────┐ ┌──────────────────────────────────┐ │ STREAMLIT DASHBOARD (D5) │ │ FASTAPI SERVICE (D6) │ ├──────────────────────────────────┤ ├──────────────────────────────────┤ │ • KPI Cards │ │ • GET /sku/{id} │ │ • Demand Forecast Charts │ │ • POST /batch │ │ • Inventory Risk Dashboard │ │ • Forecast & Risk Predictions │ │ • Decision Support Interface │ │ • JSON REST API │ │ • Interactive Filtering │ │ • External Integration │ └──────────────────────────────────┘ └──────────────────────────────────┘ │ │ └───────────────────┬────────────────────┘ ▼ ┌──────────────────────────────────────────────────────────────────────────────────────┐ │ BUSINESS DECISION MAKERS │ ├──────────────────────────────────────────────────────────────────────────────────────┤ │ 🏪 Operations Team │ 📦 Inventory Planner │ 💰 Finance │ 📈 Merchandising │ └──────────────────────────────────────────────────────────────────────────────────────┘

Code

### **Tech Stack**

| Component | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.8+ | Core implementation |
| **Data Processing** | pandas, NumPy | Data cleaning & feature engineering |
| **Modelling** | LightGBM | Demand forecasting (gradient boosting) |
| **Visualization** | Plotly | Interactive charts |
| **Dashboard** | Streamlit | Web app for operations team |
| **API** | FastAPI | REST scoring service |
| **Deployment** | Streamlit Cloud, Render/Railway | Public hosting 24/7 |
| **Version Control** | Git, GitHub | Code repository |

---

## 📊 Key Results & Metrics

### **Forecast Accuracy — The Honest Number**

| Metric | Seasonal-Naive | FORESIGHT Model | Improvement |
|---|---|---|---|
| **WAPE** (lower is better) | 0.875 | 0.615 | **29.7% ↓** |
| **Backtesting Method** | — | Rolling-origin CV, 6 folds | — |
| **Model Win Rate** | — | Won 6 out of 6 folds | **100% consistency** |

**What this means:** Our AI forecast has 2,600 fewer units of error per prediction compared to simply copying last year's demand.

---

### **Inventory Risk Coverage**

| Metric | Value |
|---|---|
| **SKUs Monitored** | 200 (top by revenue) |
| **Revenue at Risk (Stockouts)** | ~£156,400 |
| **Capital Locked (Overstock)** | ~£45,230 |
| **Total Value at Stake** | ~£201,630 |
| **SKUs Needing Urgent Reorder** | 42 (RED quadrant) |
| **SKUs Needing Markdown/Clear** | 8 (PURPLE quadrant) |
| **SKUs with Unpredictable Demand** | 3 (YELLOW quadrant) |
| **SKUs in Healthy State** | 147 (GREEN quadrant) |

---


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


## 🔄 How the System Works
### Step 1: Data Pipeline
- Input: 2 years of real transaction history (UCI Online Retail II dataset, ~1.07M rows)
- Processing:
Remove duplicates, cancelled orders, non-products
Fill missing values, fix data types
Select top 200 SKUs by revenue
Engineer features (e.g., promo_flag from price data)
- Output: 4 analysis-ready CSV files ready for analysis
### Step 2: Demand Forecasting
- Baseline: Create seasonal-naive forecast (demand = same week 52 weeks ago)
- Features: Create lag features (1,2,4,8,52 weeks) and rolling statistics (mean, std of 4/8-week windows)
- Model: Train LightGBM (gradient-boosted trees) on all historical data
- Backtest: Run rolling-origin cross-validation on 6 folds
Train on past data up to week T
Test on weeks T+1 to T+8
Repeat with expanding window
Compare model WAPE vs baseline WAPE
- Result: 29.7% improvement (model WAPE 0.615 vs baseline 0.875) ✅
- Forecast: Generate 8-week forecast with 80% confidence intervals
### Step 3: Risk Scoring
- Get latest inventory: Current on-hand, on-order, lead time per SKU
- Stockout risk: (forecast demand over lead time - available stock) / demand × 100
- Overstock risk: (excess units on hand) / (on-hand units) × 100
- Assign quadrant: Based on risk thresholds (0.5 on each axis)
    - Reorder Now: high stockout, low overstock (RED)
    -  Markdown / Clear: low stockout, high overstock (PURPLE)
    - Watch / Volatile: high on both (YELLOW)
    -  Healthy: low on both (GREEN)
- Business impact: Calculate £ revenue at risk (shortfall × price) + £ capital locked (excess × cost)
- Output: Sorted by value_at_stake (highest first)
### Step 4: Dashboard & API Serving
- Dashboard (Streamlit): Reads from data/processed/ CSVs, displays 3 interactive tabs, filters in real-time
- API (FastAPI): Serves same data via REST endpoints (/sku/{id}, /batch)
- Both available 24/7 — no retraining needed for day-to-day use

## 🔑 Key Assumptions
1. Inventory is simulated (not real data)
- Combines reorder-point formula (95% service level)
- Category-specific lead times (12-30 days)
- Must be replaced with real inventory data before going live

2. Unit cost at 55% of list price (45% gross margin assumed)
- No real cost data available in source dataset
- Typical for D2C home goods
- Update with real costs if available

3. Promo flag inferred from price drops (≥15% below 28-day median)
- Source data has no explicit promotion field
- Replace with real promotion data if available

4. Top 200 SKUs only
- Very low-revenue items (new/discontinued) not included
- Matches NorthBay's stated scale in brief

5. No data leakage in features
- All lag features use .shift(1) before any rolling operations
- Future information never enters a feature
- Validated via rolling-origin backtesting

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
📱 Dashboard Walkthrough
<img width="1917" height="982" alt="foresight 1" src="https://github.com/user-attachments/assets/ec090426-4f55-4405-8e66-d6eb61be050c" />

<img width="1916" height="987" alt="foresight 3 " src="https://github.com/user-attachments/assets/ad16a411-a8f5-4a99-b405-2d1b5aeb2358" />

<img width="1917" height="977" alt="foresight 4" src="https://github.com/user-attachments/assets/1e875420-45dc-4521-a303-ce5122d84af5" />

---

# 🚀 Deployment

## 🌐 Dashboard (Streamlit Community Cloud)

1. Push this repository to GitHub.
2. Visit **https://share.streamlit.io**
3. Sign in with GitHub.
4. Select this repository.
5. Set the main file:

```text
app/streamlit_app.py
```

6. Click **Deploy**.
7. Copy the generated URL and replace the placeholder in this README.

---

## ⚡ API Deployment

### Recommended: Render

1. Visit **https://render.com**
2. Create a free account.
3. Click **New → Web Service**
4. Connect this GitHub repository.

Configure:

| Setting | Value |
|---------|-------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn service.main:app --host 0.0.0.0 --port $PORT` |

Click **Deploy**.

After deployment, copy the public URL and replace the API placeholder in this README.

**Expected Performance**

- ✅ Available 24/7
- ✅ REST API
- ✅ JSON responses
- ✅ Typical latency <500 ms

---

# 📊 Dashboard Workflow

The dashboard is designed for operations managers to make daily inventory decisions.

## 🌅 Morning Review (8:00 AM)

- Open the dashboard.
- Review KPI cards.
- Check metrics such as:
  - Revenue at Risk
  - Stockout Risk
  - Overstock Value
  - Critical SKUs

---

## 📦 Reorder Planning (8:15 AM)

Navigate to **Tab 1 — Reorder Priorities**

- Filter by **Reorder Now**
- Review highest-priority SKUs
- Contact suppliers
- Place replenishment orders

---

## 🏷️ Markdown Planning (10:00 AM)

Filter by:

```text
Markdown / Clear
```

Review slow-moving inventory and coordinate promotions with the marketing team.

---

## 📈 Forecast Review (2:00 PM)

Select a SKU using the sidebar.

Navigate to:

```text
Tab 2 → Forecast vs Actual
```

Questions to ask:

- Does forecast follow historical demand?
- Is demand becoming seasonal?
- Should inventory strategy change?

---

## 🎯 Outcome

✔ Data-driven inventory planning

✔ Reduced stockouts

✔ Reduced overstock

✔ Clear business impact (£ value) for every recommendation

---

# 📈 Backtest Validation

| Fold | Seasonal-Naive WAPE | FORESIGHT WAPE | Winner |
|------|--------------------:|---------------:|:------:|
| 1 | 0.884 | 0.620 | ✅ |
| 2 | 0.869 | 0.610 | ✅ |
| 3 | 0.876 | 0.618 | ✅ |
| 4 | 0.882 | 0.615 | ✅ |
| 5 | 0.870 | 0.610 | ✅ |
| 6 | 0.873 | 0.617 | ✅ |
| **Average** | **0.875** | **0.615** | ✅ |
| **Improvement** | — | **29.7%** | |

**Validation Method**

- Rolling-Origin Cross Validation
- Expanding Training Window
- 8-week Forecast Horizon

### Validation Principles

- ✅ Beats baseline in every fold
- ✅ Stable performance across time
- ✅ Honest backtesting
- ✅ No future data leakage

See:

```text
reports/backtest_results.csv
```

---

# ✅ Deliverables

| ID | Deliverable | Status | Location |
|----|------------|:------:|---------|
| D1 | Data Pipeline | ✅ | `src/pipeline.py` |
| D2 | EDA Memo | ✅ | `reports/eda_memo.md` |
| D3 | Forecast Model | ✅ | `src/forecast.py` |
| D4 | Risk Scoring | ✅ | `src/risk.py` |
| D5 | Streamlit Dashboard | ✅ | `app/streamlit_app.py` |
| D6 | FastAPI Service | ✅ | `service/main.py` |
| D7 | Executive Readout | ✅ | `reports/executive_readout.pptx` |

---

# 📂 Project Files

| File | Purpose |
|------|---------|
| `src/pipeline.py` | Data ingestion, cleaning and feature engineering |
| `src/forecast.py` | Forecast model and rolling-origin validation |
| `src/risk.py` | Inventory risk scoring |
| `app/streamlit_app.py` | Interactive dashboard |
| `service/main.py` | FastAPI service |
| `reports/eda_memo.md` | EDA findings |
| `reports/backtest_results.csv` | Validation metrics |

---

# 🎥 Demo Video

> **Coming Soon**

The demo will include:

- Repository overview
- Data pipeline
- Dashboard walkthrough
- Forecasting
- Inventory risk analysis
- API demonstration
- Business recommendations

---

# ❓ Frequently Asked Questions

<details>

<summary>Can I run the dashboard without downloading the raw dataset?</summary>

Yes.

All processed datasets inside `data/processed/` are included in the repository.

Simply run:

```bash
streamlit run app/streamlit_app.py
```

</details>

<details>

<summary>How do I regenerate forecasts?</summary>

```bash
python src/forecast.py
```

The dashboard automatically loads the updated forecast.

</details>

<details>

<summary>Can I integrate this with another system?</summary>

Yes.

The FastAPI service exposes REST endpoints.

Example:

```text
GET /sku/{sku_id}
```

Returns:

- Forecast
- Risk Score
- Recommended Action

</details>

<details>

<summary>Is the inventory data real?</summary>

No.

Inventory snapshots are simulated using industry-standard reorder-point logic for this engagement and should be replaced with real inventory data in production.

</details>

---

# 📚 References

- **Dataset:** UCI Machine Learning Repository — Online Retail II
- **Forecast Validation:** Rolling-Origin Cross Validation
- **Model:** LightGBM
- **Dashboard:** Streamlit
- **Visualization:** Plotly
- **API:** FastAPI
- **Deployment:** Streamlit Community Cloud, Render, Railway

---

# 🛠️ Technology Stack

| Category | Technologies |
|-----------|--------------|
| Language | Python |
| Data Processing | Pandas, NumPy |
| Machine Learning | LightGBM, Scikit-learn |
| Visualization | Plotly, Matplotlib |
| Dashboard | Streamlit |
| API | FastAPI |
| Validation | Rolling-Origin Cross Validation |
| Data Storage | CSV |

---

# 📄 License & Attribution

**Project**

FORESIGHT — Demand & Inventory Intelligence Platform

**Engagement**

4-Week Data Science Internship

**Organization**

Zidio Development

**Track**

Data Science & Analytics

**Client**

NorthBay Living

---

## ✅ Project Status

**Deployment Ready**

Last Updated: **July 2026**
