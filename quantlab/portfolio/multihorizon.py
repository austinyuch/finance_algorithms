"""多期配置策略(REQ-C-MULTI-001)。

每個 horizon 以自己的 lookback / vol_cap 估計一組 mean-variance 權重,再依
budget_weight 混合為單一可回測配置。僅使用 provider.history(asof, ...),維持 PIT。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from quantlab.portfolio.optimize import optimize_max_return_under_vol


@dataclass(frozen=True)
class HorizonConfig:
    name: str
    lookback: int
    vol_cap: float
    budget_weight: float


class MultiHorizonMeanVarianceStrategy:
    def __init__(
        self,
        symbols: Sequence[str],
        horizons: Sequence[HorizonConfig] | None = None,
        min_obs: int = 24,
        periods_per_year: int = 12,
    ) -> None:
        self._symbols = list(symbols)
        self._horizons = list(horizons) if horizons is not None else [
            HorizonConfig("short", lookback=12, vol_cap=0.20, budget_weight=0.25),
            HorizonConfig("medium", lookback=36, vol_cap=0.30, budget_weight=0.50),
            HorizonConfig("long", lookback=60, vol_cap=0.35, budget_weight=0.25),
        ]
        if not self._symbols:
            raise ValueError("symbols must not be empty")
        if not self._horizons:
            raise ValueError("horizons must not be empty")
        if any(h.lookback <= 0 or h.vol_cap <= 0 or h.budget_weight < 0 for h in self._horizons):
            raise ValueError("horizon lookback/vol_cap must be positive and budget_weight non-negative")
        if sum(h.budget_weight for h in self._horizons) <= 0:
            raise ValueError("at least one horizon budget_weight must be positive")
        self._min_obs = int(min_obs)
        self._ppy = int(periods_per_year)

    def fit(self, train: Any = None, **kwargs: Any) -> None:
        return None

    def _equal_array(self) -> np.ndarray:
        return np.ones(len(self._symbols), dtype=float) / len(self._symbols)

    def _weights_for_horizon(self, returns: Any, horizon: HorizonConfig) -> np.ndarray:
        window = returns.tail(horizon.lookback)
        if window.shape[0] < self._min_obs:
            return self._equal_array()
        mu = window.mean().to_numpy() * self._ppy
        cov = window.cov().to_numpy() * self._ppy
        return optimize_max_return_under_vol(mu, cov, horizon.vol_cap)

    def generate_signal(self, asof: Any, data: Any) -> Mapping[str, float]:
        hist = data.history(asof, "close", self._symbols).dropna()
        if hist.shape[0] < self._min_obs + 1:
            weights = self._equal_array()
        else:
            returns = hist[self._symbols].pct_change().dropna()
            horizon_total = sum(h.budget_weight for h in self._horizons)
            weights = np.zeros(len(self._symbols), dtype=float)
            for horizon in self._horizons:
                share = horizon.budget_weight / horizon_total
                weights += share * self._weights_for_horizon(returns, horizon)
        weights = np.clip(np.asarray(weights, dtype=float), 0.0, None)
        weights = weights / weights.sum() if weights.sum() > 0 else self._equal_array()
        return {sym: float(w) for sym, w in zip(self._symbols, weights)}

    @property
    def metadata(self) -> Mapping[str, Any]:
        return {
            "name": "MultiHorizonMeanVarianceStrategy",
            "framework": "none",
            "horizons": [
                {
                    "name": h.name,
                    "lookback": h.lookback,
                    "vol_cap": h.vol_cap,
                    "budget_weight": h.budget_weight,
                }
                for h in self._horizons
            ],
            "min_obs": self._min_obs,
        }
