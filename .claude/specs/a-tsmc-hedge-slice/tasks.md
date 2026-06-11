# Tasks — Epic A:反台積電對衝 thin slice

> SDD Phase 3。**as-built**(已實作於 PR #2)。執行紀律:嚴格 TDD = RED → GREEN → REFACTOR。
> 需求:[requirements.md](./requirements.md) · 設計:[design.md](./design.md) · verdict:[review.md](./review.md)
> 全部 ✅ 完成。全套 83 tests(Epic A 範圍)· mypy clean · 框架隔離 KEPT。

| Task | 內容 | Implements | RED→GREEN→REFACTOR | Commit |
|---|---|---|---|---|
| **A-1** ✅ | 共整合-反向篩選(Engle-Granger)+ `history()` PIT 存取器;可平行 | SCREEN-001/002, DATA-001, AC-A-01/02/03 | 3→3→抽 helper | 64c9f3e |
| **A-3** ✅ | 笨 baseline 群(StaticWeights/RandomStrategy;BuyAndHold 沿用 A0) | BASE-001 | 4→4→— | 5407211 |
| **A-4** ✅ | 對衝部位建構(build_hedge_weights + HedgeStrategy)+ 降波動 showcase;screen min_obs 守護 | HEDGE-001 | 4→4→— | 8334657 |
| **A-5** ✅ | 全鏈整合 leaderboard(run_hedge_slice)+ metrics robustness 防護 | INT-001 | 2→2→型別 | c3114f9 |
| **A-2** ✅ | PyTorch LSTM 擇時(PIT 懶訓練、CPU 可重現、torch 隔離策略層) | LSTM-001 | 4→4→— | 4e5c7b7 |
| **A-6** ✅ | 一頁誠實 writeup + 可重現執行器 | DOC-001 | (doc) | 7b2970e |

## 執行順序說明
實作順序為 A-1 → A-3 → A-4 → A-5 → A-2 → A-6(刻意把無 torch 的篩選/對衝/整合先做完,
形成完整可跑 slice,再裝 PyTorch 加 LSTM;符合「完成的深度 > 未完成的廣度」)。

## 注意（as-built 補記）
- A-0「contract」未獨立成 task:Epic A 直接複用 A0 的 `Strategy`/`DataProvider` 等 contract,
  僅以 `history()` additive 擴充,故未另立 contract task。
- 後續可補:LSTM 週期重訓 / 超參搜尋、真實資料(Epic B)替換合成 provider。
