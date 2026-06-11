# Design — Epic C:組合計算核心

> SDD Phase 2(**design 先於 implementation**)。需求:[requirements.md](./requirements.md)。

## 1. 架構

```
quantlab/portfolio/
  optimize.py    optimize_max_return_under_vol(mu, cov, vol_cap, w_max)  ← scipy SLSQP
  strategy.py    MeanVarianceStrategy(相容 A0 Strategy Protocol)
  multihorizon.py MultiHorizonMeanVarianceStrategy + HorizonConfig          [C-MULTI]
  pyramid.py     組合預算 → algo_pyramid 進場 adapter                      [C-PYRAMID]
(後續)
  rebalance.py   再平衡觸發(時間 + regime)            [C-REBAL]
```

資料流(C-1):
```
PIT data ─history(asof)→ 報酬 → μ(年化平均)、Σ(年化共變異)
                                   │
                       optimize_max_return_under_vol(vol_cap) ─SLSQP→ weights
                                   │
                      MeanVarianceStrategy.generate_signal → A0 回測
```

⚠️ `portfolio/` 屬策略/計算層,不在框架隔離契約內(用 numpy/scipy,無 ML 框架)。但**不得 import torch/tf/jax**(沿用 lab 慣例;非回測核心故 import-linter 不掃,仍自律)。

## 2. 最佳化設計(REQ-C-OPT-001)

問題:`max wᵀμ s.t. sqrt(wᵀΣw) ≤ vol_cap, w≥0, Σw=1`。

- **求解器:** `scipy.optimize.minimize(method="SLSQP")`,目標 `-wᵀμ`。
  - 約束:`Σw=1`(eq)、`vol_cap² − wᵀΣw ≥ 0`(ineq,用變異數避免 sqrt 不可微在 0)、bounds `[0, w_max]`。
  - 初值:等權。
- **不可行處理(AC-C-02):** 先解最小波動組合 `min wᵀΣw s.t. Σw=1, w≥0`;若其波動 > vol_cap → 直接回它(best-effort,vol_cap 無法滿足)。否則解主問題。
- **數值:** μ/Σ 以年化(月頻 ×12);vol = sqrt(年化變異)。

## 3. 策略設計(REQ-C-STRAT-001)

`MeanVarianceStrategy(symbols, vol_cap=0.30, lookback=36, min_obs=24)`:
- `generate_signal(asof, data)`:`data.history(asof,"close",symbols).dropna()` → 報酬 → 取最近 `lookback` → μ/Σ → optimize → `{sym: w}`。
- 歷史 < `min_obs` → 等權(無法可靠估 Σ)。
- 確定性:純 numpy/scipy,同輸入同輸出(可重現,符合 A0 DoD)。
- maxDD 約束:**不在最佳化內**(路徑相依);由回測 realized maxDD ex-post 呈現(誠實)。

## 3.5 多期配置設計(REQ-C-MULTI-001)

`HorizonConfig(name, lookback, vol_cap, budget_weight)` 定義單一配置 horizon。

`MultiHorizonMeanVarianceStrategy(symbols, horizons, min_obs=24)`:
- `generate_signal(asof, data)` 只透過 `data.history(asof,"close",symbols)` 讀取 PIT history。
- 每個 horizon 對最近 `lookback` 報酬各自估 μ/Σ,呼叫 C-1 optimizer 取得 horizon 權重。
- 依 `budget_weight / sum(budget_weight)` 將多個 horizon 權重線性混合,最後 clip + normalize 成單一 long-only、sum=1 配置。
- 若整體或單一 horizon 歷史不足,該 horizon 以等權回退,避免短樣本產生過度集中。
- C-2 不引入 regime 判斷;regime hook 仍屬 C-3 / Epic D 邊界。

## 4. Lightweight FMEA

| Risk ID | Failure Mode | Effect | Control | Task |
|---|---|---|---|---|
| FMEA-C-01 | Σ 估計不穩(短歷史)→ 極端權重 | 過度集中 | min_obs 門檻 + bounds w_max;歷史不足回等權 | C-1 |
| FMEA-C-02 | vol_cap 不可行卻丟例外 | 回測中斷 | best-effort 回退最小波動(AC-C-02) | C-1 |
| FMEA-C-03 | 把 vol 約束當成 maxDD 達標 | overclaim | 文件明示 maxDD 為 ex-post,不在最佳化內 | C-1/review |
| FMEA-C-04 | 用未來資料估 μ/Σ | lookahead | 只用 `history(asof)`,A0 PIT 守門 | C-1 |
| FMEA-C-05 | 多期權重混合後未正規化 | 槓桿或現金暴露失真 | final clip + normalize;測試 sum=1/long-only | C-2 |
| FMEA-C-06 | 短 horizon 樣本不足仍最佳化 | 極端配置 / 假穩定 | per-horizon `min_obs` 不足回等權 | C-2 |

## 5. REQ → Design / Test
| REQ | Design | Test |
|---|---|---|
| OPT-001 | §2 | test_c_1(AC-C-01/02) |
| STRAT-001 | §3 | test_c_1(AC-C-03) |
| MULTI-001 | §3.5 | test_c_2(AC-C-04/05) |
