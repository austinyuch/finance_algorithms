# Finance Algorithms — 使用者操作手冊（繁體中文）

> QuantLab 研究平台與既有金字塔計算機的操作手冊。產品操作面：**Backend /
> Tool / CLI 主導的 Hybrid**。Readiness 結論一律沿用
> `.agents/specs/**/review.md`，語意見
> [`EVIDENCE_METADATA_CONTRACT`](../../EVIDENCE_METADATA_CONTRACT.md)。
>
> ⚠️ **Claim cap：** 本專案為個人、純紙上研究 lab。每個模型切片都標註
> `no_alpha_claim`；任何內容都不宣稱獲利能力或已上 production。

## 受眾快速導覽

| 你是… | 從這裡開始 |
|---|---|
| 跑回測的研究者 | [流程 1 — 跑 TSMC 對沖切片](#流程-1--跑-tsmc-對沖切片) |
| 擷取快照的資料操作者 | [流程 2 — 每日 vintage 快照](#流程-2--每日-vintage-快照) |
| 看 dashboard 的審閱者 | [流程 3 — Showcase 儀表板](#流程-3--showcase-儀表板) |
| 既有 API 使用者 | [流程 4 — 金字塔計算機 API](#流程-4--既有金字塔計算機-api) |

## 快速開始 / Starter Assets

```bash
uv sync                      # 安裝 Python 3.13 依賴
uv run pytest -q             # 健檢：預期 249 passed
cd frontend && npm install   # 前端依賴 (Next.js)
```

已 commit 的 seed / 樣本資料：

- `data/vintage/raw/2026-06-09/`、`data/vintage/raw/2026-06-11/` — append-only
  point-in-time FRED + NOAA 快照（不可覆寫）。
- `frontend/lib/showcase-payload.json` — 含 `sourceMetadata.source=local_result_store` 的 generated dashboard payload。
- `frontend/out/showcase.json` — 匯出的 dashboard payload（可下載）。

---

## 流程 1 — 跑 TSMC 對沖切片

**誰／何時：** 研究者想要一份可重現、以 OOS-net 排名、把對沖策略與笨 baseline
並排比較的 leaderboard。

```bash
uv run python scripts/run_tsmc_hedge_slice.py
```

實際輸出（`assets/backend-hedge-slice-01-leaderboard.txt`）：

```
strategy          OOS net Sharpe
--------------------------------
BuyAndHold                0.3911
HedgeStrategy             0.3528
StaticWeights             0.2759
RandomStrategy           -0.0092
```

**怎麼讀：** 以**樣本外淨值**（扣成本後）Sharpe 排名；`RandomStrategy` 是健檢
下限。default UAT/runtime 環境未安裝 optional PyTorch LSTM lane，因此此 transcript
只包含 hedge 與 baseline 策略。本切片使用**合成**共整合資料 — 證明 pipeline 正確，
不證明對沖會賺錢。

> - Evidence Source: `live_command_output`
> - Coverage Tier: `hybrid` · Readiness State: `PASS`（`a-tsmc-hedge-slice/review.md`）
> - `MOCK_DOMINANT_EVIDENCE` — 合成資料；`no_alpha_claim`。

---

## 流程 2 — 每日 vintage 快照

**誰／何時：** 資料操作者擷取當日 point-in-time 總經/價格資料，且不覆寫先前
日期（快照不可變）。

不寫檔、不連網先預覽工作：

```bash
uv run python scripts/daily_snapshot.py --dry-run
```

實際輸出（`assets/backend-daily-snapshot-01-dryrun.txt`，節錄）：

```
[snapshot] available_date=2026-06-11  out=.../data/vintage/raw/2026-06-11  jobs=22  (DRY-RUN)
  DRY  fred_FEDFUNDS
  DRY  yahoo_2330.TW
  DRY  yahoo_idx_TWII
[snapshot] done. ok=0 skip=0 fail=0
```

實際擷取（寫 append-only 檔，逐 source 容錯）：

```bash
uv run python scripts/daily_snapshot.py
uv run python scripts/daily_snapshot.py --report-json > report.json   # CR-B11 機器可讀
uv run python scripts/snapshot_ops_gate.py report.json                # 驗證該次執行
```

**怎麼讀：** 22 個工作涵蓋 FRED 系列、Yahoo fallback 標的與 NOAA ONI。單一
source 失敗不得污染其他擷取。**Stooq 為 opt-in/blocked**（`ISSUE-B3-001`）；
Yahoo fallback 對 `2330.TW`、`^TWII` 已 live 證明。

> - Evidence Source: `live_command_output`
> - Coverage Tier: `hybrid` · Readiness State: repo-side `PASS`（`b-data-platform/review.md`）
> - `CROSS_SPEC_DEMO_DEPENDENCY` — 外部 source；Stooq 預設 blocked。

### Vintage readiness 檢查

```bash
uv run python scripts/run_vintage_slice.py
```

```
macro series : 4  ['CPIAUCSL', 'FEDFUNDS', 'GDPC1', 'UNRATE']
price assets : 1  ['SP500']
[readiness] 真實價格資產不足(<2)→ 跳過回測；待下次 snapshot 累積。
```

這是誠實的 readiness 回報：在累積到 ≥2 個真實價格資產前，寧可延後回測也不
捏造結果。

---

## 流程 3 — Showcase 儀表板

**誰／何時：** 審閱者在瀏覽器檢視 QuantLab leaderboard、配置/regime、再平衡
日期與實驗登錄。

重新匯出 static export，並（選擇性）本地啟動：

```bash
cd frontend
npm run export:public-demo     # 產生 frontend/out/{index.html,showcase.json,...}
npm run smoke                  # 127.0.0.1 本地 HTTP smoke（需 governed port）
```

已 commit 的 export 渲染五個面板：**Leaderboard**（OOS-net Sharpe，
ForecastAllocationStrategy 1.21 對 StaticWeights baseline 0.74）、**Allocation /
Regime**（risk_on，conf 0.60；GROWTH 62% / STEADY 38%）、**Rebalance**（3 個
日期）、**Experiment Registry**（`registry_only`、`no_alpha_claim`）、與
**Evidence**（`local_demo_only`）。

可下載 payload：[`frontend/out/showcase.json`](../assets/showcase.json)。

已擷取真實 chromium-headless 截圖（desktop-1440×900，
`frontend/out/browser-visual.png`，狀態 `proven`）。注意 static export 僅輸出
語意化 HTML、**未**內嵌 app 樣式表，故截圖刻意無 CSS — 它證明渲染與內容，不證明
視覺精緻度。Live `npm run dev` 才會套用 `app/globals.css`。

> - Evidence Source: `live_screenshot`（chromium-headless）+ `static_export` + `canonical_local_result_store`
> - Coverage Tier: `hybrid` · Readiness State: `CONDITIONAL`（`f-demo-hardening/review.md`）；browser visual `PASSED`，CR-FPS-006 regenerated payload 造成 branch-local public-hosting parity 暫為 `configured_not_observed`（`f-public-static-showcase/review.md`）
> - Dashboard 資料由本地 `LocalResultStore` / `ExperimentRegistry` scenario 生成（`no_alpha_claim`、`local_demo_only`），不是 live backend service。
> - 已解決：visual diff 為 repo-baseline pixel-backed（`1089 / 1,296,000`
>   mismatched pixels，threshold `0.001`）；GitHub Actions autonomous
>   `event=schedule` dry-run proof 已有 run `27392471359`。Public-hosting
>   probe 已觀測 HTTP 200 與 deployed manifest contract metadata；export 內嵌 readiness 面板依 dashboard contract 仍保守顯示 `not_proven`，直到 Pages 服務 refreshed `dataHash` 後再更新 parity proof。

---

## 流程 4 — 既有金字塔計算機 API

**誰／何時：** 使用者計算等差/等比投資金字塔下單量。

```bash
cd invest_algorithms
uv run uvicorn api:app --host 127.0.0.1 --port 2224
```

端點：

- `GET /api/pyramidArithmetic`
- `GET /api/pyramidGeometric`

兩者皆接受 budget、價格區間、交易次數、最小單位、sizing 參數、初始單位與
`toCsv`。此模組為**不可變既有基線**，維持不變。

> - Evidence Source: `report_artifact`（`tests/test_algo_pyramid.py`）
> - Coverage Tier: `hybrid` · Readiness State: 穩定既有基線。

---

## 視覺缺口盤點

**自上次檢查以來已解決（2026-06-11 → 2026-06-12）：**

- 測試套件目前為 **249 passed**（PyTorch LSTM proof 移至 optional lane，並新增 current-governance stale-evidence guards）；mypy 現涵蓋 **57** 檔且 clean；mutation spot checks **66/66 configured/killed**，包含 root Torch dependency、stale governance evidence mutations 與 non-self-staling promotion-boundary guard、CR-FPS-001/CR-FPS-002/CR-FPS-003/CR-FPS-007/CR-FPS-008 public-hosting manifest/probe/review-probe/hash/contract/taxonomy drift、stakeholder and app payload copy drift, retired F fixture marker drift、superseded F CR fixture-boundary drift、public probe expected-hash drift、review pytest/frontend-count/audit transcript、import-linter count drift and governance registry row-count drift、CR-B12 scoped source-health overclaim 防護、CR-B18 broad source-quorum overclaim 防護、CR-B19 proof replay 防護，以及 CR-B20 Stooq proof exit/file replay 防護。
- `docs/` 下首次 commit 的 manual/review 文件集。
- **已擷取 live 瀏覽器截圖**（chromium-headless，`browser-visual.png`，狀態 `proven`）— 解決先前「無瀏覽器截圖」缺口。
- **Public-hosting probe 已記錄 HTTP 200 與 deployed manifest contract metadata**（`public-hosting-probe.json`）；CR-FPS-006 regenerated local result-store payload 產生新的 `dataHash`，因此 branch-local deployment parity 正確維持 `configured_not_observed`，直到 Pages 服務 refreshed artifact。
- **Visual diff 已改為 repo-baseline pixel-backed**（`browser-visual-diff.json`：`1089 / 1,296,000` mismatched pixels，threshold `0.001`）— 解決先前 hash-equality 殘留，同時允許 gate 內的少量文字渲染差異。

**未解決的視覺缺口：**

| 缺口 | 嚴重度 | 來源 |
|---|---|---|
| 尚無 CI-managed visual baseline history（目前為 repo baseline） | Low | `f-browser-pixel-baseline/review.md` |
| Stooq source contract 仍與 FRED/Yahoo/NOAA source-quorum proof 分開治理 | Low | `b-data-platform/change-requests/cr-b19-source-quorum-live-proof.md` |
| Static export 內嵌 readiness 面板依 dashboard contract 保守顯示 `not_proven` | Low | `frontend/out/index.html` |
| Vintage 真實資料回測仍延後（<2 價格資產） | Low | `run_vintage_slice.py` 輸出 |
| Stooq source blocked（`ISSUE-B3-001`） | Low | `ISSUE_LOG.md` |

高階缺口分析見 [`docs/review/index.html`](../../review/index.html)。
