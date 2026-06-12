"""A-2 LSTM 訊號模型(PyTorch)— RED 階段測試。

對應 a-tsmc-hedge-slice REQ-A-LSTM-001。LSTMStrategy 相容 A0 Strategy Protocol、
PIT 懶訓練、給定 seed 可重現,並能與笨 baseline 並排進 leaderboard。
⚠️ torch 只存在於 strategies/lstm(策略層),不污染 engine/data。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("torch", reason="PyTorch strategy lane is optional outside the default UAT/runtime env")


def _synth_target(n=120, seed=1):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2010-01-31", periods=n, freq="ME")
    tsmc = 100.0 + np.cumsum(rng.normal(0.2, 1.0, n))   # 正值、帶輕微漂移
    return dates, tsmc


def _provider(dates, tsmc):
    from quantlab.data.provider import InMemoryPITDataProvider
    prices = pd.DataFrame([{"symbol": "TSMC", "event_date": d, "available_date": d, "close": float(v)}
                           for d, v in zip(dates, tsmc)])
    listings = pd.DataFrame([{"symbol": "TSMC", "list_date": pd.Timestamp("2009-01-01"), "delist_date": pd.NaT}])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro)


def test_lstm_conforms_to_protocol():
    from quantlab.contracts import Strategy
    from quantlab.strategies.lstm import LSTMStrategy

    assert isinstance(LSTMStrategy("TSMC", seed=0), Strategy)


def test_lstm_reproducible_given_seed():
    from quantlab.strategies.lstm import LSTMStrategy

    dates, tsmc = _synth_target()
    data = _provider(dates, tsmc)
    a = LSTMStrategy("TSMC", seed=7).generate_signal(dates[-1], data)
    b = LSTMStrategy("TSMC", seed=7).generate_signal(dates[-1], data)
    assert a == b                                        # 同 seed → 同訊號(可重現)


def test_lstm_insufficient_history_defaults_to_hold():
    from quantlab.strategies.lstm import LSTMStrategy

    dates, tsmc = _synth_target(n=120)
    data = _provider(dates, tsmc)
    w = LSTMStrategy("TSMC", seed=0).generate_signal(dates[5], data)   # 早期資料不足
    assert w == {"TSMC": 1.0}                            # 預設持有


def test_lstm_in_leaderboard(tmp_path):
    from quantlab.runner import run_and_log
    from quantlab.strategies import BuyAndHold
    from quantlab.strategies.lstm import LSTMStrategy
    from quantlab.tracking import LocalResultStore

    dates, tsmc = _synth_target()
    data = _provider(dates, tsmc)
    store = LocalResultStore(tmp_path / "s.db")
    cfg = {"start": str(dates[0].date()), "end": str(dates[-1].date()), "rebalance": "monthly",
           "fill": "same_close", "mode": "net",
           "cost_config": {"commission_bps": 5, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
                           "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
           "seed": 0, "data_version": "synth",
           "walk_forward": {"train_window_months": 36, "test_window_months": 12, "step_months": 12}}
    run_and_log(LSTMStrategy("TSMC", seed=0), data, cfg, store)
    run_and_log(BuyAndHold(["TSMC"]), data, cfg, store)

    board = store.leaderboard()
    names = [r["strategy_name"] for r in board]
    assert "LSTMStrategy" in names                       # LSTM 進榜
    assert len(board) == 2
    for row in board:
        assert store.get(row["run_id"])["strategy_name"] == row["strategy_name"]
