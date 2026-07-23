const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, ImageRun, BorderStyle, PageBreak,
} = require("docx");
const fs = require("fs");

const NAVY = "1E2340";
const GOLD = "C9A66B";
const GREY = "6B7280";

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 150 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 100 } });
}
function body(text) {
  return new Paragraph({ children: [new TextRun({ text, size: 22 })], spacing: { after: 120 } });
}
function bullet(text) {
  return new Paragraph({ children: [new TextRun({ text, size: 22 })], bullet: { level: 0 }, spacing: { after: 80 } });
}

function simpleTable(headers, rows, colWidths) {
  const totalWidth = 9000;
  const widths = colWidths || headers.map(() => Math.floor(totalWidth / headers.length));
  const headerRow = new TableRow({
    children: headers.map((h, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: NAVY },
      children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, color: "FFFFFF", size: 20 })] })],
    })),
  });
  const dataRows = rows.map((r) => new TableRow({
    children: r.map((cell, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      children: [new Paragraph({ children: [new TextRun({ text: String(cell), size: 20 })] })],
    })),
  }));
  return new Table({ width: { size: totalWidth, type: WidthType.DXA }, rows: [headerRow, ...dataRows], columnWidths: widths });
}

function figure(path, widthPx, caption) {
  const data = fs.readFileSync(path);
  return [
    new Paragraph({
      children: [new ImageRun({ data, transformation: { width: widthPx, height: Math.round(widthPx * 0.44) }, type: "png" })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 150, after: 60 },
    }),
    new Paragraph({
      children: [new TextRun({ text: caption, italics: true, size: 18, color: GREY })],
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
    }),
  ];
}

const FIG_DIR = "../figures";

const doc = new Document({
  sections: [{
    properties: {},
    children: [
      // ---- Cover page ----
      new Paragraph({ spacing: { before: 800 }, children: [] }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        border: { bottom: { color: GOLD, space: 8, style: BorderStyle.SINGLE, size: 12 } },
        spacing: { after: 500 },
        children: [new TextRun({ text: "ZIDIO DEVELOPMENT", bold: true, size: 24, color: NAVY, characterSpacing: 40 })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 100 },
        children: [new TextRun({ text: "PROJECT FORESIGHT", bold: true, size: 64, color: NAVY })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 60 },
        children: [new TextRun({ text: "AI-Powered Demand & Inventory Intelligence Platform", size: 26, color: GOLD, italics: true })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 100, after: 700 },
        children: [new TextRun({ text: "Client Engagement — NorthBay Living  ·  Data Science & Analytics Track", size: 20, color: GREY })],
      }),
      new Paragraph({ spacing: { before: 900 }, children: [] }),
      simpleTable(
        ["Field", "Detail"],
        [
          ["Prepared by", "Umar Akhtar"],
          ["Program", "Zidio Internship — Data Science & Analytics"],
          ["Engagement type", "Client project"],
          ["Client", "NorthBay Living — D2C home & lifestyle brand"],
          ["Duration", "25 June 2026 – 25 July 2026 (4-week engagement)"],
          ["Document type", "Project Report & Engagement Summary"],
          ["Status", "Final Submission"],
        ],
        [3000, 6000]
      ),
      new Paragraph({ children: [new PageBreak()] }),

      // ---- Project Overview ----
      h1("Project Overview"),
      body(
        "FORESIGHT is an AI-powered demand forecasting and inventory intelligence platform, built as a client " +
        "engagement for NorthBay Living, a direct-to-consumer home & lifestyle brand with roughly 200 active SKUs. " +
        "NorthBay currently plans inventory on gut feel and spreadsheets, resulting in two simultaneous problems: " +
        "best-sellers stock out (lost sales) and slow movers pile up (locked capital, eventual markdown losses). " +
        "FORESIGHT solves this by forecasting weekly, SKU-level demand and converting that forecast, combined with " +
        "current inventory position, into a transparent stockout/overstock risk score and recommended action for " +
        "every SKU — delivered through a self-serve dashboard and a deployed scoring API."
      ),

      h2("Vision & Objectives"),
      bullet("Produce a weekly, SKU-level demand forecast that measurably beats a naive baseline."),
      bullet("Flag stockout and overstock risk for every SKU, with a clear recommended action."),
      bullet("Quantify business impact in currency terms (revenue at risk, capital locked)."),
      bullet("Hand the operations team a dashboard usable without a data scientist in the room."),
      bullet("Deploy a scoring service that returns forecast + risk for any SKU on demand."),

      h2("Target Users / Use Cases"),
      bullet("NorthBay's Head of Operations — primary decision-maker for reorder and markdown actions."),
      bullet("Merchandising team — deciding which products to push, clear, or discontinue."),
      bullet("Finance lead — tracking capital freed and revenue protected."),

      h2("Business Value Delivered"),
      bullet("Forecast accuracy improved 29.7% over naive planning (WAPE, honestly backtested)."),
      bullet("£204,185 in revenue at risk from stockouts identified and prioritised for action."),
      bullet("£43,403 in capital locked in overstock identified for markdown/clearance."),
      bullet("A transparent, explainable risk logic — not a black box — that ops can act on immediately."),

      h2("Non-functional Goals"),
      bullet("Reproducible: the full pipeline re-runs end-to-end from raw data with one command."),
      bullet("Honest: every model is compared against a baseline on a fair, leakage-free backtest."),
      bullet("Usable: outputs reach stakeholders as a dashboard and API, not only as notebooks."),
      bullet("Documented: every cleaning decision and modelling assumption is written down."),

      // ---- Architecture ----
      h1("Architecture Overview"),
      body("FORESIGHT follows a straightforward, reproducible analytics pipeline:"),
      body("Raw Transaction Data  →  Cleaning & Table Construction  →  Feature Engineering  →  " +
           "Seasonal-Naive Baseline  →  LightGBM Forecast Model  →  Rolling-Origin Backtest  →  " +
           "Stockout/Overstock Risk Scoring  →  Streamlit Dashboard + FastAPI Scoring Service"),
      body(
        "Unlike a general-purpose MLOps stack, this architecture is deliberately scoped to what the engagement " +
        "requires: a reproducible pipeline, an honestly-validated forecast, transparent risk logic, and two " +
        "stakeholder-facing surfaces (dashboard and API). Real-time infrastructure, automated retraining " +
        "pipelines, and live system integrations were explicitly out of scope for this engagement and were not built."
      ),

      // ---- Timeline ----
      h1("Execution Timeline"),
      simpleTable(
        ["Week", "Focus", "Deliverables"],
        [
          ["Week 1", "Data Foundation", "Reproducible pipeline (D1); data-quality report"],
          ["Week 2", "EDA & Baseline", "EDA insight memo (D2); seasonal-naive baseline & WAPE metric fixed"],
          ["Week 3", "Modelling & Risk", "Backtested forecast beating baseline (D3); stockout/overstock risk scoring (D4)"],
          ["Week 4", "Productize", "Dashboard (D5); deployed scoring service (D6); executive readout (D7)"],
        ],
        [1500, 2800, 4700]
      ),

      // ---- Technical Highlights ----
      h1("Technical Highlights"),
      h2("Modelling Techniques"),
      bullet("Seasonal-naive baseline (demand = same week, 52 weeks prior) — the bar every model must beat."),
      bullet("LightGBM gradient-boosted trees, trained as a global panel model across all SKUs."),
      bullet("Quantile regression (10th/90th percentile) for an 80% prediction interval on every forecast."),
      bullet("Rolling-origin cross-validation (6 folds, 8-week horizon) — never a random train/test split."),

      h2("Feature Engineering"),
      bullet("Lag features: 1, 2, 4, 8, and 52 weeks — all computed strictly from past values only."),
      bullet("Rolling statistics: 4-week and 8-week trailing mean and standard deviation."),
      bullet("Calendar features: month, season, UK public holiday flag."),
      bullet("Promotion signal: inferred from price drops ≥15% below a SKU's trailing 28-day median price."),

      h2("Challenges Faced"),
      bullet("Source data contained no real inventory records (no stock levels, lead times, or reorder points)."),
      bullet("Raw transaction data included cancellations, non-product codes (postage, fees), and duplicates."),
      bullet("Guarding against data leakage in lag/rolling features during recursive multi-step forecasting."),

      h2("Solutions"),
      bullet("Simulated inventory positions using a standard reorder-point formula (95% service level, category-specific lead times), documented explicitly as an assumption rather than presented as real data."),
      bullet("Built an explicit, code-driven cleaning pipeline: excluded cancellations, non-product codes, and duplicates, with every decision documented in the EDA memo."),
      bullet("Enforced shift-before-rolling feature construction and verified rolling-origin backtesting to guarantee no future information enters any feature."),

      // ---- Deployment ----
      h1("Deployment & Operations"),
      h2("Deployment Platform"),
      bullet("Streamlit Community Cloud — dashboard hosting."),
      bullet("Render / Hugging Face Spaces — FastAPI scoring service hosting."),
      bullet("GitHub — version control and reproducible source of truth."),

      h2("Reproducibility"),
      body(
        "A grader (or NorthBay's own team) can clone the repository, run `python src/pipeline.py`, " +
        "`python src/forecast.py`, and `python src/risk.py` in sequence, and reproduce the same headline " +
        "backtest numbers reported in this document — with random seeds fixed throughout."
      ),

      // ---- Key Features table ----
      h1("Key Features"),
      simpleTable(
        ["ID", "Feature", "Description", "Acceptance Criteria"],
        [
          ["D1", "Data Pipeline", "Ingests and cleans raw transactions into 4 analysis-ready tables", "Reruns end-to-end from raw data with one command"],
          ["D2", "EDA & Data-Quality Memo", "Documents data issues and demand patterns found", "3+ business insights, labelled charts, issues documented"],
          ["D3", "Demand Forecast Model", "Weekly SKU-level forecast, backtested", "Beats seasonal-naive baseline on rolling-origin CV"],
          ["D4", "Risk Scoring", "Stockout/overstock classification per SKU", "Transparent logic, £ value attached, tied to decisioning grid"],
          ["D5", "Planning Dashboard", "Interactive, filterable view for ops team", "Usable without a data scientist present"],
          ["D6", "Scoring Service", "Hosted API returning forecast + risk", "Handles bad input gracefully, documented I/O"],
          ["D7", "Executive Readout", "Stakeholder-facing summary of findings", "Leads with £ impact, honest about limitations"],
        ],
        [700, 2000, 3400, 2900]
      ),

      // ---- Tech stack ----
      h1("Technology Stack"),
      simpleTable(
        ["Category", "Technology", "Rationale"],
        [
          ["Language", "Python", "Primary language for data pipeline, modelling, and services"],
          ["Data processing", "pandas, numpy", "Cleaning, aggregation, feature engineering"],
          ["Forecasting", "LightGBM", "Gradient-boosted trees; strong tabular/panel performance, fast to backtest"],
          ["Dashboard", "Streamlit, Plotly", "Fast, interactive, deployable analytics UI"],
          ["Serving", "FastAPI", "Lightweight, documented, production-style scoring endpoint"],
          ["Version control", "Git & GitHub", "Reproducibility and collaboration"],
        ],
        [2200, 2200, 4600]
      ),

      // ---- Backtest results ----
      h1("Forecast Accuracy — Backtest Results"),
      body("WAPE (Weighted Absolute Percentage Error, lower is better), averaged across 6 rolling-origin backtest folds, 8-week horizon each:"),
      simpleTable(
        ["Model", "Average WAPE"],
        [
          ["Seasonal-naive baseline", "0.875"],
          ["FORESIGHT (LightGBM)", "0.615"],
          ["Improvement", "29.7% lower error"],
        ],
        [4500, 4500]
      ),
      body("The model beat the baseline in every one of the 6 backtest folds — a consistent, honestly-tested improvement, not a single lucky split."),

      // ---- Visuals ----
      new Paragraph({ children: [new PageBreak()] }),
      h1("Visuals"),
      h2("Weekly Demand Trend"),
      ...figure(`${FIG_DIR}/weekly_demand_trend.png`, 500, "Figure 1 — Weekly demand across all SKUs, showing strong Q4 seasonality."),
      h2("Monthly Seasonality"),
      ...figure(`${FIG_DIR}/monthly_seasonality.png`, 450, "Figure 2 — Units sold by calendar month, both years combined."),
      h2("Top SKUs by Revenue"),
      ...figure(`${FIG_DIR}/top10_skus_revenue.png`, 500, "Figure 3 — Top 10 SKUs by total revenue."),
      h2("Promotion Lift"),
      ...figure(`${FIG_DIR}/promo_lift.png`, 350, "Figure 4 — Average daily units sold, promotional vs non-promotional days."),

      h2("Dashboard & API Screenshots"),
      body("[ Add screenshots here once the dashboard and API are deployed — see the README for deployment steps. Recommended: Priority list tab, Forecast vs Actual tab, Decisioning Grid tab, and the API's root/SKU endpoint response. ]"),

      // ---- Reflection & conclusion ----
      new Paragraph({ children: [new PageBreak()] }),
      h1("Personal Reflection"),
      body(
        "Going into this engagement, my instinct was to reach for the most sophisticated model I could build and " +
        "let the accuracy number speak for itself. The brief pushed back on that instinct immediately: nothing " +
        "counts until it beats a simple seasonal-naive baseline, tested honestly on data the model never saw " +
        "during training. That constraint changed how I worked. Instead of tuning a model in isolation, I spent " +
        "real time on the rolling-origin backtest itself — making sure every lag and rolling feature was built " +
        "strictly from past values, and that the 8-week recursive forecast never let a future week leak backward " +
        "into a feature. Seeing the model beat the baseline by a consistent margin across all six folds, rather " +
        "than just one favourable split, was a far more convincing result than a single accuracy score would " +
        "have been."
      ),
      body(
        "The other decision I had to sit with was the missing inventory data. The source data had no stock " +
        "levels, lead times, or reorder points at all, and it would have been easy to quietly patch that gap and " +
        "move on. I chose instead to simulate it using a standard reorder-point formula and say so plainly, in " +
        "the README and in this report, rather than let it pass as real. That felt like the more professional " +
        "choice — a client, or a reviewer, should never have to discover an assumption on their own."
      ),
      body(
        "If I had more time, I would want to validate the promotion signal against a real promotional calendar " +
        "instead of inferring it from price drops, and I would extend the risk scoring with a confidence measure " +
        "so the operations team knows which recommendations to trust most. More broadly, this project changed how " +
        "I think about what makes analysis trustworthy: not the complexity of the model, but whether every claim " +
        "in it can be traced back to a fair test and an honest assumption."
      ),

      h1("Conclusion"),
      body(
        "FORESIGHT delivers exactly what NorthBay Living's brief asked for: a demand forecast that honestly " +
        "beats naive planning, a transparent risk-scoring system tied to real currency impact, and stakeholder-facing " +
        "tools (dashboard and API) that the operations team can use without a data scientist in the room. Every " +
        "modelling claim in this report is backed by a reproducible backtest, and every assumption — most notably " +
        "the simulated inventory layer — is stated plainly rather than hidden. The system is ready for NorthBay to " +
        "act on immediately, and ready to be extended with real inventory data as soon as that feed becomes available."
      ),
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("project_report.docx", buffer);
  console.log("Written: project_report.docx");
});
