# Requirements — Epic A:反台積電對衝 thin slice(作品集中心)

> SDD Phase 1。Spec: `a-tsmc-hedge-slice`。分支 `spec/a-tsmc-hedge-slice`。
> 上游:[../allweather-portfolio-platform/epics/A-tsmc-hedge-slice.md](../allweather-portfolio-platform/epics/A-tsmc-hedge-slice.md)、A0 地基(已 merged)。

## 0. Governance
- **Work classification:** `new spec`。
- **Depends On:** `a0-backtest-foundation`(回測引擎 / PIT DataProvider / 平行 / 追蹤)。
- **Impacts:** `a0-backtest-foundation` — 於 `InMemoryPITDataProvider` **新增 `history()` PIT 歷史存取器**(additive,不改既有行為)。
- **First-slice boundary:** 端到端證明「篩選 → 訊號 → 對衝 → 回測 → leaderboard → 一頁 writeup」管線。**資料用合成先行**(strategy C:數字明知假、僅驗證管線),真實資料源接入屬 Epic B。
- **成功定義:** 作品集級「完成的深度」——一條打磨到底、誠實結論的 vertical slice;非 alpha。

## 1. 鎖定決策
- **反指標定義 = 共整合 + 反向 spread**(2026-06-10 使用者選):候選須與 TSMC **共整合**(Engle-Granger,殘差 ADF p < 門檻)**且 hedge ratio(OLS 斜率)< 0**(反向)。
- **資料:** 合成先行(planted 共整合-反向候選必須被找到;隨機候選不得)。
- **起手模型:** LSTM(PyTorch),打笨 baseline(A0 DoD)。

## 2. Functional Requirements
- **REQ-A-SCREEN-001**(A-1)系統須對候選宇宙做共整合篩選:對每個候選與 TSMC 跑 Engle-Granger(OLS hedge ratio + 殘差 ADF),回傳「共整合 且 hedge ratio<0」的候選,依 ADF p 升冪排名。**全程 point-in-time**(只用 `available_date <= asof` 的歷史)。
- **REQ-A-SCREEN-002**(A-1)篩選須可經 Tier1 `JoblibExecutor` 平行跑整個候選宇宙。
- **REQ-A-DATA-001**(A-1)`InMemoryPITDataProvider` 須新增 `history(asof, field, symbols)`,回 PIT 正確的時間序列(每 (symbol,event_date) 取 `available_date<=asof` 最新版)。
- **REQ-A-LSTM-001**(A-2)PyTorch LSTM 訊號模型,遵守 A0 `Strategy` Protocol,walk-forward 訓練。
- **REQ-A-BASE-001**(A-3)笨 baseline 群(buy&hold TSMC / 0050 / 靜態 / 隨機)。
- **REQ-A-HEDGE-001**(A-4)依訊號建對衝部位,vol 預算內 sizing。
- **REQ-A-INT-001**(A-5)全鏈走 A0 回測 → leaderboard vs baseline。
- **REQ-A-DOC-001**(A-6)一頁誠實 writeup(方法/結果/勝負/限制/負面結果)。

## 3. Acceptance Criteria(本回合聚焦 A-1)

#### AC-A-01 共整合-反向篩選找出 planted 候選(REQ-A-SCREEN-001)
1. Given 合成資料:TSMC 價格序列、一個 planted 候選(= −β·TSMC + 均值回歸殘差,β>0 → 反向)、一個隨機漫步候選
2. When 在某 asof 跑共整合篩選
3. Then planted 候選須入選(共整合 且 hedge ratio<0),隨機候選不入選
4. And 結果依 ADF p 升冪排名

#### AC-A-02 篩選為 point-in-time(REQ-A-DATA-001)
1. Given 候選的某段價格 available_date 在 asof 之後
2. When 在該 asof 跑篩選
3. Then 篩選只用 available_date<=asof 的歷史,未來資料不影響結果

#### AC-A-03 篩選可平行且與序列一致(REQ-A-SCREEN-002)
1. Given 多個候選
2. When 經 JoblibExecutor 平行篩選 vs 序列篩選
3. Then 兩者結果一致

## 4. Out of Scope(本 spec 之後或之外)
真實資料源(Epic B)、組合最佳化(Epic C)、完整 ML 模型族(Epic D)、前端(Epic F)。
