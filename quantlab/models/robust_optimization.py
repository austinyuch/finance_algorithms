"""Robust portfolio optimization model family for Epic D."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from quantlab.portfolio.optimize import optimize_max_return_under_vol
from quantlab.runner import run_and_log
from quantlab.strategies import StaticWeights


@dataclass(frozen=True)
class RobustAssetEstimate:
    symbol: str
    mean_return: float
    downside_semideviation: float
    adjusted_return: float
    volatility: float
    observations: int
    status: str


class RobustPortfolioModel:
    """PIT estimator that penalizes downside semideviation."""

    def __init__(self, symbols: Sequence[str], lookback: int = 36, min_obs: int = 24,
                 periods_per_year: int = 12, downside_penalty: float = 1.0,
                 volatility_floor: float = 1e-6) -> None:
        self._symbols = list(symbols)
        self._lookback = int(lookback)
        self._min_obs = int(min_obs)
        self._ppy = int(periods_per_year)
        self._penalty = float(downside_penalty)
        self._vol_floor = float(volatility_floor)

    def estimate(self, asof: Any, data: Any) -> list[RobustAssetEstimate]:
        hist = data.history(pd.Timestamp(asof), "close", self._symbols)
        estimates = []
        for symbol in self._symbols:
            if symbol not in hist.columns:
                estimates.append(self._degraded(symbol, 0))
                continue
            prices = hist[symbol].dropna().tail(self._lookback + 1)
            returns = prices.pct_change().dropna()
            estimates.append(self._estimate_symbol(symbol, returns))
        return estimates

    def _estimate_symbol(self, symbol: str, returns: pd.Series) -> RobustAssetEstimate:
        obs = int(returns.shape[0])
        if obs < self._min_obs:
            return self._degraded(symbol, obs)
        mean_return = float(returns.mean() * self._ppy)
        volatility = float(returns.std(ddof=0) * np.sqrt(self._ppy))
        downside = returns[returns < 0.0]
        downside_semideviation = float(np.sqrt((downside ** 2).mean()) * np.sqrt(self._ppy)) if len(downside) else 0.0
        adjusted = mean_return - self._penalty * downside_semideviation
        if not all(np.isfinite(v) for v in (mean_return, volatility, downside_semideviation, adjusted)):
            return self._degraded(symbol, obs)
        return RobustAssetEstimate(
            symbol=symbol,
            mean_return=mean_return,
            downside_semideviation=downside_semideviation,
            adjusted_return=adjusted,
            volatility=max(volatility, self._vol_floor),
            observations=obs,
            status="ok",
        )

    @staticmethod
    def _degraded(symbol: str, observations: int) -> RobustAssetEstimate:
        return RobustAssetEstimate(symbol, 0.0, 0.0, 0.0, 0.0, observations, "degraded")


class RobustOptimizationStrategy:
    """A0-compatible robust portfolio optimization strategy."""

    def __init__(self, model: RobustPortfolioModel, vol_cap: float = 0.30,
                 w_max: float = 1.0) -> None:
        self._model = model
        self._vol_cap = float(vol_cap)
        self._w_max = float(w_max)
        self._last_status = "not_run"
        self._last_weights: dict[str, float] = {}

    def fit(self, train: Any = None, **kwargs: Any) -> None:
        return None

    def generate_signal(self, asof: Any, data: Any) -> Mapping[str, float]:
        estimates = self._model.estimate(asof, data)
        if not estimates or any(estimate.status != "ok" for estimate in estimates):
            self._last_status = "degraded"
            self._last_weights = self._equal([estimate.symbol for estimate in estimates])
            return dict(self._last_weights)

        mu = np.asarray([estimate.adjusted_return for estimate in estimates], dtype=float)
        cov = np.diag([estimate.volatility ** 2 for estimate in estimates])
        weights = optimize_max_return_under_vol(mu, cov, self._vol_cap, self._w_max)
        self._last_status = "ok"
        self._last_weights = {estimate.symbol: float(weight) for estimate, weight in zip(estimates, weights)}
        return dict(self._last_weights)

    @property
    def metadata(self) -> Mapping[str, Any]:
        return {
            "name": "RobustOptimizationStrategy",
            "framework": "none",
            "robust_status": self._last_status,
            "claim_boundary": "no_alpha_claim",
            "weights": dict(self._last_weights),
            "vol_cap": self._vol_cap,
        }

    @staticmethod
    def _equal(symbols: Sequence[str]) -> dict[str, float]:
        if not symbols:
            return {}
        weight = 1.0 / len(symbols)
        return {str(symbol): weight for symbol in symbols}


def _default_config(dates: Sequence[pd.Timestamp]) -> dict[str, Any]:
    return {
        "start": str(pd.Timestamp(dates[0]).date()),
        "end": str(pd.Timestamp(dates[-1]).date()),
        "rebalance": "monthly",
        "fill": "same_close",
        "mode": "net",
        "cost_config": {"commission_bps": 5, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
                        "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
        "seed": 0,
        "data_version": "robust-optimization",
        "walk_forward": {"train_window_months": 36, "test_window_months": 12, "step_months": 12},
    }


def run_robust_optimization_benchmark(
    data: Any,
    dates: Sequence[pd.Timestamp],
    store: Any,
    *,
    symbols: Sequence[str],
    config: Mapping[str, Any] | None = None,
    vol_cap: float = 0.30,
) -> dict[str, Any]:
    ordered = [pd.Timestamp(date) for date in dates]
    if len(ordered) < 12:
        raise ValueError("robust optimization benchmark requires at least 12 price dates")
    cfg = dict(config or _default_config(ordered))
    strategy = RobustOptimizationStrategy(RobustPortfolioModel(symbols), vol_cap=vol_cap)
    baseline = StaticWeights({symbol: 1.0 for symbol in symbols})
    robust_run_id, _ = run_and_log(strategy, data, cfg, store)
    baseline_run_id, _ = run_and_log(baseline, data, cfg, store)
    return {
        "claim_boundary": "no_alpha_claim",
        "robust_run_id": robust_run_id,
        "baseline_run_id": baseline_run_id,
        "leaderboard": store.leaderboard(),
    }
