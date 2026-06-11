# Epic A — Thin Slice:反台積電對衝 → LSTM → 回測 vs Baseline

> P0 作品集中心。**第一個要「打磨到底」的 showcase 完成品。** 依賴 Epic A0 完成。
> 來源:[../01-problem-space.md](../01-problem-space.md)

## Epic 級驗收(DoD)
- 端到端跑通:反台積電候選篩選(平行)→ LSTM 訊號(PyTorch)→ A0 point-in-time 回測 → leaderboard vs 笨 baseline 群。
- 產出**一頁誠實 writeup**:含方法、OOS 結果、對 baseline 的勝負、成本後報酬、**負面結果與限制誠實揭露**。
- 全程可重現(seed/資料版本/config)。

## ⚠️ 待關閉的 requirements 決策(進 SDD 第一件事)
**「反指標 / 反台積電」的精確定義** —— 四選一(或組合),影響整個 A-1 篩選邏輯:
- (a) 負相關(rolling correlation < 0)
- (b) 負 beta(對 TSMC 報酬迴歸係數 < 0)
- (c) 共整合 + 反向(cointegrated, 反向 spread)
- (d) 反向 lead-lag(TSMC 領先、對方反向落後)

## DAG
```
A-0 contract(含反指標定義)
 ├─> A-1 反台積電篩選 sweep(用 A0 Tier1)─┐
 ├─> A-2 LSTM 訊號(PyTorch)─────────────┤
 ├─> A-3 笨 baseline 群 ──────────────────┼─> A-5 整合 leaderboard ─> A-6 QC + writeup
 └─> A-4 對衝組合邏輯 ────────────────────┘
```

---

## Tasks

### A-0 — 實驗協定 + 反指標定義(Contract)
- **Role:** Coder · **Effort:** S/M · **depends_on:** ["A0-0"]
- **Description:** 鎖定「反指標」定義(見上四選一);定義本 slice 的策略介面實例(對齊 A0 `Strategy`)、輸入特徵集、笨 baseline 清單、評比指標。
- **AC:** 反指標定義書面確認;LSTM 模型 + baseline 皆宣告為 A0 介面相容;評比指標固定(報酬/vol/maxDD/Sharpe,net of cost)。
- **Test:** 介面相容性 contract test。

### A-1 — 反台積電候選篩選 sweep(Impl,並行)
- **Role:** Coder · **Effort:** M · **depends_on:** ["A0-1","A0-3","A-0"]
- **Description:** 用 A0 Tier1 對股票宇宙平行計算 vs TSMC 的 rolling 相關/beta/共整合(依 A-0 定義),排名出反指標候選。**全程 point-in-time**。
- **AC:** sweep 在 Tier1 平行跑通;輸出排名候選 + 統計量;篩選使用 as-of 資料無 lookahead。
- **Test:** 小宇宙正確性對拍;lookahead 檢查。

### A-2 — LSTM 訊號模型(PyTorch)(Impl,並行)
- **Role:** Coder · **Effort:** M/L · **depends_on:** ["A-0"]
- **Description:** PyTorch LSTM,遵守 A0 `generate_signal`;**walk-forward 訓練**(無 OOS 洩漏);輸出對衝訊號。
- **AC:** 模型可被 A0 engine 呼叫;walk-forward 切分正確;**過擬合護欄**(OOS 與 in-sample 並列呈現,不只報 in-sample)。
- **Test:** 介面相容;walk-forward 無洩漏;固定 seed 可重現。

### A-3 — 笨 baseline 群(Impl,並行)
- **Role:** Coder · **Effort:** S · **depends_on:** ["A-0"]
- **Description:** buy-and-hold TSMC、buy-and-hold QQQ/0050、靜態混合、隨機訊號。作為 LSTM 必須打贏的衡量尺。
- **AC:** 每個 baseline 皆 A0 介面相容、可入 leaderboard。
- **Test:** 介面相容;隨機 baseline 以固定 seed 可重現。

### A-4 — 對衝組合邏輯(Impl,並行)
- **Role:** Coder · **Effort:** M · **depends_on:** ["A-0"]
- **Description:** 將 LSTM 訊號轉成對衝部位(多核心/空或反向對衝),在 vol≤30% 預算內 sizing;(可選)接 `algo_pyramid` 做分批進場。
- **AC:** 組合權重滿足 vol 預算;部位邏輯文件化;與金字塔的接點為可選旗標。
- **Test:** 約束滿足測試;sizing 邊界案例。

### A-5 — 整合 leaderboard(Integration)
- **Role:** QA_Engineer · **Effort:** M · **depends_on:** ["A-1","A-2","A-3","A-4"]
- **Description:** 全 slice 走 A0 回測,產出 LSTM-對衝 vs 所有 baseline 的 OOS leaderboard。
- **AC:** leaderboard 產出且 net of cost;結果可重現;明確標示 LSTM 是否打贏 baseline(**允許輸,誠實呈現**)。
- **Test:** 端到端;重現性;成本後一致性。

### A-6 — QC + 一頁誠實 writeup(QC Review + Showcase)
- **Role:** QC_Reviewer · **Effort:** M · **depends_on:** ["A-5"]
- **Description:** 方法論審查(篩選無 lookahead、LSTM 無 OOS 洩漏、成本後報酬、樣本誠實);產出**作品集級一頁 writeup**(方法/結果/勝負/限制/負面結果)。
- **AC:** 無方法論漏洞;writeup 含誠實限制與負面結果;可重現附 config。**這頁是作品集的門面。**
- **Test:** 全綠;writeup peer-readable;repro 指令可一鍵重跑。
