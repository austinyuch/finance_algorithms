"""H-1 deep-learning research lab — reference forecaster, adapter, backend registry.

RED/GREEN/REFACTOR trace:
- RED: added before `quantlab.models.dl_forecaster` / `quantlab.models.dl.backends` exist.
- GREEN: implement framework-free deterministic MLP + A0 adapter + honest backend registry.
- REFACTOR: clarify stat helpers without behaviour drift.

Requirements: REQ-H-DLMODEL-001, REQ-H-DLALLOC-001, REQ-H-FWBACKEND-001.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


def _provider_from_prices(prices_by_symbol: dict[str, list[float]], start: str = "2016-01-31"):
    from quantlab.data.provider import InMemoryPITDataProvider

    dates = pd.date_range(start, periods=len(next(iter(prices_by_symbol.values()))), freq="ME")
    rows = [
        {"symbol": sym, "event_date": date, "available_date": date, "close": float(value)}
        for sym, values in prices_by_symbol.items()
        for date, value in zip(dates, values)
    ]
    listings = pd.DataFrame(
        [{"symbol": sym, "list_date": pd.Timestamp("2014-01-01"), "delist_date": pd.NaT}
         for sym in prices_by_symbol]
    )
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(pd.DataFrame(rows), listings, macro), dates


def _synthetic_market(n: int = 96):
    rng = np.random.default_rng(7)
    growth = 100 * np.cumprod(1 + rng.normal(0.012, 0.04, n))
    steady = 100 * np.cumprod(1 + rng.normal(0.004, 0.02, n))
    return _provider_from_prices({"GROWTH": list(growth), "STEADY": list(steady)})


# --- REQ-H-DLMODEL-001 ---------------------------------------------------------

def test_numpy_mlp_is_pit_safe_and_deterministic():
    from quantlab.models import NumpyMLPForecaster

    data, dates = _synthetic_market()
    a = NumpyMLPForecaster(["GROWTH", "STEADY"], lookback=6, hidden=4, epochs=30, seed=0, min_obs=24)
    b = NumpyMLPForecaster(["GROWTH", "STEADY"], lookback=6, hidden=4, epochs=30, seed=0, min_obs=24)

    fa = a.forecast(dates[-1], data)
    fb = b.forecast(dates[-1], data)

    assert {f.symbol for f in fa} == {"GROWTH", "STEADY"}
    assert all(f.status == "ok" for f in fa)
    assert all(np.isfinite(f.expected_return) for f in fa)
    # determinism: identical forecasts AND identical learning curve for equal seed/config
    assert [f.expected_return for f in fa] == [f.expected_return for f in fb]
    assert a.training_trace == b.training_trace
    assert len(a.training_trace) == 30
    assert a.backend == "reference"
    # PIT: forecasting an earlier as-of uses only prior rows and is repeatable
    early = a.forecast(dates[40], data)
    assert early == a.forecast(dates[40], data)


def test_numpy_mlp_learning_curve_is_finite_and_improves():
    from quantlab.models import NumpyMLPForecaster

    data, dates = _synthetic_market()
    m = NumpyMLPForecaster(["GROWTH", "STEADY"], lookback=6, hidden=4, epochs=40, seed=1, min_obs=24)
    m.forecast(dates[-1], data)

    trace = m.training_trace
    assert trace and all(np.isfinite(v) and v >= 0 for v in trace)
    # full-batch gradient descent should not increase loss overall
    assert trace[-1] <= trace[0]


def test_numpy_mlp_degraded_on_thin_history():
    from quantlab.models import NumpyMLPForecaster

    data, dates = _synthetic_market(n=8)
    m = NumpyMLPForecaster(["GROWTH", "STEADY"], lookback=6, hidden=4, epochs=20, seed=0, min_obs=24)

    out = m.forecast(dates[-1], data)
    assert all(f.status == "degraded" for f in out)
    assert all(f.expected_return == 0.0 for f in out)


# --- REQ-H-DLALLOC-001 ---------------------------------------------------------

def test_deep_alloc_strategy_weights_long_only_sum_to_one():
    from quantlab.models import DeepForecastAllocationStrategy, NumpyMLPForecaster

    data, dates = _synthetic_market()
    strat = DeepForecastAllocationStrategy(
        NumpyMLPForecaster(["GROWTH", "STEADY"], lookback=6, hidden=4, epochs=30, seed=0, min_obs=24)
    )
    w = strat.generate_signal(dates[-1], data)

    assert set(w) == {"GROWTH", "STEADY"}
    assert all(np.isfinite(v) and v >= -1e-9 for v in w.values())
    assert sum(w.values()) == pytest.approx(1.0)
    md = strat.metadata
    assert md["name"] == "DeepForecastAllocationStrategy"
    assert md["claim_boundary"] == "no_alpha_claim"
    assert md["framework"] == "reference"
    assert md["learning_curve_points"] == 30


def test_deep_alloc_degraded_metadata():
    from quantlab.models import DeepForecastAllocationStrategy, NumpyMLPForecaster

    data, dates = _synthetic_market(n=8)
    strat = DeepForecastAllocationStrategy(
        NumpyMLPForecaster(["GROWTH", "STEADY"], lookback=6, hidden=4, epochs=20, seed=0, min_obs=24)
    )
    w = strat.generate_signal(dates[-1], data)

    assert w == pytest.approx({"GROWTH": 0.5, "STEADY": 0.5})
    assert strat.metadata["forecast_status"] == "degraded"
    assert strat.metadata["claim_boundary"] == "no_alpha_claim"


@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    a=st.lists(st.floats(min_value=-0.05, max_value=0.06, allow_nan=False, allow_infinity=False),
               min_size=40, max_size=70),
    b=st.lists(st.floats(min_value=-0.05, max_value=0.06, allow_nan=False, allow_infinity=False),
               min_size=40, max_size=70),
)
def test_pbt_deep_weights_long_only_and_finite(a, b):
    from quantlab.models import DeepForecastAllocationStrategy, NumpyMLPForecaster

    n = min(len(a), len(b))
    prices = {
        "A": list(100 * np.cumprod(1 + np.asarray(a[:n]))),
        "B": list(100 * np.cumprod(1 + np.asarray(b[:n]))),
    }
    data, dates = _provider_from_prices(prices)
    strat = DeepForecastAllocationStrategy(
        NumpyMLPForecaster(["A", "B"], lookback=6, hidden=4, epochs=15, seed=0, min_obs=20)
    )
    w = strat.generate_signal(dates[-1], data)

    assert set(w) == {"A", "B"}
    assert all(np.isfinite(v) and v >= -1e-9 for v in w.values())
    assert sum(w.values()) == pytest.approx(1.0)


# --- REQ-H-FWBACKEND-001 -------------------------------------------------------

def test_backend_registry_reference_always_available():
    from quantlab.models.dl.backends import FrameworkAdapterRegistry

    reg = FrameworkAdapterRegistry()
    assert "reference" in reg.available_backends()
    ref = reg.resolve("reference")
    assert ref.name == "reference"
    assert ref.available is True


def test_backend_resolve_absent_framework_falls_back_to_reference():
    from quantlab.models.dl.backends import FrameworkAdapterRegistry

    reg = FrameworkAdapterRegistry()
    # Regardless of whether torch/jax/tf are installed, resolve must NEVER raise for a
    # known label: when the framework is absent it degrades honestly to reference.
    for label in ("pytorch", "jax", "tensorflow"):
        resolved = reg.resolve(label)
        assert resolved.name in {label, "reference"}
        if resolved.name == "reference":
            assert resolved.requested == label
            assert resolved.reason  # records why it fell back
        assert resolved.available is True


def test_backend_unknown_label_fails_closed():
    from quantlab.models.dl.backends import FrameworkAdapterRegistry

    reg = FrameworkAdapterRegistry()
    with pytest.raises(ValueError):
        reg.resolve("quantum-annealer")


# --- REQ-H-DLALLOC-001 integration through the A0 engine -----------------------

def test_deep_forecast_benchmark_logs_oos_baseline_and_no_alpha_claim(tmp_path):
    from quantlab.models import run_deep_forecast_benchmark
    from quantlab.tracking import LocalResultStore

    data, dates = _synthetic_market()
    store = LocalResultStore(tmp_path / "h1.sqlite")

    report = run_deep_forecast_benchmark(
        data, dates, store, symbols=["GROWTH", "STEADY"],
        lookback=6, hidden=4, epochs=20, seed=0,
    )

    assert report["claim_boundary"] == "no_alpha_claim"
    names = {row["strategy_name"] for row in report["leaderboard"]}
    assert names == {"DeepForecastAllocationStrategy", "StaticWeights"}
    assert all(row["oos_net_sharpe"] is not None for row in report["leaderboard"])
    assert report["model_run_id"] and report["baseline_run_id"]
