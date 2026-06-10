"""B-5 pit_strictness(CR-B5,對 a0 backtest_config 的 overlay)— RED 階段測試。

- backtest_config 新增 pit_strictness(strict|lenient,default lenient)
- InMemoryPITDataProvider strict 排除 is_approximate=true 列
- vintage loader 寫入 is_approximate、可傳 strict
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _base_cfg(**extra):
    cfg = dict(start="2020-01-01", end="2024-01-01", rebalance="monthly", fill="next_open",
               mode="gross", seed=1, data_version="v0",
               walk_forward={"train_window_months": 36, "test_window_months": 12, "step_months": 12})
    cfg.update(extra)
    return cfg


def test_backtest_config_accepts_pit_strictness():
    from quantlab.contracts import BacktestConfig

    assert BacktestConfig(**_base_cfg()).pit_strictness == "lenient"          # 預設
    assert BacktestConfig(**_base_cfg(pit_strictness="strict")).pit_strictness == "strict"


def test_provider_strict_excludes_approximate():
    from quantlab.data.provider import InMemoryPITDataProvider
    ts = pd.Timestamp
    prices = pd.DataFrame([
        {"symbol": "A", "event_date": ts("2020-01-31"), "available_date": ts("2020-01-31"),
         "close": 10.0, "is_approximate": False},
        {"symbol": "A", "event_date": ts("2020-02-29"), "available_date": ts("2020-02-29"),
         "close": 11.0, "is_approximate": True},     # 估算可得日
    ])
    listings = pd.DataFrame([{"symbol": "A", "list_date": ts("2019-01-01"), "delist_date": pd.NaT}])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])

    lenient = InMemoryPITDataProvider(prices, listings, macro, strict=False)
    strict = InMemoryPITDataProvider(prices, listings, macro, strict=True)

    # lenient 在 3 月取最新 = 估算的 11.0;strict 排除估算 → 退回 clean 的 10.0
    assert float(lenient.get(ts("2020-03-01"), ["close"], ["A"]).loc["A", "close"]) == 11.0
    assert float(strict.get(ts("2020-03-01"), ["close"], ["A"]).loc["A", "close"]) == 10.0


def test_vintage_loader_carries_is_approximate(tmp_path):
    from quantlab.data.vintage import build_provider_from_vintage

    root = tmp_path / "raw"
    d = root / "2026-06-09"
    d.mkdir(parents=True)
    (d / "fred_SP500.json").write_text(json.dumps({
        "source": "fred:SP500", "available_date": "2026-06-09", "is_approximate": True,
        "raw": "observation_date,SP500\n2026-06-05,5800.0\n"}), encoding="utf-8")

    # strict loader 應排除 is_approximate=true 的價格 → 該資產無資料
    strict = build_provider_from_vintage(root, fred_price_series={"SP500"}, strict=True)
    assert strict.get(pd.Timestamp("2026-06-10"), ["close"], ["SP500"]).empty
    lenient = build_provider_from_vintage(root, fred_price_series={"SP500"}, strict=False)
    assert not lenient.get(pd.Timestamp("2026-06-10"), ["close"], ["SP500"]).empty
