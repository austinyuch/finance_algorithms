# Epic Breakdown — Portfolio-grade 個人 Quant 研究 Lab

> 來源:[01-problem-space.md](./01-problem-space.md)。本檔 = Epic→Task 樹主檔。
> 依 DEEP 原則:**A0 / A 拆到 task 級(可直接進 SDD);B~G 為 epic 級骨架**,輪到時再細拆。
> 詳細 task:[epics/A0-backtest-foundation.md](./epics/A0-backtest-foundation.md)、[epics/A-tsmc-hedge-slice.md](./epics/A-tsmc-hedge-slice.md)

---

## 0. 鎖定約束(拆 task 時的硬規則)

- 個人自用 / 純紙上(不接券商,假設 A2′)。成功 = 實驗能力 + 方法論誠實度,非 alpha。
- 雙目的:作品集 + 投資研究 lab → **兩速結構**(curated showcase 層 vs messy lab 層)。
- 每模型 DoD:能在 A0 產出「**可與笨 baseline 並排比較的 OOS 績效報告**」。
- 三框架(PyTorch/TF/JAX)一級目標;harness 對框架無感;禁同模型港三遍(R1)。
- 風險守則:R1(yak-shaving,綁 milestone)、R2(回測謊言,A0 先正確)、R3(過早抽象,Tier3 延後)。

---

## 1. Epic 清單與分層

| Epic | 名稱 | 優先 | Showcase 完成度 | Lab 實驗性 | Lane 建議 |
|---|---|---|---|---|---|
| **A0** | 回測引擎 + Tier1 平行底座 + Tier2 追蹤 | P0(地基) | 中(嚴謹度本身是賣點) | 低(基礎設施) | **獨立 foundation lane** |
| **A** | Thin slice:反台積電對衝 → LSTM → 回測 vs baseline | P0(作品集中心) | **高(打磨到底)** | 中 | 接 A0 主線 |
| **B** | 資料層擴充(總經/氣候/多資產 point-in-time) | P1 | 低 | 中 | 可與 C 部分並行 |
| **C** | 組合計算核心(配置最佳化 + 再平衡 + 金字塔整合) | P1 | 中 | 中 | 主線 |
| **D** | ML 模型族(regime→預測→最佳化→事件驅動) | P2 | 中 | **高** | 主線 + 各模型可並行 lane |
| **E** | Tier3 完整 MLOps | P3(延後) | 中 | 低 | 萃取後獨立 lane |
| **F** | Next.js 前端(showcase 展示面) | P2 | **高** | 低 | 獨立 FE lane |
| **G** | Alt-data / NLP / 衛星(OPTIONAL) | P4(另開戰線) | 低 | **高** | **獨立 optional lane** |

---

## 2. 相依 DAG 與關鍵路徑

```
A0 (回測地基 + 平行 + 追蹤)
 │   └── 關鍵路徑起點,一切之上
 ├─> A   (反台積電 thin slice;作品集第一個完成品)   ← 第一個 milestone
 ├─> B   (資料層擴充)
 │     └─> C  (組合計算核心,需多資產 point-in-time 資料)
 │           └─> D  (ML 模型族,需 B 資料 + C 最佳化框架 + A0 回測)
 │                 └─> E  (Tier3 MLOps,從 D 的實驗痛點萃取)   ← 延後
 ├─> F   (前端;A 之後即可展示 leaderboard,隨 C/D 擴充)
 └┄┄> G  (alt-data;optional,鎖 A0 紀律,獨立 lane)
```

**關鍵路徑(critical path):** `A0 → A`(證明地基)→ `B → C → D`(研究主幹)→ `E`。
**第一個可交付 milestone:** A0 + A = 一條端到端、point-in-time 正確、有誠實 baseline 比較的 showcase 切片。

### 並行機會
- A0 內部 4 個 implementation task 可並行(見 A0 詳細)。
- A 完成後:**B、F 可並行**(F 先展示 A 的 leaderboard;B 鋪資料)。
- D 的各模型族(regime / 報酬預測 / 事件驅動)在 C 完成後**可並行 lane**,各自打同一 baseline。
- G 全程獨立 optional lane,不阻塞主線。

### 需獨立 branch/worktree lane(高衝突/大改面)
- **A0**:大型地基,介面一旦定義會被全專案依賴 → 獨立 lane 先穩定 contract。
- **G**:optional 另開戰線,避免污染主線。
- **E**:Tier3 平台萃取,大改面。
- **F**:前端技術棧(Next.js)與後端 Python 分離,獨立 lane。

---

## 3. 兩速結構(作品集 vs lab)落點

- **Showcase 層(curated,要打磨):** Epic A 全部、Epic F、各 epic 的「一頁誠實 writeup」、leaderboard 展示。
- **Lab 層(messy,可快可髒):** Epic D 的模型實驗、Epic G、A0 之後的探索性 sweep。
- **硬規則:** showcase 層任何東西都要能重現(seed/資料版本/config)、要有誠實結論(含負面結果與 n)。

---

## 4. 各 Epic Task 概覽

> A0 / A 已拆到 task 級(連結見下)。B~G 列 epic 級切分,進 SDD 時再套同樣的 Contract→Impl(2-4 並行)→Integration→QC 模板細拆。

### Epic A0 — 詳見 [epics/A0-backtest-foundation.md](./epics/A0-backtest-foundation.md)
7 tasks:介面 contract → (point-in-time DataProvider / 回測引擎核心 / Tier1 平行底座 / Tier2 追蹤)4 並行 → 整合(含 lookahead golden test)→ 方法論 QC。

### Epic A — 詳見 [epics/A-tsmc-hedge-slice.md](./epics/A-tsmc-hedge-slice.md)
7 tasks:實驗協定 contract(含「反指標」精確定義)→ (反台積電篩選 sweep / LSTM 訊號 / 笨 baseline 群 / 對衝組合邏輯)4 並行 → 整合 leaderboard → QC + 一頁 writeup。

### Epic B — 資料層擴充(epic 級切分)
- B-contract:統一 point-in-time 資料介面 + 來源 adapter 契約(行情/總經/氣候)。
- B-impl(並行):多資產行情 adapter|總經 adapter(FED/財政/CPI/GDP,含 release-date lag)|氣候 adapter(El Niño/ENSO 指數)|缺值與頻率對齊 + 資料版本/設定管理。
- B-integration:跨來源 as-of join 正確性測試(無 lookahead)。B-QC:資料品質與授權合規審查。

### Epic C — 組合計算核心(epic 級切分)
- C-contract:Allocator 介面(吃預期/約束,吐權重)+ 再平衡訊號介面 + 金字塔進場 adapter 契約。
- C-impl(並行):報酬最大化 + vol/maxDD 硬約束最佳化器|多期(短中長)配置|再平衡觸發(時間 + regime)|與 `algo_pyramid` 進場整合。
- C-integration:配置→金字塔進場→回測 端到端。C-QC:約束滿足 + 數值穩定性審查。

### Epic D — ML 模型族(epic 級切分,各模型可並行)
- D-contract:統一 model 實驗協定(對齊 A0 薄介面 + DoD 報告格式)。
- D-impl(逐一打 baseline,可並行 lane):regime/phase 分類|各資產報酬/風險預測|組合最佳化模型|**事件驅動(event-study + NLP 偵測 + 類比庫,硬限制 D-E1~E3)**。
- D-integration:各模型 OOS vs 笨 baseline leaderboard。D-QC:**過擬合/lookahead/小樣本誠實度**對抗式審查(此 epic 的 QC 最關鍵)。

### Epic E — Tier3 完整 MLOps(延後;從 D 痛點萃取)
- 進入條件:至少 2~3 個 D 模型手動跑通後。E-contract:model registry + 實驗→生產契約。impl:registry/自動重訓/drift 監控/serving/CI-CD。**禁止在 D 跑通前啟動(R3)。**

### Epic F — Next.js 前端(showcase 展示面)
- F-contract:後端 read API 契約(leaderboard/配置/regime/再平衡)。impl(並行):leaderboard 展示|配置與 regime 儀表板|再平衡建議檢視|writeup/報告頁。F-QC:可重現展示 + UX。

### Epic G — Alt-data(OPTIONAL / 獨立 lane)
- 進入條件:主線穩定 + 明確 milestone。G-contract:文本/情緒 point-in-time 攝取契約(時間戳=可讀取時間,禁回填重算)。impl:輿論/情緒爬取|GenAI/NLP 情緒分析|(後期)衛星數據。**綁 milestone,禁開放式探索(R1)。**

---

## 5. 建議的 SDD 進入點

**Epic A0**(預設)。理由:它是關鍵路徑起點、皇冠鑽石、且其介面 contract 會被全專案依賴 — 必須先在獨立 foundation lane 把 `requirements.md`(尤其 point-in-time 正確性、平行、追蹤的可驗收標準)定清楚。A 緊接其後作為第一個 showcase 完成品。

> 下一步:交給 `spec-driven-development`,在 A0 lane 開 `requirements.md`。
