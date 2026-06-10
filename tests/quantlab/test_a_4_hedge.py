"""A-4 對衝部位建構 — RED 階段測試。

對應 a-tsmc-hedge-slice REQ-A-HEDGE-001。
把篩出的共整合-反向候選轉成對衝部位:target 核心 + hedge 候選(hedge_fraction),
並驗證對衝在反向資料上**確實降低波動**(showcase)。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


# --- build_hedge_weights 配置性質 ---

def test_build_hedge_weights_allocation():
    from quantlab.strategies.hedge import build_hedge_weights

    w = build_hedge_weights("TSMC", [{"symbol": "A"}, {"symbol": "B"}], hedge_fraction=0.3)
    assert sum(w.values()) == pytest.approx(1.0)
    assert w["TSMC"] == pytest.approx(0.7)             # target = 1 - hedge_fraction
    assert w["A"] == pytest.approx(0.15)               # 候選均分 hedge_fraction
    assert w["B"] == pytest.approx(0.15)


def test_build_hedge_weights_edges():
    from quantlab.strategies.hedge import build_hedge_weights

    assert build_hedge_weights("T", [], hedge_fraction=0.3) == pytest.approx({"T": 1.0})  # 無 hedge → 全 target
    allhedge = build_hedge_weights("T", [{"symbol": "A"}], hedge_fraction=1.0)
    assert allhedge["A"] == pytest.approx(1.0)         # hedge_fraction=1 → 全 hedge


# --- HedgeStrategy 串接篩選、相容 Protocol ---

def _synth():
    from quantlab.data.provider import InMemoryPITDataProvider
    rng = np.random.default_rng(42)
    n = 120
    dates = pd.date_range("2010-01-31", periods=n, freq="ME")
    tsmc = 100.0 + np.cumsum(rng.normal(0, 1, n))
    plant = 50.0 - 0.5 * tsmc + rng.normal(0, 0.5, n)
    rand = 80.0 + np.cumsum(rng.normal(0, 1, n))
    rows = [{"symbol": s, "event_date": d, "available_date": d, "close": float(v)}
            for s, arr in (("TSMC", tsmc), ("PLANT", plant), ("RAND", rand))
            for d, v in zip(dates, arr)]
    prices = pd.DataFrame(rows)
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("2009-01-01"), "delist_date": pd.NaT}
                             for s in ("TSMC", "PLANT", "RAND")])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro), dates


def test_hedge_strategy_conforms_and_screens():
    from quantlab.contracts import Strategy
    from quantlab.strategies.hedge import HedgeStrategy

    data, dates = _synth()
    h = HedgeStrategy("TSMC", ["PLANT", "RAND"], hedge_fraction=0.3, adf_pmax=0.05)
    assert isinstance(h, Strategy)
    w = h.generate_signal(dates[-1], data)
    assert w["TSMC"] == pytest.approx(0.7)             # 核心
    assert "PLANT" in w and w["PLANT"] > 0             # 共整合-反向候選入對衝
    assert "RAND" not in w                             # 隨機不入
    assert sum(w.values()) == pytest.approx(1.0)


# --- showcase:對衝在反向資料上降低波動 ---

def test_hedge_reduces_vol_vs_pure_target():
    from quantlab.strategies.hedge import build_hedge_weights

    rng = np.random.default_rng(0)
    n = 200
    tsmc_ret = rng.normal(0, 0.05, n)
    anti_ret = -tsmc_ret + rng.normal(0, 0.01, n)      # 強反向
    w = build_hedge_weights("TSMC", [{"symbol": "ANTI"}], hedge_fraction=0.4)
    port_ret = w["TSMC"] * tsmc_ret + w["ANTI"] * anti_ret
    assert port_ret.std() < tsmc_ret.std()             # 對衝確實降波動
