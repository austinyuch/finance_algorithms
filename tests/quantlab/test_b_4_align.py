"""B-4 as-of 頻率對齊 — RED 階段測試。

對應 b-data-platform REQ-B-ALIGN-001(對齊部分)。
把日頻價格 + 月頻總經以 as-of forward-fill 對齊成 panel,全程 PIT(每列只用 available<=date)。
"""
from __future__ import annotations

import math

import pandas as pd


def _provider():
    from quantlab.data.provider import InMemoryPITDataProvider
    ts = pd.Timestamp
    prices = pd.DataFrame([
        {"symbol": "X", "event_date": ts("2020-01-02"), "available_date": ts("2020-01-02"), "close": 10.0},
        {"symbol": "X", "event_date": ts("2020-01-03"), "available_date": ts("2020-01-03"), "close": 11.0},
        {"symbol": "X", "event_date": ts("2020-01-06"), "available_date": ts("2020-01-06"), "close": 12.0},
    ])
    listings = pd.DataFrame([{"symbol": "X", "list_date": ts("2019-01-01"), "delist_date": pd.NaT}])
    macro = pd.DataFrame([
        # Jan CPI:所屬 2020-01-01,釋出 2020-01-05(lag)
        {"series": "CPI", "event_date": ts("2020-01-01"), "available_date": ts("2020-01-05"), "value": 256.0},
    ])
    return InMemoryPITDataProvider(prices, listings, macro)


def test_align_asof_forward_fill_and_pit():
    from quantlab.research.align import align_asof

    dates = [pd.Timestamp("2020-01-02"), pd.Timestamp("2020-01-03"), pd.Timestamp("2020-01-06")]
    panel = align_asof(_provider(), dates, price_symbols=["X"], macro_series=["CPI"])

    assert list(panel.index) == dates
    assert list(panel["X"]) == [10.0, 11.0, 12.0]            # 價格每日對齊
    assert math.isnan(panel.loc[dates[0], "CPI"])           # CPI 釋出前 → NaN(PIT)
    assert math.isnan(panel.loc[dates[1], "CPI"])
    assert panel.loc[dates[2], "CPI"] == 256.0              # 釋出後 → forward-fill 可得值


def test_align_asof_price_only():
    from quantlab.research.align import align_asof

    panel = align_asof(_provider(), [pd.Timestamp("2020-01-03")], price_symbols=["X"])
    assert panel.loc[pd.Timestamp("2020-01-03"), "X"] == 11.0
    assert "CPI" not in panel.columns
