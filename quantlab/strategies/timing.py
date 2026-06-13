"""SmaTimingStrategy — single-asset moving-average timing (PIT-safe).

Holds the asset when its most recent PIT close is above its simple moving
average, otherwise holds cash (weight 0). Framework-agnostic, stateless: reads
only ``data.history(asof, ...)`` so it cannot see beyond ``asof``. This is the
minimal strategy that *differs* from buy-and-hold on a single market index, so a
real-data OOS comparison on one index is non-degenerate.

⚠️ 不得 import torch/tensorflow/jax(經 Strategy Protocol 解耦)。
"""
from __future__ import annotations

from typing import Any, Mapping


class SmaTimingStrategy:
    def __init__(self, symbol: str, window: int = 10) -> None:
        if window < 2:
            raise ValueError("SmaTimingStrategy window must be >= 2")
        self._symbol = symbol
        self._window = window

    def fit(self, train: Any = None, **kwargs: Any) -> None:
        return None

    def generate_signal(self, asof: Any, data: Any = None) -> Mapping[str, float]:
        if data is None:
            return {self._symbol: 1.0}
        hist = data.history(asof, "close", [self._symbol])
        if self._symbol not in getattr(hist, "columns", []):
            return {self._symbol: 0.0}
        closes = hist[self._symbol].dropna()
        if len(closes) < self._window:
            return {self._symbol: 1.0}  # not enough history: default invested
        recent = closes.iloc[-self._window:]
        sma = float(recent.mean())
        last = float(closes.iloc[-1])
        return {self._symbol: 1.0 if last > sma else 0.0}

    @property
    def metadata(self) -> Mapping[str, Any]:
        return {"name": "SmaTimingStrategy", "framework": "none",
                "symbols": [self._symbol], "window": self._window,
                "claim_boundary": "no_alpha_claim"}
