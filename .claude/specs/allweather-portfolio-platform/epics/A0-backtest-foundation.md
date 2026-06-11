# Epic A0 — 回測引擎 + Tier1 平行底座 + Tier2 追蹤(皇冠鑽石)

> P0 地基 / 關鍵路徑起點。獨立 foundation lane。來源:[../01-problem-space.md](../01-problem-space.md)
> **此 epic 的嚴謹度本身就是作品集賣點**(point-in-time 正確 = 99% 業餘 quant 作品集做不到的事)。

## Epic 級驗收(Definition of Done)
- 任意遵守薄介面的策略/模型(PyTorch/TF/JAX/sklearn 皆可)可被回測,**框架無感**。
- 回測**無 lookahead、無 survivorship**;含成交/成本/稅/匯模型;walk-forward/OOS 切分。
- 大規模 sweep 可平行(Tier1);每 run 的 config+OOS 指標自動入庫並可 leaderboard 比較(Tier2)。
- 同 seed+config+資料版本 → 可重現完全相同指標。

## DAG
```
A0-0 contract
 ├─> A0-1 DataProvider ─┐
 ├─> A0-2 Engine ───────┤
 ├─> A0-3 Tier1 平行 ───┼─> A0-5 整合(含 lookahead golden test) ─> A0-6 方法論 QC
 └─> A0-4 Tier2 追蹤 ───┘
```

---

## Tasks

### A0-0 — Define core interfaces(Contract)
- **Role:** Coder · **Effort:** M · **depends_on:** []
- **Description:** 定義全專案共用的薄介面與資料契約:`Strategy/Model`(`fit`/`predict`/`generate_signal`,框架無感,只吐標準化 signal/weight 序列 + metadata)、`PointInTimeDataProvider`(as-of 語意)、`BacktestEngine` API、`ResultRecord` schema(config + data_version + seed + OOS 指標)、`Leaderboard` 查詢介面。
- **AC:**
  - 介面以型別註記 + docstring 定義完成;附 1 個 dummy 策略 reference 實作。
  - `ResultRecord` 明確包含 data_version / seed / cost_assumptions,確保可重現。
  - signal 輸出格式與框架完全解耦(以 pure array/series + 時間索引表達)。
- **Test:** 介面 contract test(dummy 策略可被 engine 呼叫);schema 驗證測試。

### A0-1 — Point-in-Time DataProvider(Impl,並行)
- **Role:** Coder · **Effort:** L · **depends_on:** ["A0-0"]
- **Description:** as-of 取數(只回傳「該時點可得」的資料);survivorship-safe 宇宙成員資格(含已下市標的);總經資料的 **release-date / revision lag**(GDP/CPI 用「公布日」非「所屬期」對齊)。
- **AC:**
  - `get(asof, fields)` 絕不回傳 asof 之後才可得的資料(含修訂值)。
  - 宇宙查詢回傳「該時點實際存在」的標的,不排除已下市者。
  - 總經序列以公布日索引;單元測試證明所屬期 ≠ 可得日。
- **Test:** lookahead 注入測試(餵未來資料,斷言被拒);survivorship 對照測試。

### A0-2 — Backtest engine core(Impl,並行)
- **Role:** Coder · **Effort:** L · **depends_on:** ["A0-0"]
- **Description:** 回測主迴圈(向量化或事件式);fill 模型(可設滑價);**交易成本 + 台股交易稅 + 美股股息預扣 + USD/TWD 匯兌**;walk-forward / OOS 切分;績效指標(累積/年化報酬、年化 vol、maxDD、Sharpe、turnover)。
- **AC:**
  - 報酬計算為**稅後/匯後/成本後**;可切換 gross/net 並標示。
  - walk-forward 切分無訓練/測試洩漏;OOS 區段明確。
  - 指標對拍一個已知解析解的玩具案例(數值正確性)。
- **Test:** 玩具案例對拍;成本歸零時 net==gross;turnover 正確性。

### A0-3 — Tier1 平行運算底座(Impl,並行)
- **Role:** Coder · **Effort:** M/L · **depends_on:** ["A0-0"]
- **Description:** 平行抽象(joblib/Ray;先 joblib MVP,介面預留 Ray);批次 sweep 提交;**每框架環境隔離**(分 venv 或容器映像,排程挑對應映像,解 PyTorch/TF/JAX 的 CUDA 衝突)。
- **AC:**
  - 同一 sweep API 可在本機多核跑 N 個回測,結果與序列執行一致(determinism 給定 seed)。
  - 提供 PyTorch/TF/JAX 三個隔離環境定義,各自可獨立載入不衝突。
- **Test:** 並行 vs 序列結果一致性;三框架環境冒煙測試(各自 import 成功)。

### A0-4 — Tier2 輕量實驗追蹤(Impl,並行)
- **Role:** Coder · **Effort:** M · **depends_on:** ["A0-0"]
- **Description:** 每 run 落 config+data_version+seed+OOS 指標到可查詢結果表(MLflow tracking 或輕量 SQLite/parquet);leaderboard 對笨 baseline 排序;可重現查詢。
- **AC:**
  - 跑完任一回測自動產生一筆 `ResultRecord`;可用 leaderboard 並排比較 vs baseline。
  - 由 record 可完整重建該實驗(取回 config/seed/data_version)。
- **Test:** 寫入→查詢往返;重現性測試(同 record 重跑指標一致)。

### A0-5 — 整合測試(Integration,含 lookahead golden test)
- **Role:** QA_Engineer · **Effort:** M · **depends_on:** ["A0-1","A0-2","A0-3","A0-4"]
- **Description:** dummy 策略 + dummy baseline 走 DataProvider→Engine→Tier2→Leaderboard 全鏈;**金標 lookahead 測試**(注入未來資訊,斷言績效不應改善/應被攔);重現性端到端。
- **AC:** 全鏈跑通並產出 leaderboard;lookahead 注入被偵測/攔截;同 seed 兩次跑出相同指標。
- **Test:** happy path + lookahead 注入 + 重現性 + 並行一致。

### A0-6 — 方法論 QC(QC Review)
- **Role:** QC_Reviewer · **Effort:** M · **depends_on:** ["A0-5"]
- **Description:** 對抗式審查 lookahead/survivorship 漏洞、成本模型真實度、walk-forward 正確性、介面框架無感性、可重現性。
- **AC:** 無已知 lookahead/survivorship 洩漏路徑;成本假設文件化;介面確認可承接 PyTorch/TF/JAX;coverage 達標。
- **Test:** 全測試綠燈;附一份「回測正確性 checklist」作為作品集 artifact。
