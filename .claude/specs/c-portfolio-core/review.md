# Review — Epic C:組合計算核心

> SDD Phase 5。verdict authority。
> 驗證:`uv run pytest -q` → **123 passed**;`uv run mypy quantlab/ --ignore-missing-imports` → clean(39 files);`uv run lint-imports` → KEPT。

## Verdict:**PASSED(core+C-2+C-3)**

Epic C 核心(最佳化器 + 多期配置 + 時間/regime 再平衡 selector + 金字塔進場閉環 + 全鏈驗證)完成且有測試。C-3 以 additive portfolio helper 消費 Epic D regime signal contract,不改 A0 engine 排程。

## REQ / Task → Evidence

| Task | 內容 | 證據 |
|---|---|---|
| C-1 ✅ | 組合最佳化器(max return s.t. vol≤cap,SLSQP)+ MeanVarianceStrategy | test_c_1_optimize |
| C-2 ✅ | 多期(短/中/長)配置 + horizon budget 混合 + 歷史不足回退 | test_c_2_multihorizon |
| C-4 ✅ | 組合預算 → algo_pyramid 進場 adapter(敘事閉環) | test_c_4_pyramid |
| C-5 ✅ | 整合 leaderboard(MeanVariance vs baselines)+ 全鏈重現 | test_c_5_integration |
| C-3 ✅ | 再平衡觸發(時間 + regime hook;消費 Epic D classifier signal) | test_c_3_rebalance |

## 達成的核心價值

- **鎖定目標函數落地**:problem-space 的「max 3~5 年報酬 s.t. vol≤30%」→ 可解的 SLSQP 最佳化器 + 可回測策略。
- **多期配置落地**:短/中/長 horizon 各自估權重後用 budget_weight 混合,保持 PIT、long-only、sum=1 與歷史不足保守回退。
- **C-3 selector 落地**:第一個觀測日、時間頻率到期日與 regime label 改變日會被選入,並可透過 D `FirstRegimeClassifier` smoke 驗證。
- **敘事閉環**:本 repo 從「單標的金字塔計算器」→「多資產組合最佳化 → 各資產金字塔左側進場」。C-4 additive 接回既有 `algo_pyramid`,未改其行為(33 既有測試仍綠)。

## Residual / 刻意降級
- **maxDD ≤ -50% 為 ex-post**(路徑相依,不在最佳化內;由回測 realized maxDD 呈現)。誠實標註(FMEA-C-03)。
- A0 engine-level event scheduling 尚未改;C-3 目前是 portfolio-layer selector,避免擴大引擎行為面。
- μ/Σ 為樣本估計(估計誤差固有);min_obs + bounds 緩解極端權重(FMEA-C-01)。

## 交棒
最佳化、多期策略與 C-3 selector 可在真實資料(Epic B 累積後)重跑;若後續需要交易日逐日事件驅動,再以 A0 engine-level scheduling enhancement 另開 scope。
