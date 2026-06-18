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
| 跑真實資料 OOS-net 回測的研究者 | [流程 5 — 真實資料 OOS-net 回測](#流程-5--真實資料-oos-net-回測) |
| 研究多個景氣循環的研究者 | [流程 6 — 歷史回補與多週期研究](#flow-6--historical-backfill--multi-cycle-study-cr-b21) |
| 訓練深度模型（真實 PyTorch）的研究者 | [流程 7 — 深度學習實驗](#流程-7--深度學習實驗epic-h真實-pytorch) |
| 從 dashboard 探索 Epic H 的審閱者 | [流程 8 — 互動研究 UI](#流程-8--互動研究-uiepic-h切片-h-3) |

## 快速開始 / Starter Assets

```bash
uv sync                      # 安裝 Python 3.13 依賴
uv run pytest -q             # 健檢：預期 435 passed, 2 skipped
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
npm run smoke                  # 127.0.0.1 自動選 port 的本地 HTTP smoke
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
> - Coverage Tier: `hybrid` · Readiness State: `CONDITIONAL`（`f-demo-hardening/review.md`）；browser visual `PASSED`；public hosting 現為 `proven` / `matched`，deployed==expected `dataHash c33da57d11c48945abcee36f2c78eb377f793536f769ddb10b87e8e4b3c7462a…`，在 2026-06-18 `main` 部署之後（`docs/public-hosting-probe.json`）
> - Source Ref: `.agents/specs/f-demo-hardening/review.md`、`.agents/specs/f-public-static-showcase/review.md`、`docs/deployment-manifest.json`
> - Dashboard 資料由本地 `LocalResultStore` / `ExperimentRegistry` scenario 生成（`no_alpha_claim`、`local_demo_only`），不是 live backend service。
> - 已解決：visual diff 為 repo-baseline pixel-backed（`1077 / 1,296,000`
>   mismatched pixels，threshold `0.001`），export readiness 面板現回報
>   `visualRegression=proven`（CR-FPS-009）。Public-hosting probe 現觀測到 HTTP 200
>   與 manifest-contract metadata，且 deployed hash 相符
>   （`status=proven`、deployed==expected `dataHash c33da57d11c48945abcee36f2c78eb377f793536f769ddb10b87e8e4b3c7462a…`，在 2026-06-18 `main` 部署之後）；freshness 現為 deterministic，過期證據會降級
>   而非 crash（CR-FPS-011）。Dashboard payload 自身的 `publicHosting` self-claim
>   依設計**維持 `not_proven`** — static artifact 不能自我宣稱其部署；`proven` 狀態
>   僅存在於觀測到的 probe/manifest，且為 point-in-time。

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

## 流程 5 — 真實資料 OOS-net 回測

**誰／何時：** 研究者在**真實 point-in-time vintage 資料**（非合成）上跑回測，
比較一個候選策略與笨 baseline，依樣本外**淨值** Sharpe 排名。自 CR-B21 deep
backfill（見流程 6）起，預設的 approximate run 現在會選取 **12 資產的 co-temporal
universe**，取代先前僅 SP500 的切片。

```bash
uv run python scripts/run_real_data_oos_backtest.py --out /tmp/rdo-demo.json
```

實際輸出（`assets/real-data-oos-demo-01-run.txt`；完整 artifact 見
`assets/real-data-oos-demo-02-artifact.json`）：

```
EXIT=0
status            = computed
asset_set         = 12 co-temporal assets
                    (^GSPC, ^IXIC, SPY, AGG, TLT, GLD, DBC, BTC-USD, 2330.TW, ^TWII, TWD=X, SP500)
availability_mode = approximate_event_date   (NOT true PIT)
metric_authority  = out_of_sample_net_only
asof_window       = 2016-06-13 .. 2026-06-12   (co-temporal window；深度 1990+ 歷史
                    可用 — 見流程 6 — 但共同窗口由最年輕的資產 BTC-USD 釘住)
rows（依 OOS-net Sharpe 排名）：
  BuyAndHold        1.2664   (baseline)
  RandomStrategy    1.0860
```

**怎麼讀：** 本切片組合既有 A0 engine + PIT vintage provider，跑在**真實**多資產
資料上。候選策略（當 ≥2 個資產符合資格時的 cross-sectional `RandomStrategy`）扣
成本後並未勝過 buy-and-hold。這是**真實 source 資料上的 mechanism 證據 — 不是策略
勝負判定、也不是 alpha 宣稱**。CLI 使用 `approximate_event_date` availability（讓
vintage 對歷史 as-of 可見）；artifact 明確記錄此模式，因為它**非 true PIT**，可能
引入 lookahead。

### Fail-closed 誠實守門

CLI 絕不輸出誤導性的 `computed`。兩個 guard 會 fail closed（exit 2，
`status=insufficient_data`）：

```
# CR-RDO-004 sampling-frequency oversampling（daily+monthly 混合 universe，
# monthly rebalance 會把陳舊價格 forward-fill 成捏造的 flat returns）
[fail-closed] oversampled real-data OOS: rebalance cadence 'monthly' is finer ...
  → reason=oversampled_vs_native_frequency   EXIT=2

# Degeneracy（true-PIT 單次擷取資料對歷史 as-of 不可見 → flat OOS）
[fail-closed] degenerate real-data OOS: all strategy OOS net return series are flat ...
  → reason=degenerate_flat_oos   EXIT=2
```

預設 run 的 12 個 co-temporal 資產皆為 daily-native（`coarsest_cadence=daily`、
`rebalance=monthly`），兩個 guard 都通過、維持 `computed`。

> - Evidence Source: `live_command_output` + `report_artifact`（live 12 資產
>   擷取 `assets/real-data-oos-demo-02-artifact.json`；spec 較早的 single-index
>   canonical run 已 commit 於
>   `.agents/specs/real-data-oos-backtest/reports/real-data-oos-artifact.json`，
>   checksum `421c7fd2…`）
> - Coverage Tier: `hybrid` · Readiness State: `PASS` — *Implemented · Review
>   PASSED*（`real-data-oos-backtest/review.md`）；live-demo readiness `not_assessed`
>   （CLI/library 切片，無 served surface）
> - Source Ref: `.agents/specs/real-data-oos-backtest/review.md`、
>   `.../change-requests/cr-rdo-003-market-index-availability.md`、
>   `.../change-requests/cr-rdo-004-sampling-frequency-guard.md`、
>   `.../b-data-platform/change-requests/cr-b21-historical-backfill.md`
> - Captured：2026-06-15 live 重跑 CLI（真實 vintage 資料）— 計算出的 12 資產
>   co-temporal run（universe 由 CR-B21 backfill 從僅 SP500 擴展）加上兩條
>   fail-closed 路徑（degeneracy、CR-RDO-004 sampling-frequency）；非 byte-for-byte。
> - `MOCK_DOMINANT_EVIDENCE` — 真實 CLI 輸出，跑在真實但 local-only 的 vintage
>   資料上，`availability_mode=approximate_event_date`（非 true PIT）；
>   `no_alpha_claim`，mechanism 而非策略判定。

---

## Flow 6 — Historical backfill & multi-cycle study (CR-B21)

**誰／何時：** 研究者想要研究**多個景氣循環**（2000 年 dot-com 崩盤、2008 GFC、
COVID、2022）— 這是少數即時每日快照無法提供的涵蓋範圍。CR-B21 將深度歷史
（Yahoo `period1=1990`、完整 FRED 系列、NOAA ONI）回補到
`data/vintage/raw/backfill-1990-01-01/`。

```bash
uv run python scripts/backfill_history.py --since 1990-01-01   # idempotent
```

**誠實邊界（不可妥協）：** 今天抓取的歷史**非 true point-in-time** — 每筆記錄皆為
`is_approximate=true` + `backfill=true`（`available_date`=擷取日期；FRED 總經為
latest-*revised*）。**Strict PIT 模式完全排除此 backfill**；只有
`approximate_availability=True`（research 模式）才會曝露它，且置於 `no_alpha_claim`
下。它從不把任何東西變成 true-PIT，也從不宣稱 alpha。

Manifest + deep 多週期回測（`assets/backend-historical-backfill-01-demo.txt`）：

```
_backfill_manifest.json : approximate=true, claim_boundary=no_alpha_claim,
                          since=1990-01-01, ok+skip=24/24, fail=0
residual completed (idempotent re-run, 2026-06-16) — 已補齊 6 條 FRED rate/FX
系列：DGS10, DGS2, T10Y2Y, NASDAQCOM, DCOILWTICO, DEXTAUS
  → T10Y2Y 已可用，regime family 現以 full-feature 執行

deep {^GSPC, ^IXIC} 1990-01-02 → 2026-06-12 (437 months), status=computed:
  BuyAndHold         oos_net_sharpe = 0.7007  (baseline)
  SmaTimingStrategy  oos_net_sharpe = 0.2264
```

**資料驗證**（`assets/backend-historical-backfill-02-drawdowns.txt`）— 回補的歷史
不僅是*存在*，而且歷史上*正確*；peak-to-trough 跌幅與真實紀錄相符：

| Regime | Index | Max drawdown |
|---|---|---|
| Dot-com crash | `^GSPC` / `^IXIC` | −49.1% / −77.9% |
| Global Financial Crisis | `^GSPC` | −56.8% |
| COVID crash | `^GSPC` | −33.9% |
| 2022 rate-hike bear | `^GSPC` | −25.4% |

`^GSPC` 涵蓋：**9,179 daily rows，1990-01-02 → 2026-06-12**。

> - Evidence Source: `report_artifact`（`_backfill_manifest.json`、
>   `cr-b21-deep-cycle-1990-oos-artifact.json`）+ `live_command_output`
> - Coverage Tier: `hybrid` · Readiness State: `PASS` — *Implemented · Review
>   PASSED（repo-side + live run）*（`b-data-platform/review.md`，CR-B21）
> - Source Ref: `.agents/specs/b-data-platform/change-requests/cr-b21-historical-backfill.md`、
>   `.agents/specs/b-data-platform/review.md`
> - Captured：2026-06-15 live CLI run，residual 由 idempotent re-run 於 2026-06-16
>   補齊；全部 24/24 sources 擷取，fail=0（先前 FRED 限流的 6 條 rate/FX 系列含
>   `T10Y2Y` 現已齊備 → regime family full-feature）。
> - `MOCK_DOMINANT_EVIDENCE` — 真實抓取的歷史但 `is_approximate=true` research
>   資料（非 true PIT），strict-excluded；`no_alpha_claim`。

---

## 流程 7 — 深度學習實驗（Epic H，真實 PyTorch）

**誰／何時：** 研究者想端到端透過回測引擎訓練一個深度模型，並以樣本外淨值指標
與笨 baseline 比較 —「設定參數 → 執行 → 看結果」的機制。

```bash
uv run python scripts/run_dl_experiment.py --backend pytorch \
  --symbols '^GSPC' '^IXIC' --hidden-units 8 --lookback 6 --epochs 40 --seed 0 \
  --out out/dl-demo/exp-torch-gspc-ixic.json --viz out/dl-demo/exp-torch-gspc-ixic.svg
```

實際輸出（`assets/backend-dl-experiment-01-demo.txt`）：

```
status=computed  backend=pytorch  experiment_id=1e893d7d…
learning curve : 0.9997 → 0.9975  (40 epochs，單調下降 → 模型確實有訓練)

OOS-net 排行榜（僅以 OOS-net 排名；baseline 可見）：
  StaticWeights (buy & hold)        oos_net_sharpe = +0.1292   maxDD = −65.4%   [baseline]
  DeepForecastAllocationStrategy    oos_net_sharpe = +0.0919   maxDD = −71.0%   [model]
```

**如何解讀：** 裝了 PyTorch 後，`pytorch` backend 以 torch autograd（float64）真實訓練
MLP，位於 lazy backend 邊界之後 — engine/data 核心永不匯入框架。訓練後的模型在
OOS-net Sharpe 上誠實**輸給** buy-and-hold：這正是重點 —`no_alpha_claim`、機制證據，
非策略判定。沒有 torch 時，同一呼叫降級為 deterministic 的 `reference` backend（永不
raise）。深度歷史為 CR-B21 近似 backfill（非 true PIT；strict 模式排除）。

> - Evidence Source：`report_artifact`（`out/dl-demo/exp-torch-gspc-ixic.json`，
>   checksum `b73b21e9…`）＋ `live_command_output`
> - Coverage Tier：`hybrid` · Readiness State：`PASS` —《Implemented · Review
>   PASSED（repo-side + torch UAT）》（`h-deep-learning-real-training/review.md`）
> - `MOCK_DOMINANT_EVIDENCE` — 真實 torch 訓練於 `is_approximate=true` research
>   資料（非 true PIT）；選用 torch lane；`no_alpha_claim`。

---

## 流程 8 — 互動研究 UI（Epic H，切片 H-3）

**誰／何時：** 審閱者想從 showcase 儀表板**探索** Epic H 深度學習切片 — 調整參數、
讀取 model-vs-baseline 排行榜與圖表 — 而不啟動 live 訓練工作。H-3 是對既有 H
artifacts 的 deterministic **static replay**（尚無 live backend rerun）。

```bash
cd frontend
npm run export:public-demo     # 重新匯出 dashboard（含 interactiveResearch 區塊）
npm run e2e:interactive        # 真實 Chromium/Next.js：改 seed → computed → fail_closed → VRT
```

儀表板的 **Interactive Research** 面板曝露 H 實驗參數與 deterministic 結果：

```
parameters : backend=reference  hiddenUnits=4  lookback=6  epochs=20  seed=0
             rebalance=monthly  symbols=[GROWTH, STEADY]
ranges     : hiddenUnits 2..64 · lookback 3..24 · epochs 5..200 · seed 0..999
             rebalance {monthly, quarterly} · backend {reference, pytorch, jax, tensorflow}
mode       : static_replay        status : computed
metric_authority : out_of_sample_net_only        claim_boundary : no_alpha_claim

OOS-net 排行榜（僅以 OOS-net 排名；baseline 可見）：
  DeepForecastAllocationStrategy   oos_net_sharpe = 0.91   maxDD = -16%   [model]
  StaticWeights                    oos_net_sharpe = 0.63   maxDD = -19%   [baseline]

data lineage : source=cr_b21_approximate_backfill  window 2018-01 .. 2022-12
               approximateAvailability=true  strictPitExcluded=true
               warning=research_mode_approximate_availability
```

**怎麼讀：** 面板僅以樣本外**淨值** Sharpe 排名，且永遠保留笨 `StaticWeights`
baseline 可見。每一列都帶有 equity-curve、drawdown、return-distribution，以及
（model 列）learning-curve 序列。資料 lineage 是 CR-B21 `is_approximate=true`
backfill，因此面板顯示 `research_mode_approximate_availability` 警告 — 它是 research
replay，**非** true PIT、**非** alpha 宣稱。

### Fail-closed 行為

要求超出公布 range 的參數集合，或 report checksum 不再相符的 payload，會把面板翻成
`status=fail_closed`，而非渲染陳舊或捏造的結果。`npm run e2e:interactive` 瀏覽器流程
正是驅動這條路徑（`computed` → 改 seed → `fail_closed`），並將 fail-closed 截圖與已
commit 的 VRT baseline `frontend/visual-baselines/interactive-research-failclosed.png`
比對，0 個 mismatched pixels。

> - Evidence Source：`report_artifact`（已 commit 的 `interactiveResearch`
>   static-replay 區塊，位於 `frontend/lib/showcase-payload.json` / `docs/showcase.json`）
>   ＋ `live_command_output`（`npm run e2e:interactive` 真實 Chromium fail-closed VRT）
> - Coverage Tier：`hybrid` · Readiness State：`PASS` —《Implemented · Review
>   PASSED（repo-side/local static-replay）》（`h-interactive-research-ui/review.md`）
> - Source Ref：`.agents/specs/h-interactive-research-ui/review.md`、
>   `.agents/specs/h-interactive-research-ui/requirements.md`
> - Captured：依 `h-interactive-research-ui/review.md`（2026-06-18）— 前端 52 tests
>   pass、coverage 84.12%、`npm run e2e:interactive` 通過（真實 Chromium
>   `computed`→`fail_closed`、0-pixel VRT）、browser visual diff `1077 / 1,296,000`
>   低於 threshold `0.001`，H-3 mutations `frontend-h3-interactive-claim-boundary`
>   / `frontend-h3-approximate-warning-gate` / `frontend-h3-e2e-failclosed-status-gate`
>   皆 killed。Public Pages parity 現為 `proven` — dev squash-merge 進 `main`（`49a4510`）後
>   Pages 服務該 artifact，probe 相符 deployed==expected `dataHash c33da57d…`（觀測於
>   `2026-06-18T07:47Z`）；儀表板 self-claim 依設計維持 `not_proven`。
> - `MOCK_DOMINANT_EVIDENCE` — 對既有 H artifacts 的 `static_replay`（無 live
>   backend rerun、JAX/TF 真實訓練、GPU/native models 或 production Tier3）；
>   `no_alpha_claim`。

---

## 視覺缺口盤點

**Render 驗證（2026-06-15，headless chromium `1440×2600`）：** 本手冊（en/zh）與
executive review 皆正常渲染 — 側邊導覽、hero、terminal code blocks、evidence
caption 與 warning badge（`PASS`、`MOCK_DOMINANT_EVIDENCE`）皆完整，無破版 CSS 或
缺失 asset。review 的 UX-flow 圖現已改為 **self-contained inline SVG**（可離線 /
`file://` 渲染，無 CDN 或 client-side JS，並附 accessible 文字等價 caption），已無
剩餘視覺殘留。

**自上次檢查以來已解決（CR-B21 / CR-RDO-004 / CR-FBP-001 / CR-FPS-009/010/011，as of 2026-06-15）：**

- **互動研究 UI 已落地（Epic H 切片 H-3）— 新增流程 8。** showcase 儀表板現帶有
  一個對既有 H artifacts 的互動參數面板 — deterministic `static_replay` 的
  model-vs-baseline 排行榜，含 equity/drawdown/return-distribution/learning-curve
  圖表、僅 OOS-net 排名且 baseline 可見、`research_mode_approximate_availability`
  警告，以及對不支援參數或陳舊 checksum 的 **fail-closed** 行為。由
  `tests/quantlab/test_h3_interactive_showcase.py`、
  `frontend/tests/interactive-research.test.ts` 與真實 Chromium
  `npm run e2e:interactive` fail-closed VRT（0-pixel）證明。`no_alpha_claim`；無 live
  backend rerun、JAX/TF 真實訓練、GPU/native models 或 production Tier3。

- **深度歷史回填已落地（CR-B21）— 新增流程 6。** 研究 vintage 現已回溯至
  **1990**（Yahoo deep indices + 完整 FRED + NOAA，`is_approximate=true`，
  strict-excluded，24/24 sources，fail=0）。這使一個真實的多週期回測成為可能（deep
  {^GSPC,^IXIC} 1990→2026，437 個月，`computed`），並對照真實紀錄驗證
  （dot-com −49%/−78%、GFC −57%、COVID −34%、2022 −25%）。流程 5 的預設 run
  因此從僅 SP500 擴大為 12 資產的 co-temporal universe。`no_alpha_claim`；
  先前限流的 6 條 FRED rate/FX 系列（含 `T10Y2Y`）已由 idempotent re-run 補齊
  → regime family 現為 full-feature。

- **前後端服務已 live 驗證（2026-06-15）。** Next.js dashboard smoke 對 ephemeral
  `next start` 通過（提供 `/` 與真實 `/api/showcase` payload — 見
  `assets/frontend-smoke-01.txt`），legacy FastAPI 金字塔計算機回傳真實等差金字塔
  結果（見 `assets/legacy-api-01.txt`），因此「啟動服務」證據已是 live_command_output，
  不再僅依賴已 commit 的 payload。

- **Sampling-frequency 誠實缺口已關閉（CR-RDO-004）。** 真實資料 OOS library 現會
  估計每個資產的 native cadence，並在 rebalance cadence 比最粗的選中資產更細時
  **fail closed**（`reason=oversampled_vs_native_frequency`），不再默默把陳舊價格
  forward-fill 成會灌水 Sharpe 的捏造 flat returns。預設 run（現為 12 個 co-temporal
  daily-native 資產）不受影響、維持 `computed`（見流程 5）。
- **Browser pixel baseline 現為真實且容許 re-pin（CR-FBP-001）。** stale-baseline-hash
  guard 只在 `baselineHash != currentHash` 時觸發，因此合法的 deterministic re-pin
  （`baselineHash == currentHash`、`mismatchedPixels == 0`）不再阻擋誠實的 UI 變更；
  tolerant pixel-diff threshold gate 不變。
- **Dashboard visual readiness 已 wire-through（CR-FPS-009）。** Export 的 readiness
  面板現由 repo-side browser visual diff 證據回報 `visualRegression=proven`（先前未接線）。
- **Public hosting 在 H-3 部署後已重新證明。**
  dev lane squash-merge 進 `main`（`49a4510`），GitHub Pages 建置後 live probe 相符
  deployed==expected `dataHash c33da57d11c48945abcee36f2c78eb377f793536f769ddb10b87e8e4b3c7462a…`
  （`status=proven` / `matched`，`docs/deployment-manifest.json`、
  `docs/public-hosting-probe.json`，觀測於 `2026-06-18T07:47Z`；committed proof 經
  `scripts/refresh_public_hosting_proof.py --live` 刷新）。較舊的
  `e5794260…` / `0f170441…` hosting proof 只保留為 historical point-in-time evidence；
  dashboard payload 自身的 `publicHosting` self-claim 依設計仍為 `not_proven`。
- **Hosting-freshness time-bomb 已移除（CR-FPS-011）。** Freshness 現以注入的 `asof`
  做 deterministic 分類（無隱藏 wall-clock）；過期的已 commit 證據會**降級**為
  `configured_not_observed`，而非在 re-prove ~24h 後讓 build/suite crash。

**更早已解決（2026-06-11 → 2026-06-13）：**

- 預設 root 測試套件目前為 **435 passed, 2 skipped**；**430 passed** 僅保留為 H-2 torch-enabled UAT / optional-lane 證據。Mypy 在目前 scoped `quantlab/` source set 上 clean；mutation spot checks 維持 **118/118 configured/killed**，包含 CR-RDO-004 sampling-frequency guard、root Torch dependency、stale governance evidence mutations 與 non-self-staling promotion-boundary guard、local-first CI default and skill-body guards、governance refresh review stale-evidence regression、CR-FPS public-hosting drift guards、stakeholder and app payload copy drift、import-linter count/formalization drift、governance registry row-count drift、E production evidence gates、CR-B12 scoped source-health overclaim 防護、CR-B18 broad source-quorum overclaim 防護、CR-B19 proof replay 防護，以及 CR-B20 Stooq proof exit/file replay 防護。Frontend mutation 目前 **29/29 killed**，包含 `frontend-smoke-html-api-parity-regression`，因此 local smoke 不只驗 API payload，也會檢查 HTML/API payload parity。
- `docs/` 下首次 commit 的 manual/review 文件集。
- **已擷取 live 瀏覽器截圖**（chromium-headless，`browser-visual.png`，狀態 `proven`）— 解決先前「無瀏覽器截圖」缺口。
- **Public-hosting probe 已記錄 HTTP 200 與 deployed manifest contract metadata**（`public-hosting-probe.json`）；每次 dashboard `dataHash` 刷新後 branch-local parity 為 `configured_not_observed`，直到 Pages 服務後於部署時重新證明 — 目前對 H-3 `dataHash c33da57d…` 在 2026-06-18 `main` 部署後為 **`proven`**。
- **Visual diff 已改為 repo-baseline pixel-backed**（`browser-visual-diff.json`：`1077 / 1,296,000` mismatched pixels，threshold `0.001`）— 解決先前 hash-equality 殘留，同時允許 gate 內的少量文字渲染差異。

**未解決的視覺缺口：**

| 缺口 | 嚴重度 | 來源 |
|---|---|---|
| 尚無 CI-managed visual baseline history（目前為 repo baseline） | Low | `f-browser-pixel-baseline/review.md` |
| Stooq source contract 仍與 FRED/Yahoo/NOAA source-quorum proof 分開治理 | Low | `b-data-platform/change-requests/cr-b19-source-quorum-live-proof.md` |
| Dashboard payload `publicHosting` self-claim 依契約維持 `not_proven`（靜態 artifact 無法自我宣稱部署）；外部 committed probe/manifest parity 現為 `proven` / `matched`，對 `dataHash c33da57d…` 在 2026-06-18 `main` 部署後 | by design | `frontend/out/index.html`、`docs/public-hosting-probe.json` |
| 真實資料 OOS 使用 `approximate_event_date`（非 true PIT）；具真實 vintage 歷史的 co-temporal 多資產 default universe 為後續工作 | Low | `real-data-oos-backtest/review.md` |
| Vintage co-temporal 多資產 readiness 仍在累積（single-capture FRED；daily-vintage 回測延後） | Low | `run_vintage_slice.py` 輸出 |
| Stooq source blocked（`ISSUE-B3-001`） | Low | `ISSUE_LOG.md` |

高階缺口分析見 [`docs/review/index.html`](../../review/index.html)。
