"""BuyAndHold — dummy 等權買進持有策略(A0-0 參考實作)。

框架無感、無 ML、無狀態。作為回測 harness 的最笨 baseline 與介面相容性參考。
實作 quantlab.contracts.Strategy Protocol。
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence


class BuyAndHold:
    def __init__(self, symbols: Sequence[str]) -> None:
        self._symbols = list(symbols)

    def fit(self, train: Any = None, **kwargs: Any) -> None:
        """無狀態策略:no-op。"""
        return None

    def generate_signal(self, asof: Any, data: Any = None) -> Mapping[str, float]:
        """等權配置:每個標的 1/N。"""
        n = len(self._symbols)
        weight = 1.0 / n if n else 0.0
        return {sym: weight for sym in self._symbols}

    @property
    def metadata(self) -> Mapping[str, Any]:
        return {"name": "BuyAndHold", "framework": "none", "symbols": list(self._symbols)}
