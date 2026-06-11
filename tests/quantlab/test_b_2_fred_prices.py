"""B-2 FRED 價格代理 → 真實價格資產 — RED 階段測試。

對應 b-data-platform。解除 Stooq 404 阻塞:FRED(沙箱可用)有股指/商品/油/匯率序列,
把指定的 FRED series 當成 price 資產載入,讓真實價格能進 backtest。測試不打網路。
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path

import pandas as pd


def _write(root: Path, datedir: str, fname: str, source: str, available_date: str, raw: str):
    d = root / datedir
    d.mkdir(parents=True, exist_ok=True)
    (d / fname).write_text(json.dumps(
        {"source": source, "available_date": available_date, "is_approximate": False, "raw": raw},
        ensure_ascii=False), encoding="utf-8")


def test_fred_price_series_loaded_as_price_asset(tmp_path):
    from quantlab.data.vintage import build_provider_from_vintage

    root = tmp_path / "raw"
    _write(root, "2026-06-09", "fred_SP500.json", "fred:SP500", "2026-06-09",
           "observation_date,SP500\n2026-06-05,5800.0\n2026-06-06,5850.0\n")

    p = build_provider_from_vintage(root, fred_price_series={"SP500"})
    df = p.get(pd.Timestamp("2026-06-10"), ["close"], ["SP500"])
    assert float(df.loc["SP500", "close"]) == 5850.0                  # 最新 observation 當價格
    assert df.loc["SP500", "available_date"] == pd.Timestamp("2026-06-09")
    assert "SP500" in p.universe(pd.Timestamp("2026-06-10"))          # 成為可投資資產


def test_fred_default_stays_macro(tmp_path):
    from quantlab.data.vintage import build_provider_from_vintage

    root = tmp_path / "raw"
    _write(root, "2026-06-09", "fred_CPIAUCSL.json", "fred:CPIAUCSL", "2026-06-09",
           "observation_date,CPIAUCSL\n2026-04-01,332.4\n")

    p = build_provider_from_vintage(root)                             # 無 fred_price_series
    assert p.macro(pd.Timestamp("2026-06-10"), "CPIAUCSL") == 332.4   # 仍是 macro
    assert p.get(pd.Timestamp("2026-06-10"), ["close"], ["CPIAUCSL"]).empty  # 不是價格資產


def test_snapshot_captures_fred_price_proxies():
    """每日 snapshot 應捕捉 FRED 價格代理(繞過 Stooq 404),routine 才會累積真實價格。"""
    spec = importlib.util.spec_from_file_location(
        "daily_snapshot", Path(__file__).resolve().parents[2] / "scripts" / "daily_snapshot.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    series = set(mod.FRED_SERIES)
    # 至少含:美股指數、商品、油、台幣匯率(FRED 在沙箱可用)
    assert {"SP500", "PCOPPUSDM", "DCOILWTICO", "DEXTAUS"} <= series
    assert "GOLDAMGBD228NLBM" not in series
    assert "GOLDPMGBD228NLBM" not in series
