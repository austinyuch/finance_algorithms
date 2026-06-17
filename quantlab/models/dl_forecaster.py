"""Framework-free deep neural forecaster for Epic H (REQ-H-DLMODEL-001/002).

`NumpyMLPForecaster` is a deterministic, from-scratch multi-layer perceptron (one tanh
hidden layer) trained by full-batch gradient descent on lookback-windowed PIT returns.
It is the **reference backend**: it always runs without any ML framework installed, and
it realizes the same `DeepForecastModel` shape that a real PyTorch / JAX / TensorFlow
backend would (resolved via :class:`FrameworkAdapterRegistry`). It is a research
mechanism, not an alpha source — every output carries `no_alpha_claim`.

⚠️ Framework isolation: this lives in `quantlab.models` (allowed numpy/pandas). The
backtest core (`quantlab.engine` / `quantlab.data`) must not import ML frameworks; the
backend registry keeps framework imports lazy and confined.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

import numpy as np
import pandas as pd

from quantlab.models.dl.backends import FrameworkAdapterRegistry
from quantlab.runner import run_and_log
from quantlab.strategies import StaticWeights


@dataclass(frozen=True)
class DeepForecast:
    symbol: str
    expected_return: float
    status: str


@runtime_checkable
class DeepForecastModel(Protocol):
    """Domain protocol: map PIT history to a per-symbol expected return + learning curve."""

    backend: str
    training_trace: list[float]

    def forecast(self, asof: Any, data: Any) -> list[DeepForecast]: ...


class NumpyMLPForecaster:
    """Deterministic numpy MLP forecaster (the framework-free reference backend)."""

    def __init__(self, symbols: Sequence[str], *, lookback: int = 6, hidden: int = 4,
                 epochs: int = 30, seed: int = 0, min_obs: int = 24, lr: float = 0.1,
                 backend: str = "reference") -> None:
        self._symbols = list(symbols)
        self._lookback = int(lookback)
        self._hidden = int(hidden)
        self._epochs = int(epochs)
        self._seed = int(seed)
        self._min_obs = int(min_obs)
        self._lr = float(lr)
        # Resolve the backend now so the label is stable before training and degrades
        # honestly when the requested framework is absent.
        self.backend = FrameworkAdapterRegistry().resolve(backend).name
        self.training_trace: list[float] = []

    # --- public API ---

    def forecast(self, asof: Any, data: Any) -> list[DeepForecast]:
        """Retrain (seeded) on rows available at/<= ``asof`` and forecast each symbol.

        No state is cached across as-of dates, so repeated calls are deterministic and
        no future row can leak into an earlier forecast (PIT-safe).
        """
        hist = data.history(pd.Timestamp(asof), "close", self._symbols)
        returns_by_symbol: dict[str, np.ndarray] = {}
        for symbol in self._symbols:
            if symbol not in hist.columns:
                returns_by_symbol[symbol] = np.empty(0)
                continue
            prices = hist[symbol].dropna().to_numpy(dtype="float64")
            returns_by_symbol[symbol] = (np.diff(prices) / prices[:-1]) if len(prices) > 1 else np.empty(0)

        x_train, y_train = self._pooled_windows(returns_by_symbol)
        self.training_trace = []
        if x_train.shape[0] < self._min_obs or any(
            len(r) < self._lookback + 1 for r in returns_by_symbol.values()
        ):
            return [self._degraded(symbol) for symbol in self._symbols]

        x_mean, x_std = x_train.mean(axis=0), x_train.std(axis=0)
        x_std = np.where(x_std > 1e-12, x_std, 1.0)
        y_mean, y_std = float(y_train.mean()), float(y_train.std())
        if y_std <= 1e-12:
            return [self._degraded(symbol) for symbol in self._symbols]

        xs = (x_train - x_mean) / x_std
        ys = ((y_train - y_mean) / y_std).reshape(-1, 1)
        weights = self._train(xs, ys)

        out: list[DeepForecast] = []
        for symbol in self._symbols:
            window = returns_by_symbol[symbol][-self._lookback:]
            xw = ((window - x_mean) / x_std).reshape(1, -1)
            pred_std = float(self._forward(xw, weights)[0][0, 0])
            expected = pred_std * y_std + y_mean
            if not np.isfinite(expected):
                out.append(self._degraded(symbol))
            else:
                out.append(DeepForecast(symbol=symbol, expected_return=expected, status="ok"))
        return out

    # --- internals ---

    def _pooled_windows(self, returns_by_symbol: Mapping[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
        xs: list[np.ndarray] = []
        ys: list[float] = []
        for returns in returns_by_symbol.values():
            for i in range(len(returns) - self._lookback):
                xs.append(returns[i:i + self._lookback])
                ys.append(float(returns[i + self._lookback]))
        if not xs:
            return np.empty((0, self._lookback)), np.empty(0)
        return np.asarray(xs, dtype="float64"), np.asarray(ys, dtype="float64")

    def _train(self, xs: np.ndarray, ys: np.ndarray) -> dict[str, np.ndarray]:
        if self.backend == "pytorch":
            # Real PyTorch training (slice H-2). The lazy import keeps the
            # framework-isolation boundary intact; reachable only when the registry
            # resolved torch as installed, so the default env never enters this branch.
            from quantlab.models.dl.torch_trainer import train_mlp_torch

            weights, trace = train_mlp_torch(
                xs, ys, lookback=self._lookback, hidden=self._hidden,
                epochs=self._epochs, seed=self._seed, lr=self._lr,
            )
            self.training_trace = trace
            return weights
        rng = np.random.default_rng(self._seed)
        w1 = rng.standard_normal((self._lookback, self._hidden)) * 0.1
        b1 = np.zeros((1, self._hidden))
        w2 = rng.standard_normal((self._hidden, 1)) * 0.1
        b2 = np.zeros((1, 1))
        n = xs.shape[0]
        for _ in range(self._epochs):
            out, hidden = self._forward(xs, {"w1": w1, "b1": b1, "w2": w2, "b2": b2})
            err = out - ys
            self.training_trace.append(float(np.mean(err ** 2)))
            grad_out = (2.0 / n) * err
            grad_w2 = hidden.T @ grad_out
            grad_b2 = grad_out.sum(axis=0, keepdims=True)
            grad_hidden = (grad_out @ w2.T) * (1.0 - hidden ** 2)  # tanh'
            grad_w1 = xs.T @ grad_hidden
            grad_b1 = grad_hidden.sum(axis=0, keepdims=True)
            w1 -= self._lr * grad_w1
            b1 -= self._lr * grad_b1
            w2 -= self._lr * grad_w2
            b2 -= self._lr * grad_b2
        return {"w1": w1, "b1": b1, "w2": w2, "b2": b2}

    @staticmethod
    def _forward(xs: np.ndarray, weights: Mapping[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
        hidden = np.tanh(xs @ weights["w1"] + weights["b1"])
        out = hidden @ weights["w2"] + weights["b2"]
        return out, hidden

    @staticmethod
    def _degraded(symbol: str) -> DeepForecast:
        return DeepForecast(symbol=symbol, expected_return=0.0, status="degraded")


class DeepForecastAllocationStrategy:
    """A0-compatible strategy wrapping a deep forecaster (long-only, OOS-net ranked)."""

    def __init__(self, forecaster: NumpyMLPForecaster) -> None:
        self._forecaster = forecaster
        self._last_status = "not_run"
        self._last_weights: dict[str, float] = {}

    def fit(self, train: Any = None, **kwargs: Any) -> None:
        return None  # PIT (re)training happens per as-of in generate_signal

    def generate_signal(self, asof: Any, data: Any) -> Mapping[str, float]:
        forecasts = self._forecaster.forecast(asof, data)
        symbols = [f.symbol for f in forecasts]
        if not forecasts or any(f.status != "ok" for f in forecasts):
            self._last_status = "degraded"
            self._last_weights = self._equal(symbols)
            return dict(self._last_weights)

        positive = np.clip([f.expected_return for f in forecasts], 0.0, None)
        total = float(positive.sum())
        if total <= 0.0:
            self._last_weights = self._equal(symbols)
        else:
            self._last_weights = {f.symbol: float(p / total) for f, p in zip(forecasts, positive)}
        self._last_status = "ok"
        return dict(self._last_weights)

    @property
    def metadata(self) -> Mapping[str, Any]:
        return {
            "name": "DeepForecastAllocationStrategy",
            "framework": self._forecaster.backend,
            "claim_boundary": "no_alpha_claim",
            "forecast_status": self._last_status,
            "learning_curve_points": len(self._forecaster.training_trace),
            "weights": dict(self._last_weights),
        }

    @staticmethod
    def _equal(symbols: Sequence[str]) -> dict[str, float]:
        if not symbols:
            return {}
        weight = 1.0 / len(symbols)
        return {str(symbol): weight for symbol in symbols}


def _default_config(dates: Sequence[pd.Timestamp], rebalance: str = "monthly") -> dict[str, Any]:
    return {
        "start": str(pd.Timestamp(dates[0]).date()),
        "end": str(pd.Timestamp(dates[-1]).date()),
        "rebalance": rebalance,
        "fill": "same_close",
        "mode": "net",
        "cost_config": {"commission_bps": 5, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
                        "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
        "seed": 0,
        "data_version": "deep-forecast",
        "walk_forward": {"train_window_months": 36, "test_window_months": 12, "step_months": 12},
    }


def run_deep_forecast_benchmark(
    data: Any,
    dates: Sequence[pd.Timestamp],
    store: Any,
    *,
    symbols: Sequence[str],
    config: Mapping[str, Any] | None = None,
    lookback: int = 6,
    hidden: int = 4,
    epochs: int = 20,
    seed: int = 0,
    backend: str = "reference",
) -> dict[str, Any]:
    """Run the deep model + a dumb StaticWeights baseline → leaderboard (OOS-net)."""
    ordered = [pd.Timestamp(d) for d in dates]
    if len(ordered) < 12:
        raise ValueError("deep forecast benchmark requires at least 12 price dates")
    cfg = dict(config or _default_config(ordered, str((config or {}).get("rebalance", "monthly"))))
    forecaster = NumpyMLPForecaster(symbols, lookback=lookback, hidden=hidden,
                                    epochs=epochs, seed=seed, backend=backend)
    strategy = DeepForecastAllocationStrategy(forecaster)
    baseline = StaticWeights({symbol: 1.0 for symbol in symbols})

    model_run_id, _ = run_and_log(strategy, data, cfg, store)
    baseline_run_id, _ = run_and_log(baseline, data, cfg, store)
    return {
        "claim_boundary": "no_alpha_claim",
        "backend": forecaster.backend,
        "model_run_id": model_run_id,
        "baseline_run_id": baseline_run_id,
        "leaderboard": store.leaderboard(),
    }
