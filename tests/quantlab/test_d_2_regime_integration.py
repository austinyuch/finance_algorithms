"""D-2 regime model OOS-net baseline comparison."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _synth(n=72):
    from quantlab.data.provider import InMemoryPITDataProvider

    dates = pd.date_range("2017-01-31", periods=n, freq="ME")
    eq = 100 * np.cumprod(np.r_[np.full(n // 2, 1.012), np.full(n - n // 2, 0.992)])
    bond = 100 * np.cumprod(np.full(n, 1.002))
    rows = []
    for sym, values in {"SP500": eq, "BOND": bond}.items():
        rows.extend(
            {"symbol": sym, "event_date": d, "available_date": d, "close": float(v)}
            for d, v in zip(dates, values)
        )
    macro_rows = [
        {"series": "T10Y2Y", "event_date": d, "available_date": d,
         "value": 0.5 if i < n // 2 else -0.5}
        for i, d in enumerate(dates)
    ]
    prices = pd.DataFrame(rows)
    listings = pd.DataFrame(
        [{"symbol": s, "list_date": pd.Timestamp("2016-01-01"), "delist_date": pd.NaT}
         for s in ("SP500", "BOND")]
    )
    macro = pd.DataFrame(macro_rows)
    return InMemoryPITDataProvider(prices, listings, macro), dates


def _cfg(dates):
    return {
        "start": str(dates[0].date()),
        "end": str(dates[-1].date()),
        "rebalance": "monthly",
        "fill": "same_close",
        "mode": "net",
        "cost_config": {"commission_bps": 5, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
                        "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
        "seed": 0,
        "data_version": "synth-regime",
        "walk_forward": {"train_window_months": 36, "test_window_months": 12, "step_months": 12},
    }


def test_regime_allocation_strategy_in_oos_net_leaderboard(tmp_path):
    from quantlab.models import FirstRegimeClassifier, RegimeAllocationStrategy
    from quantlab.runner import run_and_log
    from quantlab.strategies import StaticWeights
    from quantlab.tracking import LocalResultStore

    data, dates = _synth()
    store = LocalResultStore(tmp_path / "d.db")
    cfg = _cfg(dates)
    regime = RegimeAllocationStrategy(
        classifier=FirstRegimeClassifier(price_symbol="SP500", lookback=12),
        risk_on_weights={"SP500": 0.8, "BOND": 0.2},
        defensive_weights={"SP500": 0.2, "BOND": 0.8},
    )
    baseline = StaticWeights({"SP500": 0.5, "BOND": 0.5})

    run_and_log(regime, data, cfg, store)
    run_and_log(baseline, data, cfg, store)

    board = store.leaderboard()
    assert {row["strategy_name"] for row in board} == {"RegimeAllocationStrategy", "StaticWeights"}
    assert all("oos_net_sharpe" in row for row in board)
    assert all(row["oos_net_sharpe"] is not None for row in board)
    assert [row["oos_net_sharpe"] for row in board] == sorted(
        [row["oos_net_sharpe"] for row in board], reverse=True
    )


def test_regime_allocation_exposes_signal_metadata():
    from quantlab.models import FirstRegimeClassifier, RegimeAllocationStrategy

    data, dates = _synth()
    strategy = RegimeAllocationStrategy(
        classifier=FirstRegimeClassifier(price_symbol="SP500", lookback=12),
        risk_on_weights={"SP500": 1.0, "BOND": 0.0},
        defensive_weights={"SP500": 0.0, "BOND": 1.0},
    )

    weights = strategy.generate_signal(dates[-1], data)
    assert weights == {"SP500": 0.0, "BOND": 1.0}
    assert strategy.metadata["last_regime"] == "defensive"
