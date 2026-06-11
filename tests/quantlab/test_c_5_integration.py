"""C-5 組合最佳化整合 — RED 階段測試。

對應 c-portfolio-core REQ-C-STRAT-001 整合驗證:
MeanVarianceStrategy + 笨 baselines 全鏈 → A0 PIT 回測 → leaderboard。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _synth(n=72):
    from quantlab.data.provider import InMemoryPITDataProvider
    rng = np.random.default_rng(1)
    dates = pd.date_range("2015-01-31", periods=n, freq="ME")
    series = {
        "EQ": 100 * np.cumprod(1 + rng.normal(0.009, 0.05, n)),    # 高報酬高波動
        "BOND": 100 * np.cumprod(1 + rng.normal(0.003, 0.015, n)),  # 低報酬低波動
        "GOLD": 100 * np.cumprod(1 + rng.normal(0.004, 0.04, n)),
    }
    rows = [{"symbol": s, "event_date": d, "available_date": d, "close": float(series[s][i])}
            for s in series for i, d in enumerate(dates)]
    prices = pd.DataFrame(rows)
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("2014-01-01"), "delist_date": pd.NaT}
                             for s in series])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro), dates


def _cfg(dates):
    return {"start": str(dates[0].date()), "end": str(dates[-1].date()), "rebalance": "monthly",
            "fill": "same_close", "mode": "net",
            "cost_config": {"commission_bps": 5, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
                            "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
            "seed": 0, "data_version": "synth",
            "walk_forward": {"train_window_months": 36, "test_window_months": 12, "step_months": 12}}


def test_mean_variance_in_leaderboard(tmp_path):
    from quantlab.portfolio import MeanVarianceStrategy
    from quantlab.runner import run_and_log
    from quantlab.strategies import BuyAndHold, RandomStrategy, StaticWeights
    from quantlab.tracking import LocalResultStore

    data, dates = _synth()
    store = LocalResultStore(tmp_path / "s.db")
    universe = ["EQ", "BOND", "GOLD"]
    for strat in (MeanVarianceStrategy(universe, vol_cap=0.20),
                  BuyAndHold(["EQ"]), StaticWeights({s: 1 for s in universe}),
                  RandomStrategy(universe, seed=2)):
        run_and_log(strat, data, _cfg(dates), store)

    board = store.leaderboard()
    names = [r["strategy_name"] for r in board]
    assert "MeanVarianceStrategy" in names
    assert len(board) == 4
    vals = [(-1e18 if r["oos_net_sharpe"] is None else r["oos_net_sharpe"]) for r in board]
    assert vals == sorted(vals, reverse=True)
    for row in board:
        assert store.get(row["run_id"])["strategy_name"] == row["strategy_name"]


def test_mean_variance_backtest_reproducible(tmp_path):
    from quantlab.portfolio import MeanVarianceStrategy
    from quantlab.runner import run_and_log
    from quantlab.tracking import LocalResultStore

    data, dates = _synth()
    s = LocalResultStore(tmp_path / "s.db")
    _, r1 = run_and_log(MeanVarianceStrategy(["EQ", "BOND", "GOLD"], vol_cap=0.20), data, _cfg(dates), s)
    _, r2 = run_and_log(MeanVarianceStrategy(["EQ", "BOND", "GOLD"], vol_cap=0.20), data, _cfg(dates), s)
    assert r1["metrics"] == r2["metrics"]
