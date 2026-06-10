"""A-3 笨 baseline 群 — RED 階段測試。

對應 a-tsmc-hedge-slice REQ-A-BASE-001。baseline = LSTM 等花俏模型必須打敗的衡量尺;
皆須相容 A0 Strategy Protocol、可入 leaderboard、且(random)可重現。
"""
from __future__ import annotations

import pandas as pd
import pytest


def _toy():
    from quantlab.data.provider import InMemoryPITDataProvider
    ts = pd.Timestamp
    dates = [ts("2020-01-31"), ts("2020-02-29"), ts("2020-03-31"), ts("2020-04-30")]
    series = {"X": [100.0, 110.0, 99.0, 121.0], "Y": [50.0, 48.0, 55.0, 52.0]}
    rows = [{"symbol": s, "event_date": d, "available_date": d, "close": series[s][i]}
            for s in series for i, d in enumerate(dates)]
    prices = pd.DataFrame(rows)
    listings = pd.DataFrame([{"symbol": s, "list_date": ts("2019-01-01"), "delist_date": pd.NaT}
                             for s in series])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro)


def _cfg():
    return {"start": "2020-01-31", "end": "2020-04-30", "rebalance": "monthly",
            "fill": "same_close", "mode": "net",
            "cost_config": {"commission_bps": 5, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
                            "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
            "seed": 0, "data_version": "toy",
            "walk_forward": {"train_window_months": 1, "test_window_months": 1, "step_months": 1}}


def test_static_weights_conforms_and_normalizes():
    from quantlab.contracts import Strategy
    from quantlab.strategies import StaticWeights

    s = StaticWeights({"X": 3.0, "Y": 1.0})
    assert isinstance(s, Strategy)
    w = s.generate_signal(pd.Timestamp("2020-01-31"))
    assert w == pytest.approx({"X": 0.75, "Y": 0.25})      # 正規化到和為 1


def test_random_strategy_reproducible_and_conforms():
    from quantlab.contracts import Strategy
    from quantlab.strategies import RandomStrategy

    asof = pd.Timestamp("2020-01-31")
    a = RandomStrategy(["X", "Y", "Z"], seed=7)
    b = RandomStrategy(["X", "Y", "Z"], seed=7)
    assert isinstance(a, Strategy)
    assert a.generate_signal(asof) == b.generate_signal(asof)        # 同 seed → 一致
    w = a.generate_signal(asof)
    assert sum(w.values()) == pytest.approx(1.0)                     # 正規化
    assert all(v >= 0 for v in w.values())
    # 不同 seed 多半不同
    assert RandomStrategy(["X", "Y", "Z"], seed=8).generate_signal(asof) != w


def test_baselines_run_through_engine_and_leaderboard(tmp_path):
    from quantlab.runner import run_and_log
    from quantlab.strategies import BuyAndHold, RandomStrategy, StaticWeights
    from quantlab.tracking import LocalResultStore

    store = LocalResultStore(tmp_path / "s.db")
    data = _toy()
    for strat in (BuyAndHold(["X"]), StaticWeights({"X": 1, "Y": 1}), RandomStrategy(["X", "Y"], seed=3)):
        run_and_log(strat, data, _cfg(), store)

    board = store.leaderboard()
    assert len(board) == 3
    vals = [(-1e18 if r["oos_net_sharpe"] is None else r["oos_net_sharpe"]) for r in board]
    assert vals == sorted(vals, reverse=True)                       # 排序
    for row in board:
        assert store.get(row["run_id"])["strategy_name"] == row["strategy_name"]  # 可追溯


def test_random_strategy_backtest_reproducible(tmp_path):
    from quantlab.runner import run_and_log
    from quantlab.strategies import RandomStrategy
    from quantlab.tracking import LocalResultStore

    store = LocalResultStore(tmp_path / "s.db")
    data = _toy()
    _, r1 = run_and_log(RandomStrategy(["X", "Y"], seed=5), data, _cfg(), store)
    _, r2 = run_and_log(RandomStrategy(["X", "Y"], seed=5), data, _cfg(), store)
    assert r1["metrics"] == r2["metrics"]                           # 全鏈重現
