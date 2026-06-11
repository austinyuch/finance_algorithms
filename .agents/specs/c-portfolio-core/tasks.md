# Tasks — Epic C:組合計算核心

> SDD Phase 3。執行紀律:嚴格 TDD = RED → GREEN → REFACTOR(且 **design 先於 implementation**)。
> 需求:[requirements.md](./requirements.md) · 設計:[design.md](./design.md)

| Task | 內容 | Implements | 狀態 |
|---|---|---|---|
| **C-1** | 組合最佳化器(max return s.t. vol≤cap,SLSQP;不可行回退最小波動)+ `MeanVarianceStrategy`(PIT、相容、可重現) | OPT-001, STRAT-001, AC-C-01/02/03 | in progress |
| **C-2** | 多期(短/中/長)配置 | MULTI-001 | planned |
| **C-3** | 再平衡觸發(時間 + regime hook) | REBAL-001 | planned |
| **C-4** | 組合預算 → `algo_pyramid` 進場 adapter(**additive,不改既有金字塔**) | PYRAMID-001 | planned |
| **C-5** | 整合 leaderboard(最佳化策略 vs baselines)+ review | — | planned |

## 注意
- maxDD 硬約束為 ex-post(回測 realized）；C-1 最佳化只強制 vol_cap(誠實標註，FMEA-C-03)。
- C-4 對 `invest_algorithms/algo_pyramid` 為 additive adapter；若需改其行為才需 CR。
