"""對衝部位建構(REQ-A-HEDGE-001)。

把共整合-反向篩選結果轉成部位:target 核心(1 - hedge_fraction)+ hedge 候選(均分
hedge_fraction)。HedgeStrategy 相容 A0 Strategy Protocol:每個 asof 即時跑 PIT 篩選
→ 建對衝權重,可丟進 A0 回測。
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from quantlab.research.screen import screen_cointegration_hedge


def build_hedge_weights(target: str, selected: Sequence[Any],
                        hedge_fraction: float = 0.3) -> dict:
    """target 核心 + selected 候選均分 hedge_fraction;正規化到和為 1。空 selected → 全 target。"""
    f = min(1.0, max(0.0, float(hedge_fraction)))
    syms = [s["symbol"] if isinstance(s, dict) else s for s in selected]
    if not syms:
        return {target: 1.0}
    weights = {target: 1.0 - f}
    each = f / len(syms)
    for s in syms:
        weights[s] = weights.get(s, 0.0) + each
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()} if total > 0 else weights


class HedgeStrategy:
    def __init__(self, target: str, candidates: Sequence[str],
                 hedge_fraction: float = 0.3, adf_pmax: float = 0.05) -> None:
        self._target = target
        self._candidates = list(candidates)
        self._fraction = float(hedge_fraction)
        self._adf_pmax = float(adf_pmax)

    def fit(self, train: Any = None, **kwargs: Any) -> None:
        return None

    def generate_signal(self, asof: Any, data: Any) -> Mapping[str, float]:
        selected = screen_cointegration_hedge(data, asof, self._target,
                                              self._candidates, self._adf_pmax)
        return build_hedge_weights(self._target, selected, self._fraction)

    @property
    def metadata(self) -> Mapping[str, Any]:
        return {"name": "HedgeStrategy", "framework": "none",
                "target": self._target, "hedge_fraction": self._fraction}
