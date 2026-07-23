const pptxgen = require("pptxgenjs");

const NAVY = "1E2340";
const GOLD = "C9A66B";
const CREAM = "F6F3EC";
const GREEN = "3FA66B";
const RED = "D9564F";
const PURPLE = "8E7CC3";
const GREY = "6B7280";

let pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5

function titleSlide() {
  let s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText("Project FORESIGHT", {
    x: 0.8, y: 2.3, w: 11.7, h: 1.0,
    fontSize: 40, bold: true, color: "FFFFFF", fontFace: "Georgia",
  });
  s.addText("Demand & Inventory Intelligence — Executive Readout", {
    x: 0.8, y: 3.15, w: 11.7, h: 0.6,
    fontSize: 18, color: GOLD, fontFace: "Arial",
  });
  s.addText("Prepared for the Head of Operations & Finance · NorthBay Living", {
    x: 0.8, y: 3.75, w: 11.7, h: 0.4,
    fontSize: 13, color: CREAM,
  });
  s.addShape("line", { x: 0.8, y: 4.35, w: 3.2, h: 0, line: { color: GOLD, width: 2 } });
}

function headline() {
  let s = pres.addSlide();
  s.background = { color: CREAM };
  s.addText("The bottom line", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: NAVY });

  const cards = [
    { label: "Revenue at risk\nfrom stockouts", value: "£204,185", color: RED },
    { label: "Capital locked\nin overstock", value: "£43,403", color: PURPLE },
    { label: "Forecast improvement\nover naive planning", value: "29.7%", color: GREEN },
  ];
  cards.forEach((c, i) => {
    const x = 0.7 + i * 4.05;
    s.addShape("roundRect", { x, y: 1.6, w: 3.7, h: 2.6, rectRadius: 0.12, fill: { color: "FFFFFF" }, line: { color: "E5E1D8", width: 1 } });
    s.addText(c.value, { x, y: 2.0, w: 3.7, h: 1.0, align: "center", fontSize: 36, bold: true, color: c.color });
    s.addText(c.label, { x, y: 3.0, w: 3.7, h: 1.0, align: "center", fontSize: 14, color: NAVY });
  });

  s.addText(
    "FORESIGHT identifies exactly which SKUs need reordering now, which should be marked down, " +
    "and quantifies the £ impact of each — replacing spreadsheet guesswork with a forecast that " +
    "measurably beats naive planning.",
    { x: 0.7, y: 4.6, w: 11.9, h: 1.3, fontSize: 15, color: NAVY, italic: false }
  );
}

function problem() {
  let s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText("The problem we were asked to solve", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: NAVY });

  const points = [
    "Stock is planned on gut feel and spreadsheets — no forecasting in place today.",
    "Best-sellers run out (lost sales, frustrated customers).",
    "Slow movers pile up (cash locked in stock, later marked down at a loss).",
    "Both problems happen at once, across ~200 active SKUs.",
  ];
  s.addText(
    points.map((p, i) => ({ text: p, options: { bullet: true, breakLine: i < points.length - 1, color: NAVY, fontSize: 16, paraSpaceAfter: 14 } })),
    { x: 0.9, y: 1.6, w: 7.2, h: 4.5 }
  );

  s.addShape("roundRect", { x: 8.5, y: 1.7, w: 4.1, h: 4.2, rectRadius: 0.1, fill: { color: NAVY } });
  s.addText("\u201CI need something my team can actually look at — not a notebook only a data scientist can read.\u201D", {
    x: 8.8, y: 2.1, w: 3.5, h: 2.6, fontSize: 14, italic: true, color: CREAM,
  });
  s.addText("— Head of Operations, NorthBay Living", { x: 8.8, y: 4.9, w: 3.5, h: 0.5, fontSize: 11, color: GOLD });
}

function whatWeBuilt() {
  let s = pres.addSlide();
  s.background = { color: CREAM };
  s.addText("What FORESIGHT delivers", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: NAVY });

  const items = [
    ["1", "Weekly forecast", "8-week SKU-level demand forecast, backtested against a naive baseline"],
    ["2", "Risk scoring", "Every SKU flagged: reorder now, markdown, watch, or healthy — with £ impact"],
    ["3", "Planning dashboard", "Filterable, self-serve view for the ops team — no data scientist required"],
    ["4", "Live scoring service", "A hosted API returning forecast + risk for any SKU, on demand"],
  ];
  items.forEach((it, i) => {
    const x = 0.7 + (i % 2) * 6.0;
    const y = 1.7 + Math.floor(i / 2) * 2.2;
    s.addShape("roundRect", { x, y, w: 5.6, h: 1.9, rectRadius: 0.1, fill: { color: "FFFFFF" }, line: { color: "E5E1D8", width: 1 } });
    s.addText(it[0], { x: x + 0.25, y: y + 0.2, w: 0.8, h: 0.8, fontSize: 26, bold: true, color: GOLD });
    s.addText(it[1], { x: x + 1.0, y: y + 0.2, w: 4.4, h: 0.5, fontSize: 16, bold: true, color: NAVY });
    s.addText(it[2], { x: x + 1.0, y: y + 0.75, w: 4.4, h: 1.0, fontSize: 12, color: GREY });
  });
}

function accuracy() {
  let s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText("Forecast accuracy — tested honestly", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: NAVY });
  s.addText("WAPE (lower is better) — model vs seasonal-naive baseline, averaged across 6 rolling-origin backtest folds", {
    x: 0.7, y: 1.2, w: 11.9, h: 0.4, fontSize: 13, color: GREY,
  });

  s.addChart(pres.ChartType.bar, [
    {
      name: "WAPE",
      labels: ["Seasonal-naive baseline", "FORESIGHT model"],
      values: [0.8747, 0.6153],
    },
  ], {
    x: 1.5, y: 1.8, w: 7.0, h: 4.3,
    barDir: "col",
    chartColors: [GREY, GREEN],
    showTitle: false,
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.00",
    valAxisTitle: "WAPE",
    showLegend: false,
    catAxisLabelColor: NAVY,
    valAxisLabelColor: NAVY,
    valGridLine: { color: "EEEEEE", size: 1 },
    catGridLine: { style: "none" },
  });

  s.addShape("roundRect", { x: 8.9, y: 2.2, w: 3.7, h: 3.4, rectRadius: 0.1, fill: { color: CREAM } });
  s.addText("29.7%", { x: 8.9, y: 2.5, w: 3.7, h: 0.9, align: "center", fontSize: 34, bold: true, color: GREEN });
  s.addText("lower error than\nnaive planning", { x: 8.9, y: 3.3, w: 3.7, h: 0.7, align: "center", fontSize: 13, color: NAVY });
  s.addText("Non-negotiable rule followed: rolling-origin backtesting, no future data in any feature, result reported honestly whether it won or lost.", {
    x: 9.1, y: 4.2, w: 3.3, h: 1.2, fontSize: 10, color: GREY, italic: true,
  });
}

function impact() {
  let s = pres.addSlide();
  s.background = { color: CREAM };
  s.addText("Where the risk sits today", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: NAVY });

  s.addChart(pres.ChartType.bar, [
    {
      name: "SKUs",
      labels: ["Healthy", "Reorder Now", "Markdown / Clear"],
      values: [105, 83, 12],
    },
  ], {
    x: 0.7, y: 1.5, w: 6.3, h: 4.5,
    barDir: "col",
    chartColors: [GREEN, RED, PURPLE],
    showTitle: true, title: "SKUs by risk quadrant (of 200)",
    titleColor: NAVY, titleFontSize: 14,
    showValue: true, dataLabelPosition: "outEnd",
    showLegend: false,
    catAxisLabelColor: NAVY, valAxisLabelColor: NAVY,
    valGridLine: { color: "EEEEEE", size: 1 }, catGridLine: { style: "none" },
  });

  s.addText("Top 5 priority SKUs (by £ value at stake)", { x: 7.3, y: 1.5, w: 5.3, h: 0.4, fontSize: 14, bold: true, color: NAVY });
  const rows = [
    ["SKU", "Product", "Status", "£ at stake"],
    ["37503", "Tea Time Cake Stand", "Reorder Now", "23,596"],
    ["84078A", "Retro Storage Cubes", "Reorder Now", "20,293"],
    ["22423", "Regency Cakestand", "Reorder Now", "8,359"],
    ["15056BL", "Edwardian Parasol", "Markdown", "7,993"],
    ["23084", "Rabbit Night Light", "Reorder Now", "7,499"],
  ];
  s.addTable(rows, {
    x: 7.3, y: 2.0, w: 5.3, h: 3.0,
    fontSize: 10.5, color: NAVY,
    border: { type: "solid", color: "E5E1D8", pt: 0.5 },
    fill: { color: "FFFFFF" },
    autoPage: false,
    rowH: 0.42,
  });
}

function howToUse() {
  let s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  s.addText("How the team uses this, starting Monday", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: NAVY });

  const steps = [
    ["Open the dashboard", "See the prioritised reorder / markdown list, sorted by £ impact."],
    ["Filter by category or SKU", "Drill into any product line the merchandiser cares about."],
    ["Check the decisioning grid", "Triage the whole 200-SKU catalog in one glance."],
    ["Query the API for any SKU", "Get forecast + risk on demand — for future system integration."],
  ];
  steps.forEach((st, i) => {
    const y = 1.7 + i * 1.15;
    s.addShape("oval", { x: 0.9, y: y, w: 0.5, h: 0.5, fill: { color: GOLD } });
    s.addText(String(i + 1), { x: 0.9, y: y, w: 0.5, h: 0.5, align: "center", valign: "middle", fontSize: 16, bold: true, color: "FFFFFF" });
    s.addText(st[0], { x: 1.6, y: y - 0.05, w: 4.5, h: 0.5, fontSize: 15, bold: true, color: NAVY });
    s.addText(st[1], { x: 1.6, y: y + 0.4, w: 9.8, h: 0.5, fontSize: 12, color: GREY });
  });
}

function limitations() {
  let s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText("Honest limitations", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: "FFFFFF" });

  const points = [
    "Built on a real 2-year e-commerce transaction history; inventory positions (stock on-hand, lead time, reorder point) are simulated using standard reorder-point logic, since no inventory feed was available in the source data.",
    "The model beats the seasonal-naive baseline by 29.7% WAPE on backtest — a real, honestly-tested improvement, not a guarantee for every SKU every week.",
    "Promotions are inferred from price drops, not from a true promo calendar — treat promo-week forecasts with some caution.",
    "Recommended next step: connect NorthBay's real inventory feed to replace the simulated layer before this drives live purchase orders.",
  ];
  s.addText(
    points.map((p, i) => ({ text: p, options: { bullet: true, breakLine: i < points.length - 1, color: CREAM, fontSize: 14, paraSpaceAfter: 16 } })),
    { x: 0.9, y: 1.6, w: 11.3, h: 5.0 }
  );
}

function closing() {
  let s = pres.addSlide();
  s.background = { color: CREAM };
  s.addText("Recommended next steps", { x: 0.7, y: 0.5, w: 11.9, h: 0.7, fontSize: 26, bold: true, color: NAVY });
  const items = [
    "Act on the 83 \u201CReorder Now\u201D SKUs this week — £204K in sales is at risk if they stock out.",
    "Run a markdown/clearance pass on the 12 overstocked SKUs to free £43K in working capital.",
    "Connect NorthBay's real inventory feed to replace the simulated layer.",
    "Re-run the pipeline monthly as new sales data arrives — it is fully reproducible end-to-end.",
  ];
  s.addText(
    items.map((p, i) => ({ text: p, options: { bullet: true, breakLine: i < items.length - 1, color: NAVY, fontSize: 16, paraSpaceAfter: 16 } })),
    { x: 0.9, y: 1.7, w: 11.3, h: 4.0 }
  );
  s.addShape("line", { x: 0.7, y: 6.2, w: 11.9, h: 0, line: { color: "D9D2C2", width: 1 } });
  s.addText("Project FORESIGHT · Zidio Development Data Science & Analytics Engagement", {
    x: 0.7, y: 6.4, w: 11.9, h: 0.4, fontSize: 11, color: GREY,
  });
}

titleSlide();
headline();
problem();
whatWeBuilt();
accuracy();
impact();
howToUse();
limitations();
closing();

pres.writeFile({ fileName: "reports/executive_readout.pptx" }).then(() => {
  console.log("Deck written to reports/executive_readout.pptx");
});
