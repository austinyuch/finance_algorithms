# Tasks — Epic C:組合計算核心

> SDD Phase 3。執行紀律:嚴格 TDD = RED → GREEN → REFACTOR(且 **design 先於 implementation**)。
> 需求:[requirements.md](./requirements.md) · 設計:[design.md](./design.md)

| Task | 內容 | Implements | 狀態 |
|---|---|---|---|
| **C-1** ✅ | 組合最佳化器(max return s.t. vol≤cap,SLSQP;不可行回退最小波動)+ `MeanVarianceStrategy` | OPT-001, STRAT-001, AC-C-01/02/03 | **DONE**(commit b33a40a) |
| **C-4** ✅ | 組合預算 → `algo_pyramid` 進場 adapter(敘事閉環,additive) | PYRAMID-001 | **DONE**(commit 8def1f4) |
| **C-5** ✅ | 整合 leaderboard(MeanVariance vs baselines)+ 全鏈重現 + review | — | **DONE**([review.md](./review.md)) |
| **C-2** ⬜ | 多期(短/中/長)配置 | MULTI-001 | planned |
| **C-3** ⬜ | 再平衡觸發(時間 + regime hook;regime 依賴 Epic D) | REBAL-001 | planned |

## 注意
- maxDD 硬約束為 ex-post(回測 realized）；C-1 最佳化只強制 vol_cap(誠實標註，FMEA-C-03)。
- C-4 對 `invest_algorithms/algo_pyramid` 為 additive adapter；若需改其行為才需 CR。
