"""Deterministic return/risk forecast model for Epic D second slice."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from quantlab.portfolio.optimize import optimize_max_return_under_vol
from quantlab.runner import run_and_log
from quantlab.strategies import StaticWeights


@dataclass(frozen=True)
class ReturnRiskForecast:
    symbol: str
    expected_return: float
    volatility: float
    observations: int
    status: str


class ReturnRiskForecaster:
    """Rolling PIT mean/vol forecaster.

    This is not an alpha claim. It is a deterministic model family slice used to
    exercise the A0 harness with a forecast-driven strategy.
    """

    def __init__(self, symbols: Sequence[str], lookback: int = 36, min_obs: int = 24,
                 periods_per_year: int = 12, volatility_floor: float = 1e-9) -> None:
        self._symbols = list(symbols)
        self._lookback = int(lookback)
        self._min_obs = int(min_obs)
        self._ppy = int(periods_per_year)
        self._vol_floor = float(volatility_floor)

    def forecast(self, asof: Any, data: Any) -> list[ReturnRiskForecast]:
        hist = data.history(pd.Timestamp(asof), "close", self._symbols)
        out = []
        for symbol in self._symbols:
            if symbol not in hist.columns:
                out.append(self._degraded(symbol, 0))
                continue
            prices = hist[symbol].dropna().tail(self._lookback + 1)
            returns = prices.pct_change().dropna()
            out.append(self._forecast_symbol(symbol, returns))
        return out

    def _forecast_symbol(self, symbol: str, returns: pd.Series) -> ReturnRiskForecast:
        obs = int(returns.shape[0])
        if obs < self._min_obs:
            return self._degraded(symbol, obs)
        expected = float(returns.mean() * self._ppy)
        volatility = float(returns.std(ddof=0) * np.sqrt(self._ppy))
        if not np.isfinite(expected) or not np.isfinite(volatility):
            return self._degraded(symbol, obs)
        return ReturnRiskForecast(
            symbol=symbol,
            expected_return=expected,
            volatility=max(volatility, self._vol_floor),
            observations=obs,
            status="ok",
        )

    @staticmethod
    def _degraded(symbol: str, observations: int) -> ReturnRiskForecast:
        return ReturnRiskForecast(symbol, 0.0, 0.0, observations, "degraded")


class ForecastAllocationStrategy:
    """A0-compatible strategy using return/risk forecasts and C optimizer."""

    def __init__(self, forecaster: ReturnRiskForecaster, vol_cap: float = 0.30,
                 w_max: float = 1.0) -> None:
        self._forecaster = forecaster
        self._vol_cap = float(vol_cap)
        self._w_max = float(w_max)
        self._last_status = "not_run"
        self._last_weights: dict[str, float] = {}

    def fit(self, train: Any = None, **kwargs: Any) -> None:
        return None

    def generate_signal(self, asof: Any, data: Any) -> Mapping[str, float]:
        forecasts = self._forecaster.forecast(asof, data)
        if not forecasts or any(f.status != "ok" for f in forecasts):
            self._last_status = "degraded"
            self._last_weights = self._equal([f.symbol for f in forecasts])
            return dict(self._last_weights)

        mu = np.asarray([f.expected_return for f in forecasts], dtype=float)
        cov = np.diag([f.volatility ** 2 for f in forecasts])
        weights = optimize_max_return_under_vol(mu, cov, self._vol_cap, self._w_max)
        self._last_status = "ok"
        self._last_weights = {f.symbol: float(w) for f, w in zip(forecasts, weights)}
        return dict(self._last_weights)

    @property
    def metadata(self) -> Mapping[str, Any]:
        return {
            "name": "ForecastAllocationStrategy",
            "framework": "none",
            "forecast_status": self._last_status,
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
        "data_version": "return-risk-forecast",
        "walk_forward": {"train_window_months": 36, "test_window_months": 12, "step_months": 12},
    }


def run_return_risk_forecast_benchmark(
    data: Any,
    dates: Sequence[pd.Timestamp],
    store: Any,
    *,
    symbols: Sequence[str],
    config: Mapping[str, Any] | None = None,
    vol_cap: float = 0.30,
) -> dict[str, Any]:
    ordered = [pd.Timestamp(d) for d in dates]
    if len(ordered) < 12:
        raise ValueError("return/risk benchmark requires at least 12 price dates")
    cfg = dict(config or _default_config(ordered))
    strategy = ForecastAllocationStrategy(ReturnRiskForecaster(symbols), vol_cap=vol_cap)
    baseline = StaticWeights({symbol: 1.0 for symbol in symbols})

    forecast_run_id, _ = run_and_log(strategy, data, cfg, store)
    baseline_run_id, _ = run_and_log(baseline, data, cfg, store)
    return {
        "claim_boundary": "no_alpha_claim",
        "forecast_run_id": forecast_run_id,
        "baseline_run_id": baseline_run_id,
        "leaderboard": store.leaderboard(),
    }
