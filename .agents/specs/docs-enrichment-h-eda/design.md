# 架構設計 — docs-enrichment-h-eda

> 參照：本 spec 的 [requirements.md](./requirements.md)（REQ-DOCENRICH-001/002/004/006、REQ-DLEDA-001、REQ-FUTWORK-001）。Source-of-truth DL 數字來自 committed artifacts：`.agents/specs/real-data-oos-backtest/reports/{real-data-oos-artifact,multi-cycle-family-oos-artifact}.json`、`quantlab/research/{model_performance_report,model_report_viz,multi_cycle_oos,real_data_oos}.py`、`quantlab/models/{dl_forecaster.py,dl/{backends,torch_trainer}.py}`、`quantlab/showcase/{scenario,rerun_service}.py`。

## 概述

純文件交付：把已部署的能力（Epic A–H，重點 Epic H 深度學習）用「圖文並茂 + 誠實邊界」呈現到 stakeholder 敘述層。**不新增任何 runtime contract、API、dependency 或 deploy-coupled payload**。

## 架構

三類產出，全部落在既有敘述層 + 新 asset 檔：

1. **示意圖（inline SVG，新繪）**
   - **Capability/data-flow map**：A0 → B(data/PIT) → C(portfolio) → D(model families) → E(MLOps Tier3) → F(showcase) → G(alt-data) → H(deep-learning) 的能力地圖，標 `no_alpha_claim`。→ review + manual。
   - **Epic H pipeline 圖**：`vintage data → NumpyMLPForecaster (reference) │ torch_trainer (lazy, optional) → model_performance_report → model_report_viz (SVG) → showcase dashboard (static_replay) → rerun_service (live_compute)`。→ manual Flow 7–9 + review。
   - **DL OOS-net 排行條圖**：multi-cycle 真實數字（Regime 0.669 / BuyAndHold 0.657 / Forecast 0.354 / Robust 0.321）水平 bar SVG，baseline 標示，附 `no_alpha_claim`/OOS-net-only/非 verdict caption。→ review + manual。

2. **DL EDA 內容（prose，新增段落）**：方法（reference MLP 架構、framework isolation/honest fallback、torch 平價）、指標（report 計算項 + SVG 四面板）、真實觀察（multi-cycle + single-window 排行、approximate-availability 邊界）、H-3 static_replay vs H-4 live_compute、Lane 2 charter-gated。

3. **Future-work roadmap（本 spec roadmap 章節 + NEXT_STEPS pointer）**。

### 技術選型 (Ponytail Rung 2–6)

- **Rung 1**：圖/內容/roadmap 三者皆有 `/goal` 明確需求 → 需存在。
- **Rung 2–4（不引入新 dependency）**：是否需要 charting library（Chart.js / D3 / matplotlib→png）？**否**。`docs/manual/assets/chart.umd.min.js`(Chart.js) 只服務 live dashboard，不該為靜態文件圖引入 runtime；repo 既有 `quantlab/research/model_report_viz.py` 已證明「hand-authored 自足 SVG」是此 repo 的 canonical 慣例（no CDN、file://+headless 可渲染）。
- **Rung 5–6**：示意圖以**手寫最小 inline SVG**（`<svg><rect/><line/><polyline/><text/>`）完成，無外部資源、無 build step。DL 排行條圖數值直接硬編自 committed artifact（單一真實來源），不在文件端重算。
- **結論**：零新 dependency、零新 contract、零 deploy-coupled 變更。

## Test Coverage Declaration

本 spec 無產品程式碼，故「驗證」= 文件正確性 gate（非單元測試）：

- **Governance guards**（authority）：`uv run pytest tests/quantlab/test_governance_guards.py -q` 維持 **25 passed**（涵蓋 count/payload/hosting/visual sync、stale-marker、payload-parity）。real-wired，不是 mock。
- **HTML well-formed**：對 `docs/review/index.html` + `docs/manual/{en,zh-tw}/index.html` 跑 `html.parser` 解析無殘留 tag stack。
- **Frozen-payload assertion**：`git diff --name-only` 不得含 Key Locked Decisions 列出的任何凍結檔。
- **數字真實性**：每個文件端 DL 數字須能對回 committed artifact JSON（人工 crosswalk + 引用路徑）。
- **EN/ZH 同步**：每個新增 EN 區塊須有對應 ZH。
- 無 critical journey 需 live backend；本交付不觸及 auth/data runtime。mock/fixture：不適用（無測試替身）。

## Repo-side Closure vs External Execution Boundary

- **Repo-side（全部）**：SVG/prose/roadmap/guide 編寫 + guard 驗證 + PR。
- **External**：無。合併後 Pages 會自動重建（docs/ 變更），但因 `showcase.json`/manifest 凍結，`dataHash 6c18e572` 不變、committed probe 仍 proven → **不需** `--live` 重證（與前次 PR #137 docs-only 合併同模式）。
- **Authoritative handoff**：無外部 handoff；closeout 由本 spec `review.md` 裁決。

## 契約定義 (Contracts)

**無新契約。** 不在 `contract/` 新增或修改任何定義（doc deliverable）。DL 數字的 SSOT 是既有 committed report JSON artifacts（上方 overview 路徑）。

## 組件和介面

| 產出 | 落點 | 形式 | SSOT |
|---|---|---|---|
| Capability map SVG | review + manual(en/zh,html) | inline SVG | SPECS.md epic 狀態 |
| Epic H pipeline SVG | manual Flow 7–9 + review | inline SVG | H 程式碼路徑 |
| DL OOS-net 排行條圖 | review + manual | inline SVG（硬編真值） | multi-cycle artifact JSON |
| DL EDA prose | review（H 卡附近）+ manual（H flows）| HTML/MD 文字 | H 程式碼 + report JSON |
| Future-work roadmap | 本 spec `design.md`(下節) + NEXT_STEPS pointer | markdown | 各 spec deferred 註記 |
| Guide 更新 | docs/{MANUAL,REVIEW}_GENERATION_GUIDE.md | markdown 小節 | 本 spec |

## Failure Mode and Effects Analysis (FMEA, lightweight)

| Risk ID | Failure Mode | Effect | Cause | Current Control | Sev | Occ | Det | Planned Response | Task Trace |
|---|---|---|---|---|---|---|---|---|---|
| FMEA-DE-01 | 誤改 deploy-coupled payload/gate/png | dataHash 漂移、hosting 翻 `configured_not_observed`、觸發重部署循環 | 編輯時手滑動到凍結檔 | Key Locked Decisions 清單 + frozen-file 檢查 | High | Low | Med | **Prevent/Detect**：編輯後 `git diff --name-only` 比對凍結清單；只動 narrative HTML/MD + 新 SVG asset | T-IMPL, T-VERIFY |
| FMEA-DE-02 | DL 數字 overclaim / 杜撰 / 誤呈為 verdict | stakeholder 誤判為 alpha/可投資 | 文件端重算或記憶填數、漏標 `no_alpha_claim` | 硬編自 committed artifact + 強制 caption | High | Med | Med | **Prevent/Contain**：每個數字附 artifact 路徑 crosswalk；每張 DL 圖/段落帶 `no_alpha_claim`+OOS-net-only+非 verdict+approximate 標註；無 current-asof 語句 | T-DLEDA, T-VERIFY |
| FMEA-DE-03 | EN/ZH 漂移（只更新一語） | 雙語讀者看到不一致內容 | 雙語各自編輯遺漏 | EN/ZH 配對編輯 + grep 對齊檢查 | Med | Med | Med | **Detect**：每個新增 EN 區塊確認對應 ZH；closeout grep | T-IMPL, T-VERIFY |
| FMEA-DE-04 | 引入 CDN/外部 `<script src>`/外部圖 | 違反 self-contained、離線/headless 失效、潛在隱私/供應鏈面 | 為了省事用外部 chart lib/圖床 | inline-SVG-only 設計決策 | Med | Low | Low | **Prevent**：手寫 inline SVG；closeout grep 無新 `src=`/`http`/CDN | T-IMPL, T-VERIFY |
| FMEA-DE-05 | 破壞 HTML 結構（minified 行誤改） | 頁面渲染壞掉 | 在長 minified 行插入 SVG 出錯 | well-formed 解析 gate | Med | Low | Low | **Detect**：每次改後 `html.parser` 解析；保留 sibling tag 結構 | T-VERIFY |
| FMEA-DE-06 | Future-work 承諾超出 charter（暗示要做 Lane 2 actionable signal） | 違反 `no_alpha_claim` charter | roadmap 寫成產品承諾 | charter 邊界標註 | High | Low | Med | **Prevent/Contain**：roadmap 每項標 charter/honesty 邊界；Lane 2 明列為 deferred、charter-gated；不發明未被 spec/charter 支撐的承諾 | T-FUTWORK |

### Risk Response and Mitigation Plan（高風險）

- **FMEA-DE-01 / -02 / -06（High）**：均採 Prevent + Detect/Contain；任一 detect 失敗即保守降級（寧可不加圖/不寫數字，也不誤改凍結檔或 overclaim）。對應 task 在 `tasks.md` 明列 verify 步驟。

## 錯誤處理

- 若某 SVG 一定要改到 deploy-coupled 檔才能呈現 → 放棄該呈現，改 narrative-only（REQ-DOCENRICH-004 AC4）。
- 若 guard 因新增內容失敗 → 視為 stale-marker/格式違規，回退並修正，不改 guard。
- 若某數字無法對回 committed artifact → 不寫該數字。

## 評估標準 (EDD)

- 全 6 個 REQ 的 AC 滿足；guards 25 passed；凍結檔未動；EN/ZH 同步；inline-SVG-only；`no_alpha_claim` 全程；HTML well-formed。

## Future-Work Roadmap（REQ-FUTWORK-001 authoring 位置）

> 本節是 roadmap 的 SSOT；`NEXT_STEPS.md` 只放 pointer + 高階指標。每項標 charter/honesty 邊界，且僅蒐集**已被既有 spec/charter 支撐**的 deferred 項目，不發明新承諾。

| ID | 主題 | 來源 deferred 註記 | Charter / Honesty 邊界 | 相依 / 優先序（指示性） |
|---|---|---|---|---|
| FW-H-JAXTF | JAX / TensorFlow 真實訓練後端 | H-1/H-2 deferred；backend registry 已留 `jax`/`tensorflow` label + honest fallback | framework-isolation 不可破；`no_alpha_claim`；optional lane（不入 default lock） | 中；接續 H-2 torch lane 模式 |
| FW-H-GPUNATIVE | GPU / 更大 / native models | H-1/H-2 deferred | 仍 OOS-net-only 機制證據；非 production 訊號 | 中；需 FW-H-JAXTF 後端就緒 |
| FW-E-TIER3PROD | Production Tier3（真實 serving / retraining / drift monitoring） | E-tier3-* deferred；CLI 已 fail-closed 要求外部 proof URI | 需 externally-proven HTTPS proof + allowlisted identity scheme；repo 端只能 smoke | 高（價值）但需外部基礎設施 |
| FW-H-LANE2 | Lane 2 actionable current-asof signal（「現在該配置什麼」） | H-4 REQ-H4-008 明列 charter-gated/deferred | **charter-gated**：跨越 `成功=方法論誠實度…非 alpha`，本 charter 下不開放；列此僅為完整性 | 低 / 受 charter 約束（預設不做） |
| FW-RDO-COTEMPORAL | 升級為 strict-PIT、co-temporal、真實 survivorship 的 verdict-grade 比較 | real-data-oos / CR-RDO-005：目前 approximate-availability、mechanism-not-verdict | 在達到 strict PIT 前不得宣稱 strategy verdict | 中；需真實 PIT 資料治理 |
| FW-DOC-VIS | stakeholder 視覺後續（互動圖、更多 EDA 面板、live dashboard 圖文同步） | 本 spec 之延伸 | 維持 self-contained / deploy-coupling policy | 低；本 spec 後的增量 |

## 追溯參照 (Traceability References)

- Design sections → REQ：架構/組件 → REQ-DOCENRICH-001/002；DL EDA → REQ-DLEDA-001；FMEA → REQ-DOCENRICH-004；Roadmap → REQ-FUTWORK-001；Guide → REQ-DOCENRICH-006。
- 供 `RTM.md` 聚合的穩定 id：`docs-enrichment-h-eda` spec row（Phase 5 closeout 時新增）。

## Governance Artifact Lifecycle

- **Upstream truth**：committed H report JSON + H 程式碼（DL 數字）；各 spec deferred 註記（roadmap）。
- **本 spec 產出**：requirements/design/tasks/review（branch-spec truth）；新增的 manual/review 敘述內容與 SVG asset。
- **Derived（只讀/單向）**：`SPECS.md`（新增本 spec row）、`RTM.md`（新增 traceability row）、`NEXT_STEPS.md`（rolling pointer）。皆於 closeout 由 SDD/spec-registry 寫入，不反向改寫 upstream。
- **不得**：讓本 doc spec 改動 deploy-coupled payload 或任何 completed baseline 的行為。
