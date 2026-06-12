#!/usr/bin/env python3
"""反台積電對衝 thin slice 的可重現執行器(產生 A-6 writeup 的數字)。

⚠️ 資料為合成(strategy C:數字明知假、僅驗證管線),非真實 alpha。
跑:HedgeStrategy(共整合-反向對衝)+ optional LSTMStrategy(PyTorch 擇時)+ 笨 baselines
→ A0 PIT 回測 → leaderboard(依 OOS-net Sharpe)。

用法:uv run python scripts/run_tsmc_hedge_slice.py
"""
from __future__ import annotations

import sys
import tempfile
import importlib
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from quantlab.data.provider import InMemoryPITDataProvider
from quantlab.runner import run_and_log, run_hedge_slice
from quantlab.tracking import LocalResultStore


def load_lstm_strategy() -> type[Any] | None:
    try:
        return importlib.import_module("quantlab.strategies.lstm").LSTMStrategy
    except ModuleNotFoundError as exc:
        if exc.name == "torch":
            return None
        raise


def synth():
    rng = np.random.default_rng(42)
    n = 120
    dates = pd.date_range("2010-01-31", periods=n, freq="ME")
    tsmc = 100.0 + np.cumsum(rng.normal(0.2, 1.0, n))
    plant = 150.0 - 0.5 * tsmc + rng.normal(0, 0.5, n)      # 共整合-反向
    rand = 80.0 + np.cumsum(rng.normal(0, 1, n))
    rows = [{"symbol": s, "event_date": d, "available_date": d, "close": float(v)}
            for s, arr in (("TSMC", tsmc), ("PLANT", plant), ("RAND", rand))
            for d, v in zip(dates, arr)]
    prices = pd.DataFrame(rows)
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("2009-01-01"), "delist_date": pd.NaT}
                             for s in ("TSMC", "PLANT", "RAND")])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro), dates


def main() -> int:
    data, dates = synth()
    cfg = {"start": str(dates[0].date()), "end": str(dates[-1].date()), "rebalance": "monthly",
           "fill": "same_close", "mode": "net",
           "cost_config": {"commission_bps": 5, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
                           "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
           "seed": 0, "data_version": "synth-v1",
           "walk_forward": {"train_window_months": 36, "test_window_months": 12, "step_months": 12}}

    store = LocalResultStore(Path(tempfile.mkdtemp()) / "slice.db")
    run_hedge_slice(data, cfg, store, target="TSMC", candidates=["PLANT", "RAND"], hedge_fraction=0.3)
    lstm_strategy = load_lstm_strategy()
    if lstm_strategy is None:
        print("[optional] LSTMStrategy skipped: PyTorch lane not installed; see quantlab/envs/pytorch.txt",
              file=sys.stderr)
    else:
        run_and_log(lstm_strategy("TSMC", seed=0), data, cfg, store)

    print(f"{'strategy':<16}{'OOS net Sharpe':>16}")
    print("-" * 32)
    for r in store.leaderboard():
        s = r["oos_net_sharpe"]
        print(f"{r['strategy_name']:<16}{('n/a' if s is None else f'{s:.4f}'):>16}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
