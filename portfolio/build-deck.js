// Portfolio deck (bilingual 繁中 + English) — QuantLab Epic H Deep-Learning Research Lab
// Dark "deep-tech" theme; embeds real screenshots (DL performance report + research dashboard).
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const FA = require("react-icons/fa");

// ---------- Theme ----------
const C = {
  bg: "0B1220", panel: "16233D", panel2: "1E2C4A", navy: "14213D",
  teal: "1C7293", mint: "02C39A", cyan: "35C2F5", coral: "FF7A45", gold: "F5B841",
  txt: "EAF1FB", mute: "93A1BD", faint: "5C6B89", line: "26344F", white: "FFFFFF",
};
const F = { head: "Noto Sans CJK TC", body: "Noto Sans CJK TC" };
const W = 13.333, H = 7.5, M = 0.7;

// ---------- Icons ----------
async function iconPng(IconComponent, color = "0B1220", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(IconComponent, { color: "#" + color, size: String(size) }));
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + png.toString("base64");
}
const ICONS = {};
async function buildIcons() {
  const spec = {
    brain: FA.FaBrain, fire: FA.FaFire, sliders: FA.FaSlidersH, layers: FA.FaLayerGroup,
    scale: FA.FaBalanceScale, shield: FA.FaShieldAlt, clock: FA.FaHistory, chart: FA.FaChartLine,
    flask: FA.FaFlask, check: FA.FaCheckCircle, code: FA.FaCode, diagram: FA.FaProjectDiagram,
    lock: FA.FaLock, eye: FA.FaEye, cap: FA.FaGraduationCap, server: FA.FaServer, warn: FA.FaExclamationTriangle, cube: FA.FaCubes,
  };
  for (const [k, comp] of Object.entries(spec)) ICONS[k] = await iconPng(comp, "0B1220", 256);
}

// ---------- Helpers ----------
const sh = (o = {}) => Object.assign({ type: "outer", color: "000000", blur: 9, offset: 4, angle: 90, opacity: 0.30 }, o);

function bgBase(slide) {
  slide.background = { color: C.bg };
  slide.addShape("rect", { x: 0, y: 0, w: W, h: 0.06, fill: { color: C.mint } });
}
function footer(slide, n, label = "QuantLab · Epic H · 深度學習研究實驗室 / Deep-Learning Research Lab") {
  slide.addText(label, { x: M, y: H - 0.5, w: 10, h: 0.3, fontFace: F.body, fontSize: 9, color: C.faint, align: "left", valign: "middle", margin: 0 });
  slide.addText(String(n).padStart(2, "0") + " / 13", { x: W - M - 1.6, y: H - 0.5, w: 1.6, h: 0.3, fontFace: F.body, fontSize: 9, color: C.faint, align: "right", valign: "middle", margin: 0 });
}
function kicker(slide, x, y, text, color = C.mint) {
  slide.addShape("rect", { x, y: y + 0.04, w: 0.28, h: 0.16, fill: { color } });
  slide.addText(text.toUpperCase(), { x: x + 0.4, y: y - 0.06, w: 11, h: 0.36, fontFace: F.body, fontSize: 12, bold: true, color, charSpacing: 2, align: "left", valign: "middle", margin: 0 });
}
// bilingual title: zh big + en sub
function bititle(slide, x, y, w, zh, en, size = 29) {
  slide.addText(zh, { x, y, w, h: 0.7, fontFace: F.head, fontSize: size, bold: true, color: C.txt, align: "left", valign: "middle", margin: 0 });
  slide.addText(en, { x, y: y + 0.66, w, h: 0.38, fontFace: F.head, fontSize: 14, color: C.cyan, align: "left", valign: "middle", margin: 0 });
}
function card(slide, x, y, w, h, opts = {}) {
  slide.addShape("roundRect", { x, y, w, h, rectRadius: 0.09, fill: { color: opts.fill || C.panel }, line: { color: C.line, width: 1 }, shadow: sh({ opacity: 0.22 }) });
  if (opts.accent) slide.addShape("rect", { x, y: y + 0.18, w: 0.07, h: h - 0.36, fill: { color: opts.accent } });
}
function iconCircle(slide, x, y, d, circleColor, iconKey) {
  slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color: circleColor }, shadow: sh({ blur: 7, offset: 3, opacity: 0.28 }) });
  const ip = d * 0.46;
  slide.addImage({ data: ICONS[iconKey], x: x + (d - ip) / 2, y: y + (d - ip) / 2, w: ip, h: ip });
}
function shot(slide, x, y, w, h, imgPath, ring = C.cyan) {
  slide.addShape("roundRect", { x: x - 0.11, y: y - 0.11, w: w + 0.22, h: h + 0.22, rectRadius: 0.06, fill: { color: C.white }, line: { color: ring, width: 1.5 }, shadow: sh({ blur: 13, offset: 5, opacity: 0.42 }) });
  slide.addImage({ path: imgPath, x, y, w, h });
}
function nodes(slide, pts, color = C.cyan) {
  for (let i = 0; i < pts.length - 1; i++) { const a = pts[i], b = pts[i + 1]; slide.addShape("line", { x: a[0], y: a[1], w: b[0] - a[0], h: b[1] - a[1], line: { color, width: 1, transparency: 55 } }); }
  pts.forEach((p, i) => slide.addShape("ellipse", { x: p[0] - 0.05, y: p[1] - 0.05, w: 0.1, h: 0.1, fill: { color: i % 2 ? C.mint : color, transparency: 15 } }));
}

// ---------- Build ----------
async function main() {
  await buildIcons();
  const pres = new pptxgen();
  pres.defineLayout({ name: "WIDE", width: W, height: H });
  pres.layout = "WIDE";
  pres.author = "YC Chang";
  pres.title = "QuantLab Epic H — Deep-Learning Research Lab 作品集 / Portfolio";
  const A = "assets/";

  // ===== 1 — Cover =====
  let s = pres.addSlide(); bgBase(s);
  s.addShape("rect", { x: 0, y: 0, w: W, h: H, fill: { color: C.bg } });
  s.addShape("rect", { x: 0, y: 0, w: W, h: 0.06, fill: { color: C.mint } });
  nodes(s, [[9.4, 1.0], [10.6, 1.7], [11.6, 1.1], [12.5, 2.0]], C.cyan);
  nodes(s, [[9.9, 2.4], [11.0, 2.9], [12.2, 2.5]], C.teal);
  s.addShape("ellipse", { x: 11.7, y: 0.7, w: 1.5, h: 1.5, fill: { color: C.mint, transparency: 86 } });
  kicker(s, M, 1.75, "Machine-Learning Portfolio · 深度學習課程作品集", C.mint);
  s.addText("深度學習研究實驗室", { x: M, y: 2.2, w: 11.4, h: 1.0, fontFace: F.head, fontSize: 50, bold: true, color: C.txt, align: "left", valign: "middle", margin: 0 });
  s.addText("Deep-Learning Research Lab", { x: M, y: 3.25, w: 11.4, h: 0.6, fontFace: F.head, fontSize: 27, bold: true, color: C.cyan, align: "left", valign: "middle", margin: 0 });
  s.addText("QuantLab · Epic H", { x: M, y: 3.9, w: 11.4, h: 0.4, fontFace: F.body, fontSize: 16, color: C.mute, align: "left", valign: "middle", margin: 0 });
  s.addText([
    { text: "framework-free 參考模型", options: { color: C.mint, bold: true } }, { text: "  →  ", options: { color: C.faint } },
    { text: "真實 PyTorch 訓練", options: { color: C.gold, bold: true } }, { text: "  →  ", options: { color: C.faint } },
    { text: "互動研究 UI", options: { color: C.coral, bold: true } },
  ], { x: M, y: 4.5, w: 11.4, h: 0.4, fontFace: F.body, fontSize: 16, align: "left", valign: "middle", margin: 0 });
  s.addText("framework-free reference model  →  real PyTorch training  →  interactive research UI", { x: M, y: 4.95, w: 11.4, h: 0.35, fontFace: F.body, fontSize: 12.5, italic: true, color: C.faint, align: "left", valign: "middle", margin: 0 });
  s.addShape("roundRect", { x: M, y: 5.55, w: 6.4, h: 0.6, rectRadius: 0.3, fill: { color: C.panel2 }, line: { color: C.mint, width: 1 } });
  s.addText("方法論誠實 ＞ alpha · methodology honesty over alpha · no_alpha_claim", { x: M, y: 5.55, w: 6.4, h: 0.6, fontFace: F.body, fontSize: 11.5, bold: true, color: C.mint, align: "center", valign: "middle", margin: 0 });
  s.addText("YC Chang · ycchang.pmp@gmail.com · 2026", { x: M, y: H - 0.55, w: 9, h: 0.3, fontFace: F.body, fontSize: 10, color: C.faint, align: "left", valign: "middle", margin: 0 });

  // ===== 2 — Overview =====
  s = pres.addSlide(); bgBase(s); footer(s, 2);
  kicker(s, M, 0.6, "01 · 專案概覽 Overview");
  bititle(s, M, 1.05, 8.4, "一個對自己結果誠實的量化研究實驗室", "A quant research lab that never lies about its own results");
  s.addText([
    { text: "QuantLab", options: { bold: true, color: C.cyan } },
    { text: " 是個人、純紙上 (paper-only) 量化研究平台。成功 = ", options: { color: C.txt } },
    { text: "方法論誠實 + 實驗能力", options: { bold: true, color: C.mint } },
    { text: "，而非 alpha。", options: { color: C.txt } },
  ], { x: M, y: 2.35, w: 7.1, h: 0.6, fontFace: F.body, fontSize: 13, align: "left", valign: "top", lineSpacingMultiple: 1.2, margin: 0 });
  s.addText("A personal, paper-only quant lab. Success = methodology honesty + experimentation capability, not alpha — every model slice declares no_alpha_claim.", { x: M, y: 3.05, w: 7.1, h: 0.6, fontFace: F.body, fontSize: 11, italic: true, color: C.mute, align: "left", valign: "top", lineSpacingMultiple: 1.15, margin: 0 });
  const ovr = [
    ["scale", C.mint, "OOS-net 為唯一權威", "OOS-net is the only ranking authority — baseline always visible"],
    ["clock", C.cyan, "PIT-safe 資料", "PIT-safe: available_date ≤ asof; approximate data strict-excluded"],
    ["shield", C.coral, "Fail-closed 誠實", "Fail-closed by default — never emits a misleading computed"],
  ];
  ovr.forEach((r, i) => {
    const y = 3.95 + i * 0.95;
    iconCircle(s, M, y, 0.64, r[1], r[0]);
    s.addText(r[2], { x: M + 0.92, y: y - 0.04, w: 6.4, h: 0.34, fontFace: F.head, fontSize: 14.5, bold: true, color: C.txt, align: "left", valign: "middle", margin: 0 });
    s.addText(r[3], { x: M + 0.92, y: y + 0.3, w: 6.4, h: 0.34, fontFace: F.body, fontSize: 10.5, color: C.mute, align: "left", valign: "middle", margin: 0 });
  });
  const sx = 8.55, sw = 4.1;
  card(s, sx, 2.3, sw, 4.35, { fill: C.panel, accent: C.mint });
  s.addText("專案規模 · At a glance", { x: sx + 0.32, y: 2.48, w: sw - 0.6, h: 0.38, fontFace: F.body, fontSize: 11.5, bold: true, color: C.mute, charSpacing: 1, align: "left", valign: "middle", margin: 0 });
  [["10", "Epics 已實作 / implemented (A0→H)", C.cyan], ["435", "Python 測試通過 / tests pass (2 skipped)", C.mint], ["0", "alpha 宣稱 / alpha claims — no_alpha_claim", C.gold]].forEach((st, i) => {
    const y = 2.95 + i * 1.18;
    s.addText(st[0], { x: sx + 0.32, y, w: sw - 0.6, h: 0.66, fontFace: F.head, fontSize: 42, bold: true, color: st[2], align: "left", valign: "middle", margin: 0 });
    s.addText(st[1], { x: sx + 0.34, y: y + 0.66, w: sw - 0.62, h: 0.34, fontFace: F.body, fontSize: 10, color: C.mute, align: "left", valign: "top", lineSpacingMultiple: 1.05, margin: 0 });
  });

  // ===== 3 — Architecture =====
  s = pres.addSlide(); bgBase(s); footer(s, 3);
  kicker(s, M, 0.6, "02 · 系統架構 Architecture", C.cyan);
  bititle(s, M, 1.05, 11.9, "框架隔離：核心引擎永不依賴任何 ML 框架", "Framework isolation — the core engine never imports an ML framework");
  s.addText("FrameworkAdapterRegistry 惰性解析 torch/jax/tf，缺席時誠實降級為 reference；import-linter 兩條契約 KEPT 強制邊界。", { x: M, y: 2.3, w: 7.2, h: 0.7, fontFace: F.body, fontSize: 11.5, color: C.mute, align: "left", valign: "top", lineSpacingMultiple: 1.15, margin: 0 });
  const lyrs = [
    ["engine / data 核心 · core", "向量化回測引擎、PIT loader — 不 import torch/jax/tf", C.teal, "cube"],
    ["策略 adapter 邊界 · boundary", "DeepForecastAllocationStrategy 將模型接入 A0 引擎", C.cyan, "diagram"],
    ["DL backend registry", "惰性解析 + 誠實 fallback / lazy resolve + honest fallback", C.mint, "layers"],
  ];
  lyrs.forEach((l, i) => {
    const y = 3.15 + i * 1.0;
    card(s, M, y, 7.15, 0.86, { fill: C.panel, accent: l[2] });
    iconCircle(s, M + 0.26, y + 0.18, 0.5, l[2], l[3]);
    s.addText(l[0], { x: M + 0.95, y: y + 0.1, w: 6.0, h: 0.34, fontFace: F.head, fontSize: 13.5, bold: true, color: C.txt, align: "left", valign: "middle", margin: 0 });
    s.addText(l[1], { x: M + 0.95, y: y + 0.44, w: 6.0, h: 0.34, fontFace: F.body, fontSize: 10, color: C.mute, align: "left", valign: "middle", margin: 0 });
  });
  s.addText("import-linter 禁止 / forbids:  engine / data  ⊁  torch · jax · tf · DL backend", { x: M, y: 6.2, w: 7.15, h: 0.4, fontFace: F.body, fontSize: 10.5, italic: true, bold: true, color: C.coral, align: "center", valign: "middle", margin: 0 });
  const bx = 8.5, bw = 4.15;
  card(s, bx, 2.95, bw, 3.7, { fill: C.navy, accent: C.gold });
  s.addText("可插拔 backends · pluggable", { x: bx + 0.3, y: 3.1, w: bw - 0.5, h: 0.4, fontFace: F.body, fontSize: 11.5, bold: true, color: C.mute, charSpacing: 1, align: "left", valign: "middle", margin: 0 });
  [["reference", "framework-free，永不 raise / never raises", C.mint], ["pytorch", "真實 autograd 訓練 / real training (H-2)", C.gold], ["jax / tensorflow", "已註冊，缺席時 fallback / registered", C.faint]].forEach((b, i) => {
    const y = 3.6 + i * 0.95;
    s.addShape("roundRect", { x: bx + 0.3, y, w: bw - 0.6, h: 0.78, rectRadius: 0.08, fill: { color: C.panel2 }, line: { color: C.line, width: 1 } });
    s.addShape("ellipse", { x: bx + 0.5, y: y + 0.29, w: 0.2, h: 0.2, fill: { color: b[2] } });
    s.addText(b[0], { x: bx + 0.85, y: y + 0.08, w: bw - 1.1, h: 0.34, fontFace: F.head, fontSize: 13.5, bold: true, color: C.txt, align: "left", valign: "middle", margin: 0 });
    s.addText(b[1], { x: bx + 0.85, y: y + 0.41, w: bw - 1.1, h: 0.3, fontFace: F.body, fontSize: 9.5, color: C.mute, align: "left", valign: "middle", margin: 0 });
  });

  // ===== 4/5/6 — slices =====
  function sliceSlide(n, kick, accent, iconKey, zh, en, leadZh, leadEn, rows) {
    s = pres.addSlide(); bgBase(s); footer(s, n);
    kicker(s, M, 0.6, kick, accent);
    iconCircle(s, W - M - 0.95, 0.65, 0.95, accent, iconKey);
    bititle(s, M, 1.05, 10.0, zh, en);
    s.addText(leadZh, { x: M, y: 2.32, w: 11.0, h: 0.34, fontFace: F.body, fontSize: 12.5, color: C.txt, align: "left", valign: "top", margin: 0 });
    s.addText(leadEn, { x: M, y: 2.66, w: 11.0, h: 0.34, fontFace: F.body, fontSize: 10.5, italic: true, color: C.mute, align: "left", valign: "top", margin: 0 });
    rows.forEach((r, i) => {
      const col = i % 2, row = Math.floor(i / 2);
      const x = M + col * 6.15, y = 3.25 + row * 1.5;
      card(s, x, y, 5.85, 1.34, { fill: C.panel, accent });
      iconCircle(s, x + 0.28, y + 0.36, 0.6, accent, r[0]);
      s.addText(r[1], { x: x + 1.08, y: y + 0.18, w: 4.6, h: 0.36, fontFace: F.head, fontSize: 14, bold: true, color: C.txt, align: "left", valign: "middle", margin: 0 });
      s.addText(r[2], { x: x + 1.08, y: y + 0.55, w: 4.65, h: 0.68, fontFace: F.body, fontSize: 10.5, color: C.mute, align: "left", valign: "top", lineSpacingMultiple: 1.1, margin: 0 });
    });
  }
  sliceSlide(4, "03 · 切片 Slice H-1", C.mint, "brain", "H-1 — 深度學習研究 lab", "Deep-learning research lab",
    "framework-free 確定性參考模型 + 完整實驗 CLI 與 MLOps lineage。", "A framework-free deterministic reference model + full experiment CLI and MLOps lineage.",
    [
      ["brain", "Reference MLP forecaster", "純 NumPy、PIT-safe、per-epoch learning trace · pure-NumPy, PIT-safe"],
      ["chart", "統計效能報告 · Performance report", "distribution / rolling-Sharpe / drawdown / learning-curve；退化輸入 fail-closed"],
      ["code", "參數化實驗 CLI · Experiment CLI", "run_dl_experiment.py：模型 + dumb baseline 跑過 A0 引擎"],
      ["server", "ExperimentRegistry lineage", "確定性 idempotent experiment_id + self-contained SVG/HTML viz"],
    ]);
  sliceSlide(5, "04 · 切片 Slice H-2", C.gold, "fire", "H-2 — 真實 PyTorch 訓練", "Real PyTorch training",
    "讓 pytorch backend 真的用 torch autograd 訓練 reference MLP — 而非 mock。", "Makes the pytorch backend actually train the reference MLP via torch autograd — not a mock.",
    [
      ["fire", "真實 torch 訓練 · Real training", "torch autograd、float64 高精度，位於 lazy backend 邊界之後"],
      ["check", "Seed-init parity ≤ 1e-3", "與 reference 種子初始化一致、deterministic、可重現 · reproducible"],
      ["shield", "Optional torch lane", "預設跳過 (pytest.importorskip)；torch 缺席時誠實回退 reference"],
      ["lock", "框架隔離 KEPT · Isolation", "torch 不進 default lock；import-linter「DL backend boundary」守住"],
    ]);
  sliceSlide(6, "05 · 切片 Slice H-3", C.coral, "sliders", "H-3 — 互動研究 UI", "Interactive research UI",
    "把 Epic H 成果搬上 dashboard：調參數、讀 model-vs-baseline 排行榜。", "Brings Epic H onto the dashboard: tune parameters, read a model-vs-baseline leaderboard.",
    [
      ["sliders", "參數工作流 · Parameter workflow", "backend / hiddenUnits / lookback / epochs / seed / rebalance 控制項"],
      ["chart", "OOS-net 排行榜 · Leaderboard", "確定性 static_replay，baseline 永遠可見 · baseline always visible"],
      ["warn", "Fail-closed 行為", "不支援參數或 checksum 不符 → status=fail_closed，不渲染假結果"],
      ["eye", "真實 Chromium VRT", "npm run e2e:interactive：computed→fail_closed，0-pixel 視覺回歸"],
    ]);

  // ===== 7 — Honesty 2x2 =====
  s = pres.addSlide(); bgBase(s); footer(s, 7);
  kicker(s, M, 0.6, "06 · 誠實工程 Honesty Engineering", C.gold);
  bititle(s, M, 1.05, 11.9, "與眾不同之處：對自己結果說真話的工程", "What sets it apart — engineering that tells the truth about its results");
  const he = [
    ["scale", C.mint, "no_alpha_claim", "每個切片明確宣告不主張獲利；OOS-net 唯一權威，baseline 永遠可見 · OOS-net is the only authority, baseline always shown"],
    ["clock", C.cyan, "PIT-safe · 無 lookahead", "available_date ≤ asof；歷史回填標 is_approximate=true 並被 strict 模式排除 · strict mode excludes approximate data"],
    ["warn", C.coral, "近似資料警告 · Warnings", "research_mode_approximate_availability 全程顯示，不假裝是 true-PIT · never pretends to be true-PIT"],
    ["shield", C.gold, "Fail-closed by default", "資料不足、過取樣、checksum 不符一律 fail-closed，絕不輸出誤導的 computed · never a misleading computed"],
  ];
  he.forEach((r, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * 6.15, y = 2.5 + row * 1.95;
    card(s, x, y, 5.85, 1.78, { fill: C.panel, accent: r[1] });
    iconCircle(s, x + 0.3, y + 0.34, 0.74, r[1], r[0]);
    s.addText(r[2], { x: x + 1.26, y: y + 0.3, w: 4.4, h: 0.42, fontFace: F.head, fontSize: 16, bold: true, color: C.txt, align: "left", valign: "middle", margin: 0 });
    s.addText(r[3], { x: x + 1.26, y: y + 0.76, w: 4.4, h: 0.9, fontFace: F.body, fontSize: 10.5, color: C.mute, align: "left", valign: "top", lineSpacingMultiple: 1.18, margin: 0 });
  });

  // ===== 8 — Results: REAL performance report =====
  s = pres.addSlide(); bgBase(s); footer(s, 8);
  kicker(s, M, 0.6, "07 · 真實實驗輸出 Real Experiment Output", C.cyan);
  bititle(s, M, 1.05, 11.9, "模型誠實地輸給 buy-and-hold — 這正是重點", "The model honestly loses to buy-and-hold — that is the point");
  shot(s, M, 2.45, 4.0, 4.0, A + "perf-report.png", C.cyan);
  s.addText("真實 PyTorch 實驗報告 · real run_dl_experiment.py output", { x: M - 0.1, y: 6.55, w: 4.4, h: 0.3, fontFace: F.body, fontSize: 9, italic: true, color: C.faint, align: "center", valign: "middle", margin: 0 });
  const rx = 5.35;
  s.addText([
    { text: "StaticWeights (baseline)  ", options: { color: C.mint, bold: true } }, { text: "OOS-net Sharpe 0.129", options: { color: C.txt } },
    { text: "\nDeepForecast (model)  ", options: { color: C.cyan, bold: true } }, { text: "OOS-net Sharpe 0.092", options: { color: C.txt } },
  ], { x: rx, y: 2.4, w: 7.3, h: 0.85, fontFace: F.body, fontSize: 13, align: "left", valign: "top", lineSpacingMultiple: 1.3, margin: 0 });
  s.addText("訓練後的模型在樣本外淨值上輸給 buy-and-hold：機制證據，非策略勝負，no_alpha_claim。\nMechanism evidence on real data — not a strategy verdict, not an alpha claim.", { x: rx, y: 3.25, w: 7.3, h: 0.8, fontFace: F.body, fontSize: 10.5, italic: true, color: C.coral, align: "left", valign: "top", lineSpacingMultiple: 1.2, margin: 0 });
  card(s, rx, 4.2, 7.3, 2.45, { fill: C.panel, accent: C.gold });
  s.addText("資料正確性驗證 · Data-correctness validation 1990→2026", { x: rx + 0.3, y: 4.35, w: 6.8, h: 0.36, fontFace: F.body, fontSize: 11.5, bold: true, color: C.mute, align: "left", valign: "middle", margin: 0 });
  const dd = [["dot-com 崩盤 / crash", "−49% / −78%"], ["金融海嘯 / GFC", "−57%"], ["COVID 崩盤 / crash", "−34%"], ["2022 升息熊市 / bear", "−25%"]];
  dd.forEach((d, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = rx + 0.3 + col * 3.45, y = 4.78 + row * 0.82;
    s.addShape("roundRect", { x, y, w: 3.3, h: 0.7, rectRadius: 0.06, fill: { color: C.panel2 }, line: { color: C.line, width: 1 } });
    s.addText(d[0], { x: x + 0.18, y, w: 2.0, h: 0.7, fontFace: F.body, fontSize: 10, bold: true, color: C.txt, align: "left", valign: "middle", margin: 0 });
    s.addText(d[1], { x: x + 1.9, y, w: 1.28, h: 0.7, fontFace: F.head, fontSize: 13, bold: true, color: C.coral, align: "right", valign: "middle", margin: 0 });
  });

  // ===== 9 — Showcase dashboard screenshot =====
  s = pres.addSlide(); bgBase(s); footer(s, 9);
  kicker(s, M, 0.6, "08 · Showcase 儀表板 Research Dashboard", C.mint);
  bititle(s, M, 1.05, 11.9, "把研究成果變成可讀的儀表板", "Turning research output into a readable dashboard");
  shot(s, M, 2.5, 7.7, 4.05, A + "ui-h3.png", C.mint);
  const dxr = 8.85;
  [["chart", C.mint, "Leaderboard", "OOS-net Sharpe 排序，baseline 標記 · sorted by OOS-net, baseline flagged"],
   ["diagram", C.cyan, "Allocation / Regime", "risk_on、GROWTH/STEADY 配置 · regime-aware allocation"],
   ["server", C.gold, "Experiment Registry", "research entries、readiness、claim 邊界 · MLOps lineage on screen"],
   ["shield", C.coral, "no_alpha_claim badge", "local_demo_only；靜態 artifact self-claim not_proven · honest by contract"],
  ].forEach((r, i) => {
    const y = 2.5 + i * 1.04;
    iconCircle(s, dxr, y, 0.56, r[1], r[0]);
    s.addText(r[2], { x: dxr + 0.78, y: y - 0.02, w: 3.5, h: 0.32, fontFace: F.head, fontSize: 13, bold: true, color: C.txt, align: "left", valign: "middle", margin: 0 });
    s.addText(r[3], { x: dxr + 0.78, y: y + 0.3, w: 3.6, h: 0.6, fontFace: F.body, fontSize: 9.5, color: C.mute, align: "left", valign: "top", lineSpacingMultiple: 1.1, margin: 0 });
  });
  s.addText("Next.js 靜態匯出，由本地 result-store 生成 · Next.js static export from a canonical local result-store", { x: M, y: 6.75, w: 8.0, h: 0.3, fontFace: F.body, fontSize: 9, italic: true, color: C.faint, align: "center", valign: "middle", margin: 0 });

  // ===== 10 — Quality numbers =====
  s = pres.addSlide(); bgBase(s); footer(s, 10);
  kicker(s, M, 0.6, "09 · 品質與證據 Quality & Evidence", C.mint);
  bititle(s, M, 1.05, 11.9, "可驗證的工程：每個宣稱都有 gate 撐著", "Verifiable engineering — every claim is backed by a gate");
  const q = [
    ["435", "Python 測試通過 / tests pass", "2 skipped", C.mint],
    ["118/118", "Python mutation killed", "突變測試 / mutation", C.cyan],
    ["29/29", "frontend mutation killed", "含 H-3 守門 / incl. H-3", C.coral],
    ["84.12%", "frontend 覆蓋率 / coverage", "52 tests · 0 漏洞 / vulns", C.gold],
    ["88 / 242", "import-linter 檔/依賴 files/deps", "2 契約 KEPT / contracts", C.cyan],
    ["proven", "公開部署證明 / public hosting", "GitHub Pages · 0-pixel VRT", C.mint],
  ];
  q.forEach((it, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = M + col * 4.07, y = 2.5 + row * 2.0;
    card(s, x, y, 3.82, 1.78, { fill: C.panel, accent: it[3] });
    s.addText(it[0], { x: x + 0.3, y: y + 0.2, w: 3.3, h: 0.78, fontFace: F.head, fontSize: 36, bold: true, color: it[3], align: "left", valign: "middle", margin: 0 });
    s.addText(it[1], { x: x + 0.32, y: y + 1.0, w: 3.35, h: 0.34, fontFace: F.head, fontSize: 12.5, bold: true, color: C.txt, align: "left", valign: "middle", margin: 0 });
    s.addText(it[2], { x: x + 0.32, y: y + 1.34, w: 3.35, h: 0.32, fontFace: F.body, fontSize: 9.5, color: C.mute, align: "left", valign: "middle", margin: 0 });
  });

  // ===== 11 — Tech stack =====
  s = pres.addSlide(); bgBase(s); footer(s, 11);
  kicker(s, M, 0.6, "10 · 技術棧 Tech Stack", C.cyan);
  bititle(s, M, 1.05, 11.9, "端到端：研究核心 → 模型 → 前端 → 治理", "End to end — research core → model → frontend → governance");
  const groups = [
    ["研究與模型 · Research & model", C.mint, ["Python 3.13", "PyTorch", "NumPy", "A0 回測引擎", "ExperimentRegistry"]],
    ["前端展示 · Frontend", C.cyan, ["Next.js", "React", "TypeScript", "靜態匯出 / Pages"]],
    ["品質與治理 · Quality & governance", C.gold, ["mypy", "import-linter", "mutation testing", "Chromium VRT", "PBT (Hypothesis)"]],
  ];
  let gy = 2.45;
  groups.forEach((g) => {
    s.addShape("rect", { x: M, y: gy + 0.05, w: 0.22, h: 0.3, fill: { color: g[1] } });
    s.addText(g[0], { x: M + 0.36, y: gy, w: 6, h: 0.4, fontFace: F.head, fontSize: 14, bold: true, color: C.txt, align: "left", valign: "middle", margin: 0 });
    let cx = M, cy = gy + 0.52;
    g[2].forEach((t) => {
      const cw = 0.42 + t.length * 0.135;
      if (cx + cw > W - M) { cx = M; cy += 0.64; }
      s.addShape("roundRect", { x: cx, y: cy, w: cw, h: 0.5, rectRadius: 0.25, fill: { color: C.panel }, line: { color: g[1], width: 1 } });
      s.addText(t, { x: cx, y: cy, w: cw, h: 0.5, fontFace: F.body, fontSize: 11.5, bold: true, color: C.txt, align: "center", valign: "middle", margin: 0 });
      cx += cw + 0.22;
    });
    gy = cy + 0.92;
  });

  // ===== 12 — Skills =====
  s = pres.addSlide(); bgBase(s); footer(s, 12);
  kicker(s, M, 0.6, "11 · 展示的能力 Skills Demonstrated", C.coral);
  bititle(s, M, 1.05, 11.9, "這個作品集證明了什麼", "What this portfolio demonstrates");
  const sk = [
    ["brain", C.mint, "ML 工程 · ML engineering", "framework-free → 真實 PyTorch，理解而非堆疊框架 · understanding over stacking"],
    ["layers", C.cyan, "軟體架構 · Architecture", "import-linter 強制邊界，核心與框架解耦 · enforced boundaries"],
    ["flask", C.gold, "測試嚴謹度 · Test rigor", "PBT、mutation、VRT、smoke — 把「CI 會抓到」當成自己的責任"],
    ["server", C.coral, "MLOps lineage", "ExperimentRegistry 確定性追蹤 + 可重現 artifact · reproducible"],
    ["code", C.cyan, "全端整合 · Full-stack", "後端研究核心一路接到 Next.js 互動 dashboard"],
    ["scale", C.mint, "研究誠實 · Research honesty", "no_alpha_claim、OOS-net、fail-closed — 對結果說真話"],
  ];
  sk.forEach((r, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col * 6.15, y = 2.5 + row * 1.42;
    card(s, x, y, 5.85, 1.26, { fill: C.panel, accent: r[1] });
    iconCircle(s, x + 0.3, y + 0.32, 0.62, r[1], r[0]);
    s.addText(r[2], { x: x + 1.12, y: y + 0.18, w: 4.5, h: 0.36, fontFace: F.head, fontSize: 14, bold: true, color: C.txt, align: "left", valign: "middle", margin: 0 });
    s.addText(r[3], { x: x + 1.12, y: y + 0.56, w: 4.55, h: 0.6, fontFace: F.body, fontSize: 10, color: C.mute, align: "left", valign: "top", lineSpacingMultiple: 1.1, margin: 0 });
  });

  // ===== 13 — Closing =====
  s = pres.addSlide(); bgBase(s);
  s.addShape("rect", { x: 0, y: 0, w: W, h: H, fill: { color: C.bg } });
  s.addShape("rect", { x: 0, y: 0, w: W, h: 0.06, fill: { color: C.mint } });
  nodes(s, [[0.9, 5.7], [2.0, 6.3], [3.1, 5.8], [4.2, 6.5]], C.teal);
  s.addShape("ellipse", { x: 11.4, y: 4.9, w: 1.7, h: 1.7, fill: { color: C.cyan, transparency: 88 } });
  iconCircle(s, M, 1.4, 0.95, C.mint, "cap");
  kicker(s, M, 2.7, "Thank you · 深度學習課程作品集 / Course Portfolio", C.mint);
  s.addText("把模型做出來不難，難的是對自己的結果誠實。", { x: M, y: 3.1, w: 11.8, h: 0.75, fontFace: F.head, fontSize: 30, bold: true, color: C.txt, align: "left", valign: "middle", margin: 0 });
  s.addText([
    { text: "Building a model is easy — being ", options: { color: C.txt } }, { text: "honest", options: { color: C.mint, bold: true } }, { text: " about its results is the hard part.", options: { color: C.txt } },
  ], { x: M, y: 3.85, w: 11.8, h: 0.6, fontFace: F.head, fontSize: 21, bold: true, align: "left", valign: "middle", margin: 0 });
  s.addText("framework-free 參考模型 → 真實 PyTorch 訓練 → 互動研究 UI，全程 no_alpha_claim · OOS-net · fail-closed.", { x: M, y: 4.7, w: 11.4, h: 0.5, fontFace: F.body, fontSize: 13, color: C.cyan, align: "left", valign: "middle", margin: 0 });
  s.addShape("roundRect", { x: M, y: 5.5, w: 5.7, h: 0.6, rectRadius: 0.3, fill: { color: C.panel2 }, line: { color: C.mint, width: 1 } });
  s.addText("YC Chang · ycchang.pmp@gmail.com", { x: M, y: 5.5, w: 5.7, h: 0.6, fontFace: F.body, fontSize: 13, bold: true, color: C.txt, align: "center", valign: "middle", margin: 0 });

  await pres.writeFile({ fileName: "QuantLab-EpicH-DeepLearning-Portfolio.pptx" });
  console.log("WROTE bilingual deck (13 slides, 2 screenshots embedded)");
}
main().catch((e) => { console.error(e); process.exit(1); });
