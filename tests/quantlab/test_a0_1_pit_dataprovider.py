"""A0-1 Point-in-Time DataProvider — RED 階段測試。

對應 tasks.md A0-1 / REQ-A0-PIT-001/002/003/004 / AC-A0-01 / AC-A0-02 / PBT-2 / FMEA-A0-01/02。
這些測試在 quantlab.data 的 bitemporal provider 建立前**應失敗**(RED)。

toy fixture(build_toy_dataset)約定:
  prices:
    AAA  event 2020-01-31 avail 2020-01-31 close 100;event 2020-02-29 avail 2020-02-29 close 110
    BBB  event 2020-01-31 avail 2020-01-31 close  50;event 2020-02-29 avail 2020-02-29 close  55
  universe(上市/下市):
    AAA list 2019-01-01 delist None;  BBB list 2019-01-01 delist 2020-03-15(中途下市)
  macro "CPI"(釋出 lag + 修訂):
    Jan(event 2020-01-01)首次 avail 2020-02-12 = 256.0;修訂 avail 2020-03-11 = 256.4
    Feb(event 2020-02-01)avail 2020-03-12 = 257.0
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st


def _provider():
    from quantlab.data import InMemoryPITDataProvider  # noqa: F401
    from quantlab.data.fixtures import build_toy_dataset

    p = build_toy_dataset()
    assert isinstance(p, InMemoryPITDataProvider)
    return p


# --- AC-A0-01 / REQ-A0-PIT-001:get() 擋 lookahead ---

def test_get_blocks_unavailable_future_data():
    p = _provider()
    # 2020-01-15:AAA 的 1/31 收盤(avail 1/31)當下還不可得 → 應為空
    early = p.get(pd.Timestamp("2020-01-15"), ["close"], symbols=["AAA"])
    assert early.empty

    # 2020-02-01:1/31 收盤已可得 → close=100
    feb = p.get(pd.Timestamp("2020-02-01"), ["close"], symbols=["AAA"])
    assert float(feb.loc["AAA", "close"]) == 100.0
    assert feb.loc["AAA", "available_date"] <= pd.Timestamp("2020-02-01")

    # 2020-03-01:取最新可得 = 2/29 收盤 110
    mar = p.get(pd.Timestamp("2020-03-01"), ["close"], symbols=["AAA"])
    assert float(mar.loc["AAA", "close"]) == 110.0


@given(asof=st.dates(min_value=dt.date(2019, 1, 1), max_value=dt.date(2021, 1, 1)))
def test_pbt2_no_row_after_asof(asof):
    # PBT-2:任意 asof,get() 回傳的每一列 available_date 都 <= asof(永不洩漏未來)
    p = _provider()
    ts = pd.Timestamp(asof)
    df = p.get(ts, ["close"])
    assert (df["available_date"] <= ts).all()


# --- AC-A0-02 / REQ-A0-PIT-002:survivorship-safe universe ---

def test_universe_includes_delisted_while_alive_excludes_after():
    p = _provider()
    assert set(p.universe(pd.Timestamp("2020-02-01"))) == {"AAA", "BBB"}      # BBB 尚存
    assert set(p.universe(pd.Timestamp("2020-03-20"))) == {"AAA"}             # BBB 已下市
    assert set(p.universe(pd.Timestamp("2018-01-01"))) == set()              # 皆未上市


# --- REQ-A0-PIT-003:macro 釋出 lag + 修訂 ---

def test_macro_release_lag_and_revision():
    p = _provider()
    assert p.macro(pd.Timestamp("2020-01-15"), "CPI") is None        # 尚未釋出
    assert p.macro(pd.Timestamp("2020-02-20"), "CPI") == 256.0       # Jan 首次釋出
    assert p.macro(pd.Timestamp("2020-03-11"), "CPI") == 256.4       # Jan 修訂可見
    assert p.macro(pd.Timestamp("2020-03-12"), "CPI") == 257.0       # Feb 成為最新
