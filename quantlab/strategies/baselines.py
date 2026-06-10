"""笨 baseline 策略群(REQ-A-BASE-001)。

花俏模型(LSTM 等)必須在 A0 回測上打敗這些 baseline 才算「學到東西」(A0 DoD)。
皆相容 quantlab.contracts.Strategy Protocol、框架無感、無 ML。
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


class StaticWeights:
    """固定權重(正規化到和為 1)。"""

    def __init__(self, weights: Mapping[str, float]) -> None:
        total = sum(max(0.0, float(w)) for w in weights.values())
        self._w = {s: (max(0.0, float(w)) / total if total > 0 else 0.0)
                   for s, w in weights.items()}

    def fit(self, train: Any = None, **kwargs: Any) -> None:
        return None

    def generate_signal(self, asof: Any, data: Any = None) -> Mapping[str, float]:
        return dict(self._w)

    @property
    def metadata(self) -> Mapping[str, Any]:
        return {"name": "StaticWeights", "framework": "none", "weights": dict(self._w)}


class RandomStrategy:
    """隨機權重 baseline。給定 seed,對每個 asof 產生確定性的隨機權重(可重現)。"""

    def __init__(self, symbols: Sequence[str], seed: int = 0) -> None:
        self._symbols = list(symbols)
        self._seed = int(seed)

    def fit(self, train: Any = None, **kwargs: Any) -> None:
        return None

    def generate_signal(self, asof: Any, data: Any = None) -> Mapping[str, float]:
        # 以 (seed, asof) 為種子 → 同 seed 同 asof 必得相同權重(可重現)
        rng = np.random.default_rng([self._seed, int(pd.Timestamp(asof).value)])
        raw = rng.random(len(self._symbols))
        total = float(raw.sum())
        weights = raw / total if total > 0 else raw
        return {sym: float(w) for sym, w in zip(self._symbols, weights)}

    @property
    def metadata(self) -> Mapping[str, Any]:
        return {"name": "RandomStrategy", "framework": "none", "seed": self._seed}
