"""InMemoryPITDataProvider — bitemporal point-in-time 資料來源(A0-1)。

每筆資料帶 event_date(所屬期)與 available_date(可得/公布日)。
所有取數一律 available_date <= asof,從根源阻擋 lookahead(REQ-A0-PIT-001/003)。
universe 由上市/下市日表計算,含已下市標的(survivorship-safe,REQ-A0-PIT-002)。

⚠️ 框架隔離:本模組不得 import torch/tensorflow/jax(NFR-A0-FWAGN-001)。
"""
from __future__ import annotations

from typing import Sequence

import pandas as pd


def _available_at(df: pd.DataFrame, asof: pd.Timestamp) -> pd.DataFrame:
    """只保留在 asof 當下實際可得的列(available_date <= asof)。as-of 取數的單一守門點。"""
    return df[df["available_date"] <= asof]


class InMemoryPITDataProvider:
    """以 in-memory DataFrame 實作 PointInTimeDataProvider Protocol。

    prices   欄位:symbol, event_date, available_date, <fields...>
    listings 欄位:symbol, list_date, delist_date(可為 NaT)
    macro    欄位:series, event_date, available_date, value
    """

    def __init__(self, prices: pd.DataFrame, listings: pd.DataFrame, macro: pd.DataFrame,
                 strict: bool = False) -> None:
        # strict(pit_strictness,CR-B5):排除 is_approximate=true 列;additive,預設不變行為
        self._prices = self._apply_strict(prices.copy(), strict)
        self._listings = listings.copy()
        self._macro = self._apply_strict(macro.copy(), strict)

    @staticmethod
    def _apply_strict(df: pd.DataFrame, strict: bool) -> pd.DataFrame:
        if strict and "is_approximate" in df.columns:
            return df[~df["is_approximate"].astype(bool)]
        return df

    def get(self, asof, fields: Sequence[str], symbols: Sequence[str] | None = None) -> pd.DataFrame:
        asof = pd.Timestamp(asof)
        cols = list(fields) + ["event_date", "available_date"]

        avail = _available_at(self._prices, asof)
        if symbols is not None:
            avail = avail[avail["symbol"].isin(list(symbols))]

        if avail.empty:
            return pd.DataFrame(columns=cols, index=pd.Index([], name="symbol"))

        # 每個 symbol 取「可得範圍內最新」:先 available_date,再 event_date 為序,取最後一筆
        latest = (avail.sort_values(["available_date", "event_date"])
                       .groupby("symbol", as_index=True)
                       .tail(1)
                       .set_index("symbol"))
        return latest[cols]

    def history(self, asof, field: str, symbols: Sequence[str]) -> pd.DataFrame:
        """PIT 歷史:index=event_date、columns=symbols 的寬表,只含 available_date<=asof
        的列;同 (symbol,event_date) 取最新可得版本(處理修訂)。REQ-A-DATA-001。"""
        asof = pd.Timestamp(asof)
        df = _available_at(self._prices, asof)
        df = df[df["symbol"].isin(list(symbols))]
        if df.empty:
            return pd.DataFrame(index=pd.Index([], name="event_date"))
        df = (df.sort_values(["available_date"])
                .groupby(["symbol", "event_date"], as_index=False).tail(1))
        return df.pivot(index="event_date", columns="symbol", values=field).sort_index()

    def universe(self, asof) -> list[str]:
        asof = pd.Timestamp(asof)
        listed = self._listings["list_date"] <= asof
        not_delisted = self._listings["delist_date"].isna() | (self._listings["delist_date"] > asof)
        alive = self._listings[listed & not_delisted]
        return sorted(alive["symbol"].tolist())

    def macro(self, asof, series: str) -> float | None:
        asof = pd.Timestamp(asof)
        rows = _available_at(self._macro, asof)
        rows = rows[rows["series"] == series]
        if rows.empty:
            return None
        # 最新所屬期(event_date),同期取最新可得版本(available_date)= 處理修訂
        rows = rows.sort_values(["event_date", "available_date"])
        return float(rows.iloc[-1]["value"])
