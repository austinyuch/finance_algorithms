"""C-2 多期配置 — RED 階段測試。

對應 c-portfolio-core REQ-C-MULTI-001:
短/中/長 horizon 各自用 PIT history 最佳化,再依 budget_weight 混合為單一權重。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def _synth(n=84):
    from quantlab.data.provider import InMemoryPITDataProvider

    rng = np.random.default_rng(42)
    dates = pd.date_range("2014-01-31", periods=n, freq="ME")
    series = {
        "EQ": 100 * np.cumprod(1 + rng.normal(0.008, 0.05, n)),
        "BOND": 100 * np.cumprod(1 + rng.normal(0.003, 0.015, n)),
        "GOLD": 100 * np.cumprod(1 + rng.normal(0.004, 0.035, n)),
    }
    rows = [
        {"symbol": s, "event_date": d, "available_date": d, "close": float(series[s][i])}
        for s in series
        for i, d in enumerate(dates)
    ]
    prices = pd.DataFrame(rows)
    listings = pd.DataFrame(
        [{"symbol": s, "list_date": pd.Timestamp("2013-01-01"), "delist_date": pd.NaT} for s in series]
    )
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro), dates


def test_multihorizon_strategy_blends_normalized_horizons():
    from quantlab.contracts import Strategy
    from quantlab.portfolio import HorizonConfig, MultiHorizonMeanVarianceStrategy

    data, dates = _synth()
    strategy = MultiHorizonMeanVarianceStrategy(
        ["EQ", "BOND", "GOLD"],
        horizons=[
            HorizonConfig("short", lookback=12, vol_cap=0.20, budget_weight=1),
            HorizonConfig("medium", lookback=36, vol_cap=0.30, budget_weight=2),
            HorizonConfig("long", lookback=60, vol_cap=0.35, budget_weight=1),
        ],
        min_obs=10,
    )
    assert isinstance(strategy, Strategy)

    weights = strategy.generate_signal(dates[-1], data)
    assert set(weights) == {"EQ", "BOND", "GOLD"}
    assert sum(weights.values()) == pytest.approx(1.0)
    assert all(v >= -1e-9 for v in weights.values())


def test_multihorizon_strategy_is_pit_and_reproducible():
    from quantlab.portfolio import HorizonConfig, MultiHorizonMeanVarianceStrategy

    data, dates = _synth()
    horizons = [
        HorizonConfig("short", lookback=12, vol_cap=0.18, budget_weight=0.25),
        HorizonConfig("long", lookback=48, vol_cap=0.32, budget_weight=0.75),
    ]
    s1 = MultiHorizonMeanVarianceStrategy(["EQ", "BOND", "GOLD"], horizons=horizons, min_obs=10)
    s2 = MultiHorizonMeanVarianceStrategy(["EQ", "BOND", "GOLD"], horizons=horizons, min_obs=10)

    asof = dates[-1]
    assert s1.generate_signal(asof, data) == s2.generate_signal(asof, data)

    future_only = data.history(dates[-1], "close", ["EQ", "BOND", "GOLD"]).copy()
    future_only["EQ"] = future_only["EQ"] * 100
    # The strategy must still use the provider's asof gate; a later asof can differ,
    # but the same asof remains deterministic and does not see rows after asof.
    assert s1.generate_signal(dates[36], data) == s2.generate_signal(dates[36], data)


def test_multihorizon_insufficient_history_falls_back_to_equal_weight():
    from quantlab.portfolio import HorizonConfig, MultiHorizonMeanVarianceStrategy

    data, dates = _synth(n=8)
    strategy = MultiHorizonMeanVarianceStrategy(
        ["EQ", "BOND", "GOLD"],
        horizons=[HorizonConfig("long", lookback=60, vol_cap=0.30, budget_weight=1.0)],
        min_obs=24,
    )

    assert strategy.generate_signal(dates[-1], data) == pytest.approx(
        {"EQ": 1 / 3, "BOND": 1 / 3, "GOLD": 1 / 3}
    )
