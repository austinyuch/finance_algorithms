"""First deterministic regime signal model(REQ-D-REGIME-001 / REQ-D-HOOK-001).

This module is intentionally framework-light. It reads only through the PIT provider
surface and returns stable labels for downstream portfolio experiments.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd


@dataclass(frozen=True)
class RegimeSignal:
    label: str
    confidence: float
    feature_status: Mapping[str, str]


class RegimeFeatureBuilder:
    def __init__(self, price_symbol: str = "SP500", curve_series: str = "T10Y2Y",
                 lookback: int = 12) -> None:
        self._price_symbol = price_symbol
        self._curve_series = curve_series
        self._lookback = int(lookback)

    def build(self, asof: Any, data: Any) -> tuple[dict[str, float], dict[str, str]]:
        features: dict[str, float] = {}
        status: dict[str, str] = {}

        price_trend = self._price_trend(asof, data)
        if price_trend is None:
            status["price_trend"] = "missing"
        else:
            features["price_trend"] = price_trend
            status["price_trend"] = "available"

        curve = data.macro(pd.Timestamp(asof), self._curve_series)
        if curve is None:
            status["yield_curve"] = "missing"
        else:
            features["yield_curve"] = float(curve)
            status["yield_curve"] = "available"

        return features, status

    def _price_trend(self, asof: Any, data: Any) -> float | None:
        hist = data.history(pd.Timestamp(asof), "close", [self._price_symbol]).dropna()
        if self._price_symbol not in hist.columns or hist.shape[0] < self._lookback + 1:
            return None
        window = hist[self._price_symbol].tail(self._lookback + 1)
        first = float(window.iloc[0])
        last = float(window.iloc[-1])
        if first <= 0:
            return None
        return last / first - 1.0


class FirstRegimeClassifier:
    LABELS = ("risk_on", "defensive", "unknown")

    def __init__(self, price_symbol: str = "SP500", curve_series: str = "T10Y2Y",
                 lookback: int = 12, trend_threshold: float = 0.0) -> None:
        self._builder = RegimeFeatureBuilder(price_symbol, curve_series, lookback)
        self._trend_threshold = float(trend_threshold)

    def predict(self, asof: Any, data: Any) -> RegimeSignal:
        features, status = self._builder.build(asof, data)
        trend = features.get("price_trend")
        curve = features.get("yield_curve")

        if trend is None and curve is None:
            return RegimeSignal("unknown", 0.0, status)
        if curve is not None and curve < 0:
            return RegimeSignal("defensive", 0.75, status)
        if trend is not None and trend < self._trend_threshold:
            return RegimeSignal("defensive", 0.65, status)
        return RegimeSignal("risk_on", 0.60, status)


class RegimeAllocationStrategy:
    """A0-compatible strategy adapter for first regime model leaderboard tests."""

    def __init__(self, classifier: FirstRegimeClassifier,
                 risk_on_weights: Mapping[str, float],
                 defensive_weights: Mapping[str, float],
                 unknown_weights: Mapping[str, float] | None = None) -> None:
        self._classifier = classifier
        self._risk_on = self._normalize(risk_on_weights)
        self._defensive = self._normalize(defensive_weights)
        self._unknown = self._normalize(unknown_weights or self._risk_on)
        self._last_signal = RegimeSignal("unknown", 0.0, {})

    def fit(self, train: Any = None, **kwargs: Any) -> None:
        return None

    def generate_signal(self, asof: Any, data: Any) -> Mapping[str, float]:
        self._last_signal = self._classifier.predict(asof, data)
        if self._last_signal.label == "risk_on":
            return dict(self._risk_on)
        if self._last_signal.label == "defensive":
            return dict(self._defensive)
        return dict(self._unknown)

    @property
    def metadata(self) -> Mapping[str, Any]:
        return {
            "name": "RegimeAllocationStrategy",
            "framework": "none",
            "last_regime": self._last_signal.label,
            "last_regime_confidence": self._last_signal.confidence,
        }

    @staticmethod
    def _normalize(weights: Mapping[str, float]) -> dict[str, float]:
        clipped = {str(k): max(float(v), 0.0) for k, v in weights.items()}
        total = sum(clipped.values())
        if total <= 0:
            n = len(clipped)
            return {k: 1.0 / n for k in clipped}
        return {k: v / total for k, v in clipped.items()}
