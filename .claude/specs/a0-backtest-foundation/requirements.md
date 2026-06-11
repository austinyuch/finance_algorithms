# Requirements — Epic A0:回測引擎 + Tier1 平行底座 + Tier2 追蹤

> SDD Phase 1。Spec: `a0-backtest-foundation`。Status: **Draft(待使用者授權進 Phase 2)**。
> 上游:[../allweather-portfolio-platform/01-problem-space.md](../allweather-portfolio-platform/01-problem-space.md)、[../allweather-portfolio-platform/epics/A0-backtest-foundation.md](../allweather-portfolio-platform/epics/A0-backtest-foundation.md)

## 0. Governance(Early Declarative)

- **Work classification:** `new spec`(greenfield 地基)。
- **Depends On:** 無(關鍵路徑起點)。
- **Impacts:** 無既有基線被修改。`invest_algorithms/`(FastAPI + algo_pyramid)視為 immutable,A0 僅在其上新建。未來 Epic A/B/C/D/E/F/G 將依賴本 spec 的 `contract/` 介面。
- **First-slice boundary:** 本 spec 只交付「可被任意框架策略呼叫、point-in-time 正確、可平行、可追蹤、可重現」的回測地基。**不含**任何真實策略/模型、真實資料源接入(僅需 1 個玩具/fixture 資料集驗證正確性)、前端、Tier3 MLOps。
- **成功定義:** 此 epic 的**回測方法論正確性本身就是作品集賣點**;正確性 > 功能廣度。

## 1. Glossary(關鍵術語,避免歧義)

| 術語 | 定義 |
|---|---|
| Point-in-time (as-of) | 任一決策時點 `t` 只能取用「在 `t` 當下實際可得」的資料(含資料的公布日,而非所屬期) |
| Lookahead bias | 決策誤用了 `t` 之後才可得的資訊 |
| Survivorship bias | 用「現存標的清單」回測過去,誤排除已下市/倒閉標的 |
| Walk-forward / OOS | 訓練窗 → 樣本外(out-of-sample)測試窗,沿時間滾動,無未來洩漏 |
| Strategy/Model 薄介面 | 框架無感契約;只吐標準化 signal/weight 序列 + metadata |
| ResultRecord | 一次回測的可重現紀錄(config + data_version + seed + cost 假設 + OOS 指標) |

## 2. Functional Requirements

### 2.1 框架無感策略介面(IFC)
- **REQ-A0-IFC-001** 系統須定義一個框架無感的 `Strategy/Model` 介面,至少含 `fit`、`predict`/`generate_signal`,其輸出為純資料(帶時間索引的 signal/weight 序列 + metadata),不洩漏任何框架型別。
- **REQ-A0-IFC-002** 介面須能承接 PyTorch / TensorFlow / JAX / sklearn / statsmodels 任一實作,回測引擎不得 import 任何特定 ML 框架。
- **REQ-A0-IFC-003** 須附 1 個 dummy 參考策略實作,證明介面可被引擎呼叫並完成回測。

### 2.2 Point-in-Time DataProvider(PIT)
- **REQ-A0-PIT-001** `DataProvider.get(asof, fields)` 絕不得回傳 `asof` 之後才可得的資料(含後續修訂值)。
- **REQ-A0-PIT-002** 宇宙(universe)查詢須 survivorship-safe:回傳「該時點實際存在」的標的,含已下市者。
- **REQ-A0-PIT-003** 總經序列須以**公布日(release date)**索引,並能表達 revision/lag(所屬期 ≠ 可得日)。
- **REQ-A0-PIT-004** 須提供 fixture 玩具資料集(行情 + 一個總經序列 + 一個已下市標的)供正確性測試。

### 2.3 回測引擎(BT)
- **REQ-A0-BT-001** 引擎須接受任一 `Strategy` + `DataProvider`,沿時間執行並產出部位與績效。
- **REQ-A0-BT-002** 須支援可設定的 fill 模型(至少:次日開盤/收盤成交、可設滑價)。
- **REQ-A0-BT-003** 報酬須為**成本後**:含交易成本、台股交易稅、美股股息預扣、USD/TWD 匯兌;可切換 gross/net 並明確標示。
- **REQ-A0-BT-004** 須支援 walk-forward / OOS 切分,且訓練窗與測試窗無資料洩漏。
- **REQ-A0-BT-005** 須輸出標準績效指標:累積/年化報酬、年化波動、最大回撤(maxDD)、Sharpe、turnover。
- **REQ-A0-BT-006** 指標計算須對拍至少一個有已知解析解的玩具案例(數值正確性)。

### 2.4 Tier1 平行運算底座(PAR)
- **REQ-A0-PAR-001** 須提供平行 sweep API,可同時執行 N 個回測;結果在給定 seed 下與序列執行一致(determinism)。
- **REQ-A0-PAR-002** 平行後端須抽象化(MVP 用 joblib,介面預留可替換為 Ray),不綁死實作。
- **REQ-A0-PAR-003** 須提供 PyTorch / TF / JAX 各自獨立的環境隔離定義(分 venv 或容器映像),解決三框架 CUDA/cuDNN 衝突;排程須能對應正確環境。

### 2.5 Tier2 輕量實驗追蹤(TRK)
- **REQ-A0-TRK-001** 每次回測須自動產生一筆 `ResultRecord`,含 config、data_version、seed、cost 假設、OOS 指標。
- **REQ-A0-TRK-002** 須提供 leaderboard,可將任意 run 與指定 baseline 並排比較排序。
- **REQ-A0-TRK-003** 由 `ResultRecord` 須能完整重建該實驗設定(可重現查詢)。

## 3. Non-Functional Requirements

- **NFR-A0-CORRECT-001(正確性,最高優先)** 系統須在設計上防止 lookahead 與 survivorship;須有自動化測試證明(見 AC §4.1)。
- **NFR-A0-REPRO-001(可重現)** 同 `seed + config + data_version` 兩次執行須產出**完全相同**的指標。
- **NFR-A0-FWAGN-001(框架無感)** 回測核心模組的 import 圖中不得出現 torch/tensorflow/jax。
- **NFR-A0-PERF-001(效能,刻意放寬)** 因再平衡為月~半年,**不要求低延遲**;效能目標在於 sweep 吞吐(平行擴展),非單次回測延遲。
- **NFR-A0-QUAL-001(作品集級品質)** 程式碼須可讀、有型別註記、有文件;附「回測正確性 checklist」作為 showcase artifact。
- **NFR-A0-HONEST-001(誠實)** 任一績效輸出須標示 gross/net、成本假設、OOS 區段;禁止只報 in-sample 或 gross 數字而不標示。

## 4. Acceptance Criteria(canonical BDD)

#### AC-A0-01 Lookahead golden test(對應 REQ-A0-PIT-001、NFR-A0-CORRECT-001)
1. Given 一個會「偷看」未來價格的作弊策略,與一個 point-in-time 正確的 DataProvider
2. When 透過 DataProvider 嘗試於時點 `t` 取用 `t` 之後才可得的資料
3. Then DataProvider 須拒絕/攔截該存取(拋錯或回傳不可得),作弊策略無法取得未來資訊
4. And 測試須斷言:注入未來資訊**不會**改善回測績效(因為被攔)

#### AC-A0-02 Survivorship 安全(對應 REQ-A0-PIT-002)
1. Given fixture 宇宙含一個在區間中途下市的標的
2. When 查詢下市前某時點的宇宙成員
3. Then 該標的須被包含;查詢下市後時點則不含
4. And 回測不得因「現存清單」而隱性排除已下市標的

#### AC-A0-03 成本後報酬(對應 REQ-A0-BT-003、NFR-A0-HONEST-001)
1. Given 一組會產生交易的部位序列
2. When 以 net 模式回測(含稅/匯/交易成本)
3. Then 報酬須低於同情境 gross 模式,且差額等於成本模型加總
4. And 當所有成本參數設為 0 時,net 結果須等於 gross 結果

#### AC-A0-04 可重現性(對應 REQ-A0-TRK-003、NFR-A0-REPRO-001)
1. Given 固定的 `seed + config + data_version`
2. When 連續執行同一回測兩次
3. Then 兩次產出的所有績效指標須完全相同(bit-for-bit 或在明訂數值容差內)
4. And 由產生的 `ResultRecord` 可重建出相同設定再次重現

#### AC-A0-05 框架無感即插即用(對應 REQ-A0-IFC-002、NFR-A0-FWAGN-001)
1. Given 同一個簡單訊號分別以 PyTorch 與 sklearn(或 stub 代表第三框架)實作並遵守薄介面
2. When 兩者各自丟入同一回測引擎
3. Then 引擎皆能完成回測且不需修改引擎程式碼
4. And 回測核心模組 import 圖中不得出現任何 ML 框架型別

#### AC-A0-06 平行 determinism(對應 REQ-A0-PAR-001)
1. Given 一組 N 個回測設定與固定 seed
2. When 分別以序列與平行(joblib)執行同一組
3. Then 兩種執行方式產出的每筆結果須一致
4. And 平行執行的總時間應隨可用核心數下降(吞吐提升)

#### AC-A0-07 Leaderboard 並排比較(對應 REQ-A0-TRK-002)
1. Given 數筆已完成回測(含至少一個笨 baseline)
2. When 查詢 leaderboard
3. Then 須以指定指標(如 net Sharpe)排序並列出各 run 與 baseline
4. And 每列須可追溯回其 `ResultRecord`(config/seed/data_version)

## 5. Traceability(REQ → A0 Task)

| REQ | A0 Task |
|---|---|
| REQ-A0-IFC-001/002/003 | A0-0(contract) |
| REQ-A0-PIT-001..004 | A0-1 |
| REQ-A0-BT-001..006 | A0-2 |
| REQ-A0-PAR-001..003 | A0-3 |
| REQ-A0-TRK-001..003 | A0-4 |
| AC-A0-01..07(整合驗證) | A0-5 |
| NFR-A0-*(方法論審查) | A0-6 |

## 6. Out of Scope(本 spec 不做)
真實策略/模型(→ Epic A 起)、真實資料源接入(→ Epic B)、組合最佳化(→ C)、ML(→ D)、Tier3 MLOps(→ E)、前端(→ F)、alt-data(→ G)。

## 7. 技術選擇(2026-06-09 使用者已鎖定)
1. **追蹤後端 = MLflow tracking**(用 local file/SQLite backend 保持輕量;MLflow 同時是作品集可展示技能)。
2. **平行框架 = joblib-first,介面抽象預留 Ray**。
3. **回測引擎 = 向量化先行,介面預留事件式**(未來高頻 epic 再加)。
