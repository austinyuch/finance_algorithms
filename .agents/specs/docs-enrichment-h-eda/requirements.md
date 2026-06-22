# 需求文件 — Showcase/Manual 圖文並茂強化 + Epic H 深度學習探索分析 + Future-Work 規劃

Spec ID: `docs-enrichment-h-eda` · Epic: Docs/Comms (cross-cutting over F + H) · Profile: `default`

## 介紹

這是一個**文件交付 (documentation deliverable)** spec，不改變任何產品行為或 deploy-coupled payload。目標把既有、已部署的能力用「圖文並茂 + 誠實邊界」的方式說清楚，分三個 cohesive facet：

1. **強化 showcase/review 與 user manual 說明文件，使其圖文並茂** — 在 `docs/review/index.html` 與 `docs/manual/{en,zh-tw}/index.{html,md}` 加入 self-contained 內嵌 SVG 示意圖（架構 / data-flow / SDD lifecycle / Epic H pipeline）與 DL 分析圖，並補強解說 prose。
2. **補充 Epic H 深度學習部份的探索分析 (EDA) 內容說明** — 用真實 committed 數據解釋 H-1 reference MLP / H-2 PyTorch / H-3 static-replay / H-4 live-rerun「探索了什麼、OOS-net 機制觀察到什麼」，全程 `no_alpha_claim`。
3. **Future work 規劃** — 把目前 deferred 的 slice（JAX/TF 真實後端、GPU/native models、production Tier3、Lane 2 actionable-signal 等）整理成一份可追溯的 roadmap，落在本 spec 與 `NEXT_STEPS.md`。

> **為何這些需求需要存在 (Ponytail Rung 1)**：使用者透過 `/goal` 明確要求這三個交付面（強化 showcase/manual 圖文並茂、deep learning 探索分析說明、future work 規劃）。現有 manual/review 已有 Flow 1–9 與功能卡，但**偏文字、缺示意圖**，且 Epic H 的「探索分析」只在 spec/report artifact 內，未對 stakeholder 讀者說明；future work 散落在各 spec 的 deferred 註記，無單一 roadmap 視圖。三者皆有確認需求支撐，非 speculative。

## 相依、影響與變更請求 (Dependencies, Impacts & CRs)

- [Depends On: f-public-static-showcase, f-nextjs-showcase-dashboard, f-browser-pixel-baseline, h-deep-learning-research-lab, h-deep-learning-real-training, h-interactive-research-ui, h-live-rerun-api, real-data-oos-backtest]
- [Impacts: 無] — 本 spec 只**附加 (additive)** 文件內容到 stakeholder 敘述層 (manual/review narrative HTML/MD) 與新增 asset 檔，不改變上述任何 completed baseline 的行為、契約、或 deploy-coupled payload。因此**不需要 CR overlay**（純 additive doc enrichment，非 baseline 邏輯變更）。
- [Open Change Requests: 無]

## Repo-side Closure vs External Execution

- **Repo-side Closure**: 全部。內嵌 SVG 圖、DL EDA prose（基於 committed artifact 的真實數字）、future-work roadmap、guide 更新，皆可於本 repo / 工作站完成並通過 governance guards。
- **External Execution**: 無新的外部執行需求。Pages 部署會在合併後自動發生，但本 spec **刻意不改 deploy-coupled payload**，故不觸發 dataHash/probe 重證循環（見 REQ-DOCENRICH-004）。
- **External Blockers / Constraints**: 無。

## Key Locked Decisions（不可違反的邊界）

- **Frozen-payload scope guardrail**：不得 regenerate `docs/showcase.json`、`docs/manual/assets/showcase.json`、`docs/review/assets/showcase.json`、`docs/deployment-manifest.json`、`docs/public-hosting-probe.json`、`docs/index.html`、`docs/manual/assets/dashboard-static-export.html`、`docs/visual-snapshot.json`、`gate-*.txt`、`*.png`、`frontend/visual-baselines/*`。published snapshot 維持 `dataHash 6c18e572` proven、counts 478/70/123。
- **`no_alpha_claim` 全程**：DL EDA 內容只呈現 historical OOS-net 機制 + 可比較性證據，**絕不**產生 buy/sell/current-asof allocation/「現在該買什麼」訊息（Lane 2 charter-gated，屬 future work）。
- **誠實標註**：approximate-availability 資料須標明非 strict PIT、非 strategy verdict；mock/fixture/static-replay vs live 須區分。
- **Self-contained 視覺**：所有新增圖須為內嵌 SVG（no CDN、no `<script src>`、no 外部圖片），與既有 `model_report_viz.py` / dashboard 的 self-contained 慣例一致。
- **EN/ZH 同步**：manual 與 review 的雙語內容須對齊。
- **Governance guards 維持 25 passed**。

## 需求

### 需求 1 [REQ-DOCENRICH-001] — Review/Showcase 文件圖文並茂

**用戶故事：** 作為一個瀏覽 executive review/showcase 的 stakeholder，我希望 `docs/review/index.html` 有示意圖與分析圖搭配文字，以便快速、直覺地理解系統架構、Epic 能力地圖與 DL 分析結果，而非只讀長段文字。

#### 驗收標準

1. When 開啟 `docs/review/index.html`，系統 shall 顯示至少一張 self-contained 內嵌 SVG 架構/能力示意圖（例如 A0→B→C→D→E→F→H 的 capability/data-flow map），含 EN/ZH 標註。
2. When 閱讀 DL 相關段落，系統 shall 顯示至少一張呈現真實 multi-cycle OOS-net 排行（Regime 0.669 / BuyAndHold 0.657 / Forecast 0.354 / Robust 0.321）的內嵌 SVG 圖表，並標註 `no_alpha_claim` / OOS-net-only / 非 verdict。
3. The 新增圖 shall 全部為內嵌 SVG，無任何 CDN、外部 `<script src>` 或外部影像連結。
4. The review HTML shall 維持 EN/ZH 雙語對齊，且通過 HTML well-formed 解析。

### 需求 2 [REQ-DOCENRICH-002] — User Manual 圖文並茂

**用戶故事：** 作為一個操作者/研究者讀 user manual，我希望關鍵 flow（尤其 Epic H 的 Flow 7–9）有示意圖，以便理解資料流與模型管線，而非僅靠文字步驟。

#### 驗收標準

1. When 閱讀 `docs/manual/{en,zh-tw}/index.html`，系統 shall 在 Epic H 相關 flow（deep-learning experiment / interactive research / live rerun）至少新增一張 self-contained 內嵌 SVG 管線示意圖（資料 → reference/torch backend → report/viz → dashboard/live rerun）。
2. The manual EN 與 ZH 版本 shall 各自含對應圖與說明，內容對齊。
3. The `.md` 版本 shall 以對應方式補充（內嵌 SVG 或對既有 `docs/manual/assets/*` 圖的引用），不得只有 HTML 有圖而 MD 落差。
4. The 新增內容 shall 不修改 deploy-coupled 的 `dashboard-static-export.html` 與 `docs/manual/assets/showcase.json`。

### 需求 3 [REQ-DLEDA-001] — Epic H 深度學習探索分析內容

**用戶故事：** 作為一個技術 stakeholder，我希望有一段「Epic H 探索分析 (EDA)」說明，解釋 DL lab 探索了什麼、用什麼方法、在真實資料上觀察到什麼 OOS-net 機制結果，以便理解這部分的研究價值與誠實邊界。

#### 驗收標準

1. The 內容 shall 說明 reference MLP 架構（單隱藏層、4 units、tanh、full-batch GD、可設定 epochs、固定 seed、numpy-only、deterministic）與 framework-isolation/honest-fallback（torch/jax/tf lazy、不可用時誠實退回 reference、never raises）。
2. The 內容 shall 說明 performance report 計算的指標（OOS-net Sharpe、報酬分佈 mean/vol/skew/kurtosis/VaR5%、rolling Sharpe、drawdown、learning curve、checksum、fail-closed on degenerate）與 self-contained SVG viz 的四面板（equity/drawdown/learning-curve/return-histogram）。
3. The 內容 shall 呈現真實 committed 數據：multi-cycle (2000–2026, 5 tickers {2330.TW,SPY,^GSPC,^IXIC,^TWII}, 317mo co-temporal, 4 cycles dot-com/GFC/COVID/2022) 的 OOS-net 排行，與 single-window SP500 (2016–2026, ~120mo) 的 BuyAndHold 0.877 / SmaTiming 0.808，並標明 `approximate_event_date`（非 strict PIT）、mechanism+comparability、非 strategy verdict。
4. The 內容 shall 區分 H-3 `static_replay`（重播既有 artifact 的 DeepForecast 0.91 vs StaticWeights 0.63 leaderboard）與 H-4 `live_compute`（從 validated params 真實重算、deterministic checksum），並重申 Lane 2 actionable-signal 為 charter-gated/deferred。
5. The 內容 shall 全程 `no_alpha_claim`，不得出現任何 current-asof allocation / buy-now / 投資建議語句。

### 需求 4 [REQ-DOCENRICH-004] — Frozen-payload 與 guard 安全

**用戶故事：** 作為維護者，我希望這次文件強化不會觸發 dataHash/Pages 重部署循環、也不破壞既有 governance guards，以便這是一次乾淨、低風險的 docs-only 交付。

#### 驗收標準

1. The 變更 shall 不修改 Key Locked Decisions 列出的任何 deploy-coupled payload/gate/png/baseline 檔。
2. When 執行 `uv run pytest tests/quantlab/test_governance_guards.py -q`，系統 shall 維持 25 passed / 0 failed。
3. The published snapshot shall 維持 pytest 478 / frontend 70 / mutation 123/123、`dataHash 6c18e572` proven（不被本 spec 改動）。
4. If 任一新增圖或文字會改到 deploy-coupled 檔，則系統 shall 改採 narrative-only 或新 asset 檔的方式，而非改動凍結檔。

### 需求 5 [REQ-FUTWORK-001] — Future-Work Roadmap

**用戶故事：** 作為規劃者，我希望有一份整合的 future-work roadmap，把目前散落於各 spec 的 deferred 項目集中、分群、標示優先序與 charter 邊界，以便後續 slice 規劃有單一視圖。

#### 驗收標準

1. The roadmap shall 蒐集並分群目前已知 deferred 項目，至少涵蓋：JAX/TF 真實訓練後端、GPU/native models、production Tier3（real serving/retraining/drift）、Lane 2 actionable-signal（charter-gated）、以及 stakeholder-doc/視覺後續。
2. Each roadmap 項目 shall 標註其 charter/honesty 邊界（特別是 Lane 2 為 deferred、`no_alpha_claim`）與大致相依/優先序。
3. The roadmap shall 落在本 spec 的 artifact（roadmap 章節或 `design.md`）並在 `{workspace}/.agents/specs/NEXT_STEPS.md` 留下高階指標 + 指向本 spec 的 pointer（不複製全文）。
4. The roadmap shall 與既有 spec 的 deferred 註記一致，不得發明未被任何 spec/charter 支撐的承諾。

### 需求 6 [REQ-DOCENRICH-006] — 生成指南與 AGENTS 備忘

**用戶故事：** 作為後續維護者，我希望 manual/review 生成指南記錄了這次圖文並茂強化與 DL EDA 內容的來源與更新規則，以便日後可重現、可維護。

#### 驗收標準

1. The `docs/MANUAL_GENERATION_GUIDE.md` 與 `docs/REVIEW_GENERATION_GUIDE.md` shall 各新增簡短小節，說明圖文並茂 SVG 圖與 Epic H EDA 內容的 source-of-truth（committed H artifacts / report JSON）與更新規則，並維持既有 deploy-coupling policy 段落不變。
2. The `AGENTS.md` shall 以簡短一句指向這兩份 guide（若既有指引已涵蓋則確認其充分性，不重複膨脹）。

## 成功標準 (Success Criteria)

- review + manual（EN/ZH、html+md）圖文並茂，含 self-contained SVG 圖；DL EDA 內容用真實 committed 數字、誠實標邊界；future-work roadmap 集中可追溯。
- governance guards 25 passed；deploy-coupled payload 凍結（dataHash 6c18e572 proven、counts 478/70/123 不變）；EN/ZH 同步；`no_alpha_claim` 全程；HTML well-formed。

## 邊緣情況與約束

- SVG 圖須在 file:// 與 headless 渲染（與既有 viz 慣例一致），不依賴外部資源。
- 真實數字一律引用 committed artifact，不得四捨五入到失真或杜撰。
- 若 manual/review 既有圖（`docs/manual/assets/*.png`）足以說明，可引用而非重畫，但 Epic H pipeline / capability map 這類「說明性示意圖」傾向新繪內嵌 SVG（避免動到 deploy-coupled png）。
- Lightweight FMEA 於 Phase 2 必做（本 spec 產出 stakeholder-facing artifact，觸發 Global Constraint #12）。
