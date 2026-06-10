"""Vintage 載入器(REQ-B-LOAD-001/002/003)。

把 scripts/daily_snapshot.py 寫出的 vintage JSON 解析成 A0 InMemoryPITDataProvider:
- FRED(fredgraph CSV)→ macro 序列(event_date=observation、available_date=snapshot 日)
- Stooq(quote CSV)→ price 序列(event_date=報價日、available_date=snapshot 日)
多份 snapshot 各自保留 available_date,PIT 取數自然呈現修訂。

⚠️ data/ 模組:不得 import torch/tensorflow/jax(框架隔離契約)。
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pandas as pd

from quantlab.data.provider import InMemoryPITDataProvider


def _parse_fred_rows(available_date: str, raw: str) -> list[tuple]:
    """回 [(event_date, available_date, value), ...]。"""
    rows = list(csv.reader(io.StringIO(raw)))
    out = []
    for row in rows[1:]:
        if len(row) < 2 or not row[1] or row[1] == ".":
            continue
        try:
            value = float(row[1])
        except ValueError:
            continue
        out.append((pd.Timestamp(row[0]), pd.Timestamp(available_date), value))
    return out


def _parse_stooq(source: str, available_date: str, raw: str) -> list[dict]:
    rows = list(csv.reader(io.StringIO(raw)))
    if len(rows) < 2:
        return []
    idx = {h.strip(): i for i, h in enumerate(rows[0])}
    if not {"Symbol", "Date", "Close"} <= idx.keys():
        return []
    out = []
    for row in rows[1:]:
        if len(row) <= idx["Close"]:
            continue
        try:
            close = float(row[idx["Close"]])
        except ValueError:
            continue
        out.append({"symbol": row[idx["Symbol"]], "event_date": pd.Timestamp(row[idx["Date"]]),
                    "available_date": pd.Timestamp(available_date), "close": close})
    return out


def build_provider_from_vintage(vintage_root: str | Path,
                                fred_price_series: set | None = None) -> InMemoryPITDataProvider:
    """vintage JSON → A0 PIT provider。

    fred_price_series:指定哪些 FRED series 當「價格資產」載入(symbol=series、close=value),
    其餘 FRED series 仍為 macro。用以繞過 Stooq,以 FRED 的股指/黃金/油/匯率序列當價格。
    """
    price_set = set(fred_price_series or ())
    root = Path(vintage_root)
    macro_rows: list[dict] = []
    price_rows: list[dict] = []
    if root.exists():
        for jf in sorted(root.rglob("*.json")):
            rec = json.loads(jf.read_text(encoding="utf-8"))
            source = rec.get("source", "")
            available = rec.get("available_date")
            raw = rec.get("raw", "")
            if not available or not isinstance(raw, str):
                continue
            if source.startswith("fred:"):
                series = source.split(":", 1)[1]
                for event_date, avail, value in _parse_fred_rows(available, raw):
                    if series in price_set:
                        price_rows.append({"symbol": series, "event_date": event_date,
                                           "available_date": avail, "close": value})
                    else:
                        macro_rows.append({"series": series, "event_date": event_date,
                                           "available_date": avail, "value": value})
            elif source.startswith("stooq:"):
                price_rows += _parse_stooq(source, available, raw)
            # noaa / 其他:不解析

    macro = pd.DataFrame(macro_rows, columns=["series", "event_date", "available_date", "value"])
    prices = pd.DataFrame(price_rows, columns=["symbol", "event_date", "available_date", "close"])
    if price_rows:
        first = prices.groupby("symbol", as_index=False)["event_date"].min()
        listings = pd.DataFrame({"symbol": first["symbol"], "list_date": first["event_date"],
                                 "delist_date": pd.NaT})
    else:
        listings = pd.DataFrame(columns=["symbol", "list_date", "delist_date"])
    return InMemoryPITDataProvider(prices, listings, macro)
