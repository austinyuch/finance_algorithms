# Design — Epic A0:回測引擎 + Tier1 平行底座 + Tier2 追蹤

> SDD Phase 2。Status: **Draft(待使用者授權進 Phase 3 Tasks)**。
> Contract SSOT:[contract/interfaces.py](./contract/interfaces.py)、[contract/schemas/](./contract/schemas/)
> 需求:[requirements.md](./requirements.md)

## 1. 架構總覽

新建獨立 package `quantlab/`(= 研究 lab),與既有 `invest_algorithms/`(FastAPI + algo_pyramid)**並存不互改**。algo_pyramid 未來(Epic C)會被包成「進場 adapter」,A0 不碰它。

```
quantlab/
  contracts/      # 由 contract/schemas/*.json 生成的 Pydantic models + 介面 re-export
  data/           # PointInTimeDataProvider 實作 + fixture 玩具資料集
  engine/         # BacktestEngine:vectorized 實作(+ event_driven 預留 stub)
  costs/          # 成本/稅/匯模型(CostConfig 驅動)
  parallel/       # ParallelExecutor:joblib 實作(+ Ray 預留介面)
  tracking/       # ResultStore:MLflow(local backend)實作 + leaderboard
  envs/           # 三框架環境隔離定義(pytorch / tensorflow / jax)
tests/            # 沿用既有 tests/,新增 quantlab 測試(含 golden tests)
```

**鐵律(NFR-A0-FWAGN-001):** `quantlab/engine/`、`quantlab/data/` 的 import 圖不得出現 torch/tensorflow/jax。框架只存在於「策略實作」與 `quantlab/envs/`,經 `Strategy` Protocol 解耦。

## 2. 元件設計(對齊鎖定決策)

### 2.1 PointInTimeDataProvider(data/)— 防 lookahead 的核心
- 底層儲存採「**append-only + bitemporal**」概念:每筆資料帶 `event_date`(所屬期)與 `available_date`(可得/公布日)。`get(asof)` 一律 `WHERE available_date <= asof`。
- `universe(asof)`:由「上市/下市日」表計算成員,**含已下市標的**(survivorship-safe)。
- `macro(asof, series)`:回 `available_date <= asof` 的最新值,天然處理 release lag 與 revision(只取當時版本)。
- fixture 玩具資料:行情 + 1 條總經(含 revision)+ 1 檔中途下市標的,專供 golden tests。

### 2.2 BacktestEngine(engine/)— 向量化先行
- `VectorizedEngine` 實作 `BacktestEngine`;`config.engine` 預留 `event_driven` 之後實作。
- 流程:對每個 rebalance 時點 `t` → `strategy.generate_signal(t, data)`(只透過 PIT data)→ 依 `fill` 模型於 `t+1` 成交 → 累計部位 → 套 `costs` → 產 net/gross 報酬序列 → 計指標。
- walk-forward:依 `config.walk_forward` 切訓練/測試窗,`strategy.fit()` 只見訓練窗;指標分 `in_sample`/`out_of_sample` 各算一份。

### 2.3 Costs(costs/)
- 由 `CostConfig` 驅動;成交時套手續費+滑價+台股證交稅(賣方)、配息時套美股預扣、跨幣計價時套換匯點差。
- 不變量:**所有成本參數=0 → net == gross**(AC-A0-03,設為單元測試)。

### 2.4 Parallel(parallel/)— joblib-first
- `JoblibExecutor` 實作 `ParallelExecutor.map`;每個 job 接收明確 seed(由母 seed 衍生),確保平行/序列結果一致(AC-A0-06)。
- `envs/`:三框架各一份環境定義(venv requirements 或容器映像);executor 提交 job 時指定目標環境,避免 CUDA 衝突。Ray 介面預留,不在 A0 實作。

### 2.5 Tracking(tracking/)
- **後端決策(2026-06-10 更新):** 原訂 MLflow,但其在 **Python 3.13 依賴衝突**(protobuf 5 移除 `google.protobuf.service`;setuptools 81 移除 `pkg_resources`;pin 後回退到 mlflow 1.27.0)無法乾淨安裝。`ResultStore` Protocol 即 backend 接縫,故**預設改用零重依賴 SQLite `LocalResultStore`**;MLflow backend 延後到乾淨環境再接入。
- `LocalResultStore`(stdlib `sqlite3`)實作 `ResultStore`:
  - `log()`:把 `ResultRecord` 存成一列(run_id / strategy_name / 擷取的 OOS-net Sharpe / is_baseline / 完整 record JSON);run_id 缺則生成。
  - `leaderboard()`:依 **OOS net** Sharpe 排序(FMEA-A0-05:只認 out_of_sample+net,杜絕用高 IS/full 灌水);NULL(無 OOS-net)排末。
  - `get(run_id)`:回完整 record JSON,供重現。
- **延後(同 Protocol 可插拔):** `MlflowResultStore` + `mlflow ui` 視覺化,待乾淨環境(mlflow 2.x)。

## 3. 資料流

```
Strategy(任一框架) ──generate_signal(asof)──▶ PIT DataProvider ─(僅 available_date<=asof)
        │                                              │
        └──────────────▶ VectorizedEngine ◀────────────┘
                              │  套 fill + costs + walk-forward
                              ▼
                     PerformanceMetrics(gross/net, IS/OOS)
                              │
                              ▼
                 MlflowResultStore.log ──▶ leaderboard(vs baseline)
   (JoblibExecutor 將上述整條包成 job,平行跑 N 個設定)
```

## 4. Lightweight FMEA(強制 — false-green / 方法論風險)

| Risk ID | Failure Mode | Effect | Cause | Current Control | Sev | Occ | Det | Planned Response | Task Trace |
|---|---|---|---|---|---|---|---|---|---|
| FMEA-A0-01 | DataProvider 漏擋未來資料 | 回測虛高,所有模型學到假 edge(整個 lab 失效) | as-of 過濾遺漏修訂/某欄位 | bitemporal 過濾 | 高 | 中 | 中 | **Detect**:lookahead golden test(注入未來→須被攔)AC-A0-01 | A0-1, A0-5 |
| FMEA-A0-02 | survivorship 洩漏 | 報酬灌水(個股階段最嚴重) | universe 用現存清單 | 上市/下市日表 | 高 | 中 | 中 | **Prevent**:universe 由日期表計算 + AC-A0-02 測試 | A0-1, A0-5 |
| FMEA-A0-03 | 成本/稅/匯漏算 | 高估報酬,戰術策略假裝有 edge | net 模式遺漏某成本 | CostConfig 全欄位 required | 中 | 中 | 低 | **Detect**:cost=0→net==gross 不變量 AC-A0-03 | A0-2 |
| FMEA-A0-04 | 平行非 determinism | 結果不可重現,leaderboard 失真 | 各 job 共用全域 RNG | 母 seed 衍生子 seed | 中 | 中 | 中 | **Prevent**:平行 vs 序列一致性測試 AC-A0-06 | A0-3, A0-5 |
| FMEA-A0-05 | 只報 in-sample/gross | overclaim,作品集失去誠實度賣點 | 報告省略 basis/segment | metrics 必填 basis+segment | 中 | 中 | 低 | **Contain**:schema required + leaderboard 強制用 OOS net | A0-2, A0-4 |
| FMEA-A0-06 | walk-forward 洩漏 | OOS 其實看過未來,失去意義 | fit 誤用測試窗 | 訓練/測試窗切分 | 高 | 中 | 中 | **Detect**:洩漏偵測測試 + QC 審查 | A0-2, A0-5, A0-6 |

> 每個高風險 failure mode 皆對應到 AC/測試與具體 task(Prevent/Detect/Contain)。residual risk 由 A0-6 方法論 QC 確認。

## 4.5 測試策略(2026-06-09 鎖定:TDD + Property-Based + Mutation)

- **TDD 強制 = RED → GREEN → REFACTOR(嚴格三段循環):**
  - **RED:** 先寫**會失敗**的測試(範例測試 + 相關 PBT 性質),執行確認紅燈。不得在無紅燈測試下寫產品碼。
  - **GREEN:** 寫**剛好**讓測試通過的最小實作,執行確認綠燈。
  - **REFACTOR:** 在綠燈保護下重構(去重、命名、抽象),每步保持綠燈。
  - 每個實作 task 的子任務一律以此三段呈現;測試永遠在實作之前。
- **工具鏈:** `pytest`(沿用既有)+ `hypothesis`(PBT)+ `mutmut` 或 `cosmic-ray`(mutation)+ `mypy`(框架隔離 gate)。
- **Property-based 不變量(對任意生成輸入須成立):**
  - PBT-1:`cost=0 → net==gross`;且任意成本參數下 `net ≤ gross`(對應 AC-A0-03)。
  - PBT-2:任意 asof 與任意注入的未來資料,`DataProvider.get(asof)` 回傳列的 `available_date ≤ asof`(對應 AC-A0-01)。
  - PBT-3:任意 `config+seed`,兩次回測指標完全相同(對應 AC-A0-04)。
  - PBT-4:任意 job 集,平行結果 == 序列結果(對應 AC-A0-06)。
  - PBT-5:任意回測,`annualized_vol≥0`、`max_drawdown≤0`、`turnover≥0`(指標健全性)。
  - PBT-6:任意 walk-forward 切分,訓練窗結束 < 測試窗開始(無重疊洩漏,對應 FMEA-A0-06)。
- **Mutation gate:** 對 `quantlab/{data,engine,costs}` 核心模組跑 mutation testing,設**最低 kill score 門檻**(建議起步 ≥80%,於 A0-6 QC 裁定);存活的 mutant 須補測試或書面豁免。
- **Golden tests:** lookahead 注入(AC-A0-01)、survivorship(AC-A0-02)為具體 golden case,與 PBT 並存。

## 5. Contract → Code Generation
- `contract/schemas/*.json` → 生成 `quantlab/contracts/` 下 Pydantic models(datamodel-code-generator 或等效),**禁止手寫基礎型別**。
- `contract/interfaces.py` 的 Protocol 直接被實作 import 為型別約束;CI 須跑 `mypy` 確認實作符合 Protocol + import 圖無框架洩漏(NFR-A0-FWAGN-001)。

## 6. REQ → Design 對照
| REQ | Design |
|---|---|
| IFC-001/002/003 | §2(Strategy Protocol)、contract/interfaces.py |
| PIT-001..004 | §2.1 bitemporal data |
| BT-001..006 | §2.2 VectorizedEngine + §2.3 costs |
| PAR-001..003 | §2.4 joblib + envs |
| TRK-001..003 | §2.5 MLflow |
| NFR-CORRECT/REPRO/FWAGN/HONEST | §1 鐵律、§4 FMEA、§5 mypy gate |

## 6.5 視覺化 / API 邊界(2026-06-09 明確決策:刻意延後)

- **A0 = 純 Python library,不含任何 FastAPI 新端點、不含前端。**
- **視覺化由 MLflow 自帶 UI 提供**(`mlflow ui`):params/metrics、leaderboard 排序、跨 run 圖表比較皆免費,A0 無需寫前端即可「看圖看排行」。
- **FastAPI 擴充 + Next.js 客製 chart → Epic F**,延後到 Epic A 產出真實結果後再做(depth-first + R3,避免引擎穩定前先蓋展示層而返工)。
- **接縫(seam):** `ResultStore.leaderboard()` / `get()`(contract/interfaces.py)即為 Epic F 未來消費的唯一介面。Epic F 只需在此契約上加 read API + 前端,**不需回頭改 A0**。
- 既有 `invest_algorithms/api.py`(金字塔 FastAPI)維持不動。

## 7. 待 Phase 3 展開
依 [../allweather-portfolio-platform/epics/A0-backtest-foundation.md](../allweather-portfolio-platform/epics/A0-backtest-foundation.md) 的 7 個 task(A0-0..A0-6),於 `tasks.md` 細化為可執行子任務 + `[Implements REQ-...]` 追溯標註。
