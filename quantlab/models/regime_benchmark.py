"""Real-data-shaped regime benchmark helpers for D-3.

The helpers consume an A0 PIT provider, typically built from vintage source payloads,
and produce an OOS-net leaderboard against a static baseline. The report is an
evidence artifact, not an alpha claim.
"""
from __future__ import annotations

from typing import Any, Sequence

import pandas as pd

from quantlab.models.regime import FirstRegimeClassifier, RegimeAllocationStrategy
from quantlab.runner import run_and_log
from quantlab.strategies import StaticWeights


def benchmark_price_dates(data: Any, symbols: Sequence[str], asof: Any) -> list[pd.Timestamp]:
    hist = data.history(pd.Timestamp(asof), "close", list(symbols)).dropna()
    if hist.empty:
        return []
    return [pd.Timestamp(d) for d in hist.index]


def _config(dates: Sequence[pd.Timestamp], labels: dict[str, str]) -> dict:
    return {
        "start": str(dates[0].date()),
        "end": str(dates[-1].date()),
        "rebalance": "monthly",
        "fill": "same_close",
        "mode": "net",
        "cost_config": {"commission_bps": 5, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
                        "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
        "seed": 0,
        "data_version": "vintage-loader-real-source-format",
        "walk_forward": {"train_window_months": 6, "test_window_months": 6, "step_months": 6},
        "rebalance_policy": {"kind": "regime", "frequency": "quarterly", "labels": labels},
    }


def run_real_data_regime_benchmark(
    data: Any,
    dates: Sequence[pd.Timestamp],
    store: Any,
    *,
    risk_symbol: str = "SP500",
    defensive_symbol: str = "PCOPPUSDM",
    lookback: int = 6,
) -> dict:
    ordered = [pd.Timestamp(d) for d in dates]
    if len(ordered) < 12:
        raise ValueError("real-data regime benchmark requires at least 12 price dates")

    classifier = FirstRegimeClassifier(price_symbol=risk_symbol, lookback=lookback)
    labels = {str(d.date()): classifier.predict(d, data).label for d in ordered}
    cfg = _config(ordered, labels)

    regime = RegimeAllocationStrategy(
        classifier=classifier,
        risk_on_weights={risk_symbol: 0.8, defensive_symbol: 0.2},
        defensive_weights={risk_symbol: 0.3, defensive_symbol: 0.7},
        unknown_weights={risk_symbol: 0.5, defensive_symbol: 0.5},
    )
    baseline = StaticWeights({risk_symbol: 0.5, defensive_symbol: 0.5})

    regime_run_id, regime_result = run_and_log(regime, data, cfg, store)
    baseline_run_id, _ = run_and_log(baseline, data, cfg, store)
    return {
        "claim_boundary": "no_alpha_claim",
        "data_version": cfg["data_version"],
        "regime_run_id": regime_run_id,
        "baseline_run_id": baseline_run_id,
        "regime_rebalance_dates": regime_result["rebalance_dates"],
        "leaderboard": store.leaderboard(),
    }
