# Tasks — Epic C:組合計算核心

> SDD Phase 3。執行紀律:嚴格 TDD = RED → GREEN → REFACTOR(且 **design 先於 implementation**)。
> 需求:[requirements.md](./requirements.md) · 設計:[design.md](./design.md)

| Task | 內容 | Implements | 狀態 |
|---|---|---|---|
| **C-1** ✅ | 組合最佳化器(max return s.t. vol≤cap,SLSQP;不可行回退最小波動)+ `MeanVarianceStrategy` | OPT-001, STRAT-001, AC-C-01/02/03 | **DONE**(commit b33a40a) |
| **C-2** ✅ | 多期(短/中/長)配置:`HorizonConfig` + `MultiHorizonMeanVarianceStrategy`;horizon 權重混合後正規化,歷史不足回等權 | MULTI-001, AC-C-04/05 | **DONE**(tests `test_c_2_multihorizon`;12 C tests passed local) |
| **C-4** ✅ | 組合預算 → `algo_pyramid` 進場 adapter(敘事閉環,additive) | PYRAMID-001 | **DONE**(commit 8def1f4) |
| **C-5** ✅ | 整合 leaderboard(MeanVariance vs baselines)+ 全鏈重現 + review | — | **DONE**([review.md](./review.md)) |
| **C-3** ✅ | 再平衡觸發(時間 + regime hook;消費 Epic D signal contract,不改 A0 engine) | REBAL-001, AC-C-06/07 | **DONE**(tests `test_c_3_rebalance`;PBT + mutation spot-check + smoke) |

## 注意
- maxDD 硬約束為 ex-post(回測 realized）；C-1 最佳化只強制 vol_cap(誠實標註，FMEA-C-03)。
- C-4 對 `invest_algorithms/algo_pyramid` 為 additive adapter；若需改其行為才需 CR。
