"""A-5 反台積電對衝 thin slice 整合 — RED 階段測試。

對應 a-tsmc-hedge-slice REQ-A-INT-001。全鏈:
合成資料 → HedgeStrategy(篩選→對衝)+ 笨 baselines → A0 PIT 回測 → leaderboard。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _synth():
    from quantlab.data.provider import InMemoryPITDataProvider
    rng = np.random.default_rng(42)
    n = 120
    dates = pd.date_range("2010-01-31", periods=n, freq="ME")
    tsmc = 100.0 + np.cumsum(rng.normal(0, 1, n))
    plant = 150.0 - 0.5 * tsmc + rng.normal(0, 0.5, n)     # 共整合-反向(對衝標的)
    rand = 80.0 + np.cumsum(rng.normal(0, 1, n))
    rows = [{"symbol": s, "event_date": d, "available_date": d, "close": float(v)}
            for s, arr in (("TSMC", tsmc), ("PLANT", plant), ("RAND", rand))
            for d, v in zip(dates, arr)]
    prices = pd.DataFrame(rows)
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("2009-01-01"), "delist_date": pd.NaT}
                             for s in ("TSMC", "PLANT", "RAND")])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro), dates


def _cfg(dates):
    return {"start": str(dates[0].date()), "end": str(dates[-1].date()), "rebalance": "monthly",
            "fill": "same_close", "mode": "net",
            "cost_config": {"commission_bps": 5, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
                            "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
            "seed": 11, "data_version": "synth",
            "walk_forward": {"train_window_months": 36, "test_window_months": 12, "step_months": 12}}


def test_hedge_slice_leaderboard(tmp_path):
    from quantlab.runner import run_hedge_slice
    from quantlab.tracking import LocalResultStore

    data, dates = _synth()
    store = LocalResultStore(tmp_path / "s.db")
    board = run_hedge_slice(data, _cfg(dates), store,
                            target="TSMC", candidates=["PLANT", "RAND"], hedge_fraction=0.3)

    names = [r["strategy_name"] for r in board]
    assert "HedgeStrategy" in names                        # 主角在榜上
    assert len(board) == 4                                 # hedge + 3 baselines
    vals = [(-1e18 if r["oos_net_sharpe"] is None else r["oos_net_sharpe"]) for r in board]
    assert vals == sorted(vals, reverse=True)              # 依 OOS-net 排序
    for row in board:                                      # 每列可追溯
        assert store.get(row["run_id"])["strategy_name"] == row["strategy_name"]


def test_hedge_slice_reproducible(tmp_path):
    from quantlab.runner import run_hedge_slice
    from quantlab.tracking import LocalResultStore

    data, dates = _synth()
    b1 = run_hedge_slice(data, _cfg(dates), LocalResultStore(tmp_path / "a.db"),
                         target="TSMC", candidates=["PLANT", "RAND"])
    b2 = run_hedge_slice(data, _cfg(dates), LocalResultStore(tmp_path / "b.db"),
                         target="TSMC", candidates=["PLANT", "RAND"])
    # 同名策略的 OOS-net 指標一致(全鏈重現)
    m1 = {r["strategy_name"]: r["oos_net_sharpe"] for r in b1}
    m2 = {r["strategy_name"]: r["oos_net_sharpe"] for r in b2}
    assert m1 == m2
