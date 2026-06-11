# Tasks — Epic A0:回測引擎 + Tier1 平行底座 + Tier2 追蹤

> SDD Phase 3。Status: **Draft(待使用者授權進 Phase 4 實作)**。
> 需求:[requirements.md](./requirements.md) · 設計:[design.md](./design.md) · 契約:[contract/](./contract/)
> **執行紀律:嚴格 TDD = RED → GREEN → REFACTOR**;搭配 Property-Based(hypothesis)+ Mutation(mutmut/cosmic-ray)+ mypy 框架隔離 gate。
> - **RED** = 先寫會失敗的測試(範例 + PBT 性質),確認紅燈,**無紅燈不得寫產品碼**。
> - **GREEN** = 最小實作讓測試轉綠。
> - **REFACTOR** = 綠燈保護下重構,每步保持綠。
> 每 task 完成定義 = 三段循環走完、相關 PBT 綠燈、`[Implements REQ]` 追溯、commit 帶 `Ref: a0-backtest-foundation`。

## DAG
```
A0-0 contract codegen ──┬─> A0-1 PIT data ──┐
                        ├─> A0-2 engine+costs┤
                        ├─> A0-3 parallel    ┼─> A0-5 整合(golden+PBT) ─> A0-6 QC(mutation gate)
                        └─> A0-4 tracking ───┘
```

---

## A0-0 — Contract codegen + 骨架(Contract)
- **Role:** Coder · **Effort:** M · **depends_on:** [] · **Implements:** REQ-A0-IFC-001/002/003
- **RED:** 先寫 failing 測試:(a) dummy buy-and-hold 策略可被 `Strategy` Protocol 型別接受;(b) `result_record.json` schema 往返(model↔json);(c) import-linter 規則存在且現況會抓到違規(engine/data 不得 import torch/tf/jax)。執行 → 紅燈。
- **GREEN:** 建 `quantlab/` 骨架;由 `contract/schemas/*.json` codegen `quantlab/contracts/` Pydantic models(**禁手寫基礎型別**);re-export `interfaces.py` Protocol;設 mypy + import-linter;加 dummy 策略。執行 → 綠燈。
- **REFACTOR:** 整理 package `__init__` 匯出、codegen 腳本可重跑、設定檔去重。保持綠。
- **AC:** dummy 策略型別相容;codegen 可重跑;mypy + import-linter 綠燈。

## A0-1 — Point-in-Time DataProvider(Impl)
- **Role:** Coder · **Effort:** L · **depends_on:** ["A0-0"] · **Implements:** REQ-A0-PIT-001/002/003/004
- **RED:** 先寫 failing 測試:lookahead golden(注入未來→須被攔)、survivorship golden、macro release-lag;**PBT-2**(任意 asof/注入未來 → 回傳列 `available_date ≤ asof`)。執行 → 紅燈。
- **GREEN:** bitemporal 儲存(`event_date`+`available_date`),`get(asof)` 過濾 `available_date ≤ asof`;`universe(asof)` 由上市/下市日表計算(含已下市);`macro` 取已公布最新值;建 fixture 玩具資料集(行情+1 總經含 revision+1 中途下市標的)。執行 → 綠燈。
- **REFACTOR:** 抽出 as-of 過濾共用函式、fixture 載入 helper。保持綠。
- **AC:** AC-A0-01、AC-A0-02、PBT-2 綠燈。

## A0-2 — 回測引擎(向量化)+ 成本模型(Impl)
- **Role:** Coder · **Effort:** L · **depends_on:** ["A0-0"] · **Implements:** REQ-A0-BT-001..006
- **RED:** 先寫 failing 測試:玩具案例對拍已知解析解(指標數值);**PBT-1**(`cost=0→net==gross` 且任意成本 `net≤gross`)、**PBT-5**(指標健全性)、**PBT-6**(walk-forward 訓練窗結束 < 測試窗開始)。執行 → 紅燈。
- **GREEN:** `VectorizedEngine.run`(rebalance 迴圈 → `generate_signal` 僅 PIT → fill → 部位累計);`costs/`(手續費+滑價+台股證交稅+美股股息預扣+換匯點差);指標(報酬/vol/maxDD/Sharpe/turnover,分 IS/OOS、gross/net);walk-forward 切分;`event_driven` stub NotImplemented。執行 → 綠燈。
- **REFACTOR:** 抽出指標計算模組、成本套用 pipeline。保持綠。
- **AC:** AC-A0-03、玩具對拍、PBT-1/5/6 綠燈。

## A0-3 — Tier1 平行底座 + 環境隔離(Impl)
- **Role:** Coder · **Effort:** M/L · **depends_on:** ["A0-0"] · **Implements:** REQ-A0-PAR-001/002/003
- **RED:** 先寫 failing 測試:**PBT-4**(任意 job 集,平行結果==序列結果,同母 seed);三框架環境冒煙(各自 import 成功不衝突)。執行 → 紅燈。
- **GREEN:** `JoblibExecutor.map`(母 seed 衍生子 seed,N job 平行);`ParallelExecutor` 抽象預留 Ray(不實作);`envs/` pytorch/tensorflow/jax 環境定義。執行 → 綠燈。
- **REFACTOR:** 抽出 seed 衍生策略、job 序列化 helper。保持綠。
- **AC:** AC-A0-06、PBT-4、三框架冒煙綠燈。

## A0-4 — Tier2 追蹤(Impl)
- **Role:** Coder · **Effort:** M · **depends_on:** ["A0-0"] · **Implements:** REQ-A0-TRK-001/002/003
- **⚠️ 後端決策變更(2026-06-10):** 原訂 MLflow 在 **Python 3.13 環境依賴衝突**無法乾淨安裝
  (protobuf 5 移除 `google.protobuf.service`;setuptools 81 移除 `pkg_resources`;
  pin 後 uv 把 mlflow 回退到 2022 年的 1.27.0)。`ResultStore` Protocol 即 swappable
  backend 接縫,故**改用零重依賴 SQLite `LocalResultStore` 為預設**;MLflow backend 延後到
  乾淨環境(mlflow 2.x)再以同 Protocol 接入。能力不變(log/get/leaderboard/OOS-net 強制)。
- **RED:** 先寫 failing 測試:log→get 往返;leaderboard 依 **OOS net** Sharpe 排序且可追溯回 run_id;
  **FMEA-A0-05**(leaderboard 只認 OOS+net,忽略高 IS/full);**PBT-3**(任意 seed → 引擎兩次 run 指標一致)。
- **GREEN:** `LocalResultStore`(stdlib sqlite3)`log`/`leaderboard`/`get`;leaderboard 強制 `out_of_sample`+`net`(FMEA-A0-05)。
- **REFACTOR:** 抽出 OOS-net 擷取 helper。保持綠。
- **AC:** AC-A0-07、PBT-3 綠燈;leaderboard 可追溯。
- **待辦(非阻塞):** MLflow backend(含 `mlflow ui` 視覺化)於乾淨環境接入,走同 `ResultStore` Protocol。

## A0-5 — 整合測試(golden + PBT 端到端)(Integration)
- **Role:** QA_Engineer · **Effort:** M · **depends_on:** ["A0-1","A0-2","A0-3","A0-4"]
- **內容:** dummy 策略 + dummy baseline 走 data→engine→tracking→leaderboard 全鏈;端到端 lookahead 注入被攔、重現性、平行一致。(整合層仍先寫端到端測試再串接 → RED→GREEN。)
- **AC:** AC-A0-01..07 全綠;happy path + lookahead 注入 + 重現性 + 平行一致。

## A0-6 — 方法論 QC + Mutation gate(QC Review)
- **Role:** QC_Reviewer · **Effort:** M · **depends_on:** ["A0-5"]
- **內容:**
  1. 跑 mutation testing 於 `quantlab/{data,engine,costs}`;裁定最低 kill score 門檻(起步 ≥80%);存活 mutant 補測試或書面豁免。
  2. 對抗式審查:lookahead/survivorship、成本真實度、walk-forward、框架隔離、可重現。
  3. 產「回測正確性 checklist」(作品集 artifact);更新 folder-level `quantlab/TESTS.md`。
  4. `review.md` 裁定 acceptance/readiness verdict。
- **AC:** mutation kill score 達標;NFR 全部有證據;`review.md` 給 verdict。

---

## 測試治理待辦(closeout 前)
- 更新 folder-level `quantlab/TESTS.md`(test IDs、canonical commands、evidence refs、REQ/AC trace)。
- 若採用 workspace `.agents/specs/TESTS.md` rollup,交 `test-registry-manager` 刷新。
- `review.md` 為最終 verdict authority。
