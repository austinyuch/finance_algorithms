"""B-1 vintage 載入器 — RED 階段測試。

對應 b-data-platform REQ-B-LOAD-001/002/003 / AC-B-01/02。
把 daily_snapshot 寫出的 vintage JSON 解析成 A0 PIT DataProvider。測試不打網路(fixture)。
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def _write(root: Path, datedir: str, fname: str, source: str, available_date: str, raw: str):
    d = root / datedir
    d.mkdir(parents=True, exist_ok=True)
    (d / fname).write_text(json.dumps(
        {"source": source, "available_date": available_date, "is_approximate": False, "raw": raw},
        ensure_ascii=False), encoding="utf-8")


# --- AC-B-01:FRED vintage → PIT macro(含修訂) ---

def test_fred_vintage_to_pit_macro(tmp_path):
    from quantlab.data.vintage import build_provider_from_vintage

    root = tmp_path / "raw"
    # snapshot1(2026-03-01):Jan CPI 首次值 256.0
    _write(root, "2026-03-01", "fred_CPIAUCSL.json", "fred:CPIAUCSL", "2026-03-01",
           "observation_date,CPIAUCSL\n2026-01-01,256.0\n")
    # snapshot2(2026-04-01):Jan CPI 修訂值 256.4
    _write(root, "2026-04-01", "fred_CPIAUCSL.json", "fred:CPIAUCSL", "2026-04-01",
           "observation_date,CPIAUCSL\n2026-01-01,256.4\n")

    p = build_provider_from_vintage(root)
    assert p.macro(pd.Timestamp("2026-02-01"), "CPIAUCSL") is None      # snapshot 前
    assert p.macro(pd.Timestamp("2026-03-15"), "CPIAUCSL") == 256.0     # 首次值可得
    assert p.macro(pd.Timestamp("2026-04-15"), "CPIAUCSL") == 256.4     # 修訂值可得


# --- AC-B-02:Stooq vintage → PIT price ---

def test_stooq_vintage_to_pit_price(tmp_path):
    from quantlab.data.vintage import build_provider_from_vintage

    root = tmp_path / "raw"
    _write(root, "2026-06-09", "stooq_spy.us.json", "stooq:spy.us", "2026-06-09",
           "Symbol,Date,Time,Open,High,Low,Close,Volume\nSPY.US,2026-06-06,22:00:00,1,2,0.5,1.5,1000\n")

    p = build_provider_from_vintage(root)
    df = p.get(pd.Timestamp("2026-06-10"), ["close"], ["SPY.US"])
    assert float(df.loc["SPY.US", "close"]) == 1.5
    assert df.loc["SPY.US", "available_date"] == pd.Timestamp("2026-06-09")   # PIT
    # snapshot 前查不到
    assert p.get(pd.Timestamp("2026-06-08"), ["close"], ["SPY.US"]).empty


def test_empty_vintage_dir(tmp_path):
    from quantlab.data.vintage import build_provider_from_vintage

    p = build_provider_from_vintage(tmp_path / "raw")          # 不存在/空 → 不崩
    assert p.macro(pd.Timestamp("2026-01-01"), "X") is None
    assert p.universe(pd.Timestamp("2026-01-01")) == []
