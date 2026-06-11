"""C-1 組合最佳化器 + MeanVarianceStrategy — RED 階段測試。

對應 c-portfolio-core REQ-C-OPT-001 / REQ-C-STRAT-001 / AC-C-01/02/03。
目標:max wᵀμ s.t. 年化波動 ≤ vol_cap、long-only、Σw=1。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

# 3 資產:不相關,變異 0.04/0.09/0.16(年化波動 0.2/0.3/0.4),μ 遞減
MU = np.array([0.12, 0.09, 0.05])
COV = np.diag([0.04, 0.09, 0.16])


def _vol(w):
    return float(np.sqrt(w @ COV @ w))


# --- AC-C-01:滿足約束 + 放寬 vol_cap 不會更差 ---

def test_optimize_satisfies_constraints():
    from quantlab.portfolio.optimize import optimize_max_return_under_vol

    w = optimize_max_return_under_vol(MU, COV, vol_cap=0.25)
    assert w.min() >= -1e-9                          # long-only
    assert abs(w.sum() - 1.0) < 1e-6                 # Σw=1
    assert _vol(w) <= 0.25 + 1e-4                    # 波動約束


def test_optimize_higher_cap_not_worse():
    from quantlab.portfolio.optimize import optimize_max_return_under_vol

    obj_low = MU @ optimize_max_return_under_vol(MU, COV, vol_cap=0.22)
    obj_high = MU @ optimize_max_return_under_vol(MU, COV, vol_cap=0.35)
    assert obj_high >= obj_low - 1e-6                # 放寬約束 → 目標不更差


# --- AC-C-02:vol_cap 過嚴 → 回退最小波動,不丟例外 ---

def test_optimize_infeasible_returns_min_vol():
    from quantlab.portfolio.optimize import optimize_max_return_under_vol

    w = optimize_max_return_under_vol(MU, COV, vol_cap=1e-6)
    assert abs(w.sum() - 1.0) < 1e-6
    assert w.min() >= -1e-9
    eqw = np.ones(3) / 3
    assert _vol(w) <= _vol(eqw) + 1e-6              # 最小波動 ≤ 任意組合


# --- AC-C-03:策略 PIT + 相容 + 可重現 ---

def _synth(n=72):
    from quantlab.data.provider import InMemoryPITDataProvider
    rng = np.random.default_rng(0)
    dates = pd.date_range("2015-01-31", periods=n, freq="ME")
    series = {
        "A": 100 * np.cumprod(1 + rng.normal(0.008, 0.05, n)),
        "B": 100 * np.cumprod(1 + rng.normal(0.006, 0.07, n)),
        "C": 100 * np.cumprod(1 + rng.normal(0.004, 0.03, n)),
    }
    rows = [{"symbol": s, "event_date": d, "available_date": d, "close": float(series[s][i])}
            for s in series for i, d in enumerate(dates)]
    prices = pd.DataFrame(rows)
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("2014-01-01"), "delist_date": pd.NaT}
                             for s in series])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro), dates


def test_mean_variance_strategy_conforms_pit_reproducible():
    from quantlab.contracts import Strategy
    from quantlab.portfolio.strategy import MeanVarianceStrategy

    data, dates = _synth()
    s = MeanVarianceStrategy(["A", "B", "C"], vol_cap=0.30)
    assert isinstance(s, Strategy)

    w = s.generate_signal(dates[-1], data)
    assert set(w) == {"A", "B", "C"}
    assert abs(sum(w.values()) - 1.0) < 1e-6
    assert all(v >= -1e-9 for v in w.values())
    # 可重現
    assert MeanVarianceStrategy(["A", "B", "C"], vol_cap=0.30).generate_signal(dates[-1], data) == w


def test_mean_variance_insufficient_history_equal_weight():
    from quantlab.portfolio.strategy import MeanVarianceStrategy

    data, dates = _synth()
    w = MeanVarianceStrategy(["A", "B", "C"], min_obs=24).generate_signal(dates[3], data)  # 早期
    assert w == pytest.approx({"A": 1 / 3, "B": 1 / 3, "C": 1 / 3})
