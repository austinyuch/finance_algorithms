# Requirements — Epic C:組合計算核心(最佳化 + 再平衡 + 金字塔整合)

> SDD Phase 1。Spec: `c-portfolio-core`。分支 `spec/c-portfolio-core`。
> 上游:[../allweather-portfolio-platform/02-epic-breakdown.md](../allweather-portfolio-platform/02-epic-breakdown.md)(Epic C)、A0/A/B(已 merged)。

## 0. Governance
- **Work classification:** `new spec`。
- **Depends On:** `a0-backtest-foundation`(Strategy/Engine/DataProvider)、`b-data-platform`(資料)。
- **Impacts:** 未來 C-4 與 `invest_algorithms/algo_pyramid`(進場整合,**additive adapter,不改既有金字塔**)。
- **First-slice boundary(C-1):** 組合最佳化器 + 一個 Strategy:依 PIT 歷史估 μ/Σ,**最大化預期報酬 s.t. 年化波動 ≤ vol_cap**,long-only、sum=1;可丟進 A0 回測。
- **Continuation boundary(C-2):** 多期配置只混合短/中/長 horizon 的配置權重;不引入 regime 判斷,不改 A0 engine,不改 legacy `algo_pyramid`。
- **Continuation boundary(C-3):** portfolio 層提供時間 + regime-label 再平衡日期 selector,消費 Epic D `predict(asof,data)` signal contract;不改 A0 engine 排程。

## 1. 鎖定目標函數(承 problem-space)
> `maximize E[3~5yr 報酬] s.t. 年化波動 ≤ 30%、maxDD ≤ -50%`(積極成長 + 風險上限)。
- C-1 落實**硬約束 = 年化波動 ≤ vol_cap**(可解的凸/SLSQP 問題)。
- **maxDD ≤ -50% 為 ex-post 檢核**(路徑相依,非權重的簡單函數)→ 由回測 leaderboard 的 realized maxDD 呈現;C-1 不在最佳化內強制(誠實標註)。

## 2. Functional Requirements
- **REQ-C-OPT-001**(C-1)`optimize_max_return_under_vol(mu, cov, vol_cap, w_max)`:long-only、sum=1、年化波動 ≤ vol_cap 下最大化 `wᵀμ`;若連最小波動組合都超過 vol_cap → 回退最小波動組合(best-effort)。
- **REQ-C-STRAT-001**(C-1)`MeanVarianceStrategy`:相容 A0 Strategy Protocol;每 asof 由 PIT 歷史估 μ(年化平均)/Σ(年化共變異)→ 最佳化 → 權重;歷史不足 → 等權。
- **REQ-C-MULTI-001**(C-2)多期(短/中/長)配置:`MultiHorizonMeanVarianceStrategy` 應各自使用 horizon-specific `lookback` / `vol_cap` 估權重,再依 `budget_weight` 混合成單一 long-only、sum=1 配置;歷史不足時回等權。
- **REQ-C-REBAL-001**(C-3)再平衡觸發(時間 + regime):應選出第一個觀測日、指定時間頻率到期日,以及 regime label 改變日;可直接消費 D classifier。
- **REQ-C-PYRAMID-001**(後續)組合決定各資產預算後,進場接 `algo_pyramid`(adapter)。

## 3. Acceptance Criteria(C-1 / C-2 / C-3)

#### AC-C-01 最佳化滿足約束且最大化報酬(REQ-C-OPT-001)
1. Given μ、Σ、vol_cap
2. When 最佳化
3. Then 回傳權重 w≥0、Σw=1、`sqrt(wᵀΣw) ≤ vol_cap + 容差`
4. And 在可行域內,較高 vol_cap 的最優目標值(wᵀμ)≥ 較低 vol_cap(放寬約束不會更差)

#### AC-C-02 vol_cap 過嚴 → 回退最小波動(REQ-C-OPT-001)
1. Given vol_cap 低於最小可達波動
2. When 最佳化
3. Then 回傳最小波動組合(不丟例外)

#### AC-C-03 策略 PIT + 相容 + 可重現(REQ-C-STRAT-001)
1. Given 合成多資產 PIT 資料
2. When `MeanVarianceStrategy.generate_signal(asof, data)`
3. Then 相容 Strategy Protocol、權重 sum=1、只用 PIT 歷史;歷史不足回等權
4. And 同輸入 → 同權重(可重現)

#### AC-C-04 多期配置混合且正規化(REQ-C-MULTI-001)
1. Given 短/中/長 horizon 設定與合成多資產 PIT 資料
2. When `MultiHorizonMeanVarianceStrategy.generate_signal(asof, data)`
3. Then 每個 horizon 應只使用 `history(asof)` 可得資料估權重
4. And 輸出權重應 long-only、sum=1、同輸入可重現

#### AC-C-05 多期歷史不足時保守回退(REQ-C-MULTI-001)
1. Given PIT history 少於 `min_obs`
2. When `MultiHorizonMeanVarianceStrategy.generate_signal(asof, data)`
3. Then 系統應回傳等權配置,不丟例外,不產生集中配置

#### AC-C-06 時間 + regime 再平衡 selector(REQ-C-REBAL-001)
1. Given 有序日期與對應 regime labels
2. When `select_rebalance_dates(dates, labels, frequency)`
3. Then 第一個日期必定入選,時間頻率到期日入選,regime label 改變日入選
4. And 結果保持有序、為輸入日期子集合,日期與 label 長度不一致時 fail-closed

#### AC-C-07 D regime classifier hook(REQ-C-REBAL-001)
1. Given D `FirstRegimeClassifier` 與 PIT provider
2. When `select_regime_rebalance_dates(dates, classifier, data, frequency)`
3. Then selector 只透過 `classifier.predict(asof,data).label` 取得 regime,不耦合 ML framework 或改 A0 engine

## 4. Out of Scope（本回合）
A0 engine-level event scheduling remains future work. 金字塔進場整合已由 C-4 additive adapter 完成。
