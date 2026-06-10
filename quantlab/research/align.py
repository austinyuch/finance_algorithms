"""As-of 頻率對齊(REQ-B-ALIGN-001)。

把不同頻率的序列(日頻價格、月/季頻總經)以 point-in-time as-of forward-fill 對齊成 panel:
每個 date 只取 available_date<=date 的最新值,缺則 NaN。供特徵工程使用。
"""
from __future__ import annotations

from typing import Any, Sequence

import pandas as pd


def align_asof(provider: Any, dates: Sequence, price_symbols: Sequence[str] = (),
               macro_series: Sequence[str] = ()) -> pd.DataFrame:
    index = [pd.Timestamp(d) for d in dates]
    rows = []
    for d in index:
        row: dict = {}
        if price_symbols:
            df = provider.get(d, ["close"], list(price_symbols))
            for sym in price_symbols:
                row[sym] = float(df.loc[sym, "close"]) if sym in df.index else float("nan")
        for series in macro_series:
            value = provider.macro(d, series)
            row[series] = float("nan") if value is None else float(value)
        rows.append(row)
    return pd.DataFrame(rows, index=pd.Index(index, name="date"))
