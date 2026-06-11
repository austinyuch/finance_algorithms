"""MeanVarianceStrategy(REQ-C-STRAT-001)。

相容 A0 Strategy Protocol。每 asof 由 PIT 歷史估 μ(年化平均)/Σ(年化共變異)→
最大化報酬 s.t. 年化波動 ≤ vol_cap。歷史不足 → 等權。純 numpy/scipy → 可重現。
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from quantlab.portfolio.optimize import optimize_max_return_under_vol


class MeanVarianceStrategy:
    def __init__(self, symbols: Sequence[str], vol_cap: float = 0.30,
                 lookback: int = 36, min_obs: int = 24, periods_per_year: int = 12) -> None:
        self._symbols = list(symbols)
        self._vol_cap = float(vol_cap)
        self._lookback = int(lookback)
        self._min_obs = int(min_obs)
        self._ppy = int(periods_per_year)

    def fit(self, train: Any = None, **kwargs: Any) -> None:
        return None

    def _equal(self) -> dict:
        n = len(self._symbols)
        return {s: 1.0 / n for s in self._symbols}

    def generate_signal(self, asof: Any, data: Any) -> Mapping[str, float]:
        hist = data.history(asof, "close", self._symbols).dropna()
        if hist.shape[0] < self._min_obs + 1:
            return self._equal()
        rets = hist[self._symbols].pct_change().dropna().tail(self._lookback)
        if rets.shape[0] < self._min_obs:
            return self._equal()
        mu = rets.mean().to_numpy() * self._ppy
        cov = rets.cov().to_numpy() * self._ppy
        weights = optimize_max_return_under_vol(mu, cov, self._vol_cap)
        return {sym: float(w) for sym, w in zip(self._symbols, weights)}

    @property
    def metadata(self) -> Mapping[str, Any]:
        return {"name": "MeanVarianceStrategy", "framework": "none",
                "vol_cap": self._vol_cap, "lookback": self._lookback}
