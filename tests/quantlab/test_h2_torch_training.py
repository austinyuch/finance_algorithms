"""H-2 deep-learning real training — the real PyTorch backend (optional lane).

This file exercises *real* PyTorch training of the reference MLP. PyTorch is intentionally
excluded from the default root environment (see `a-torch-default-dependency-isolation`), so
the whole file is **skipped** unless torch is installed — exactly like the optional LSTM
lane (`tests/quantlab/test_a_2_lstm.py`). It runs in the torch-enabled UAT capture.

Requirements: REQ-H2-TORCHTRAIN-001, REQ-H2-PARITY-001, REQ-H2-DETERMINISM-001.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("torch", reason="PyTorch real-training lane is optional outside the UAT/runtime env")

# Documented parity tolerance (design.md §3): torch (float64, identical seed-init) tracks
# the framework-free reference to well under this absolute gap on expected returns.
PARITY_TOL = 1e-3


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


# --- REQ-H2-TORCHTRAIN-001 -----------------------------------------------------

def test_pytorch_backend_actually_resolves_and_trains():
    from quantlab.models import NumpyMLPForecaster

    data, dates = _synthetic_market()
    m = NumpyMLPForecaster(["GROWTH", "STEADY"], lookback=6, hidden=4, epochs=30, seed=0,
                           min_obs=24, backend="pytorch")
    out = m.forecast(dates[-1], data)

    assert m.backend == "pytorch"  # torch is installed in this lane → no fallback
    assert {f.symbol for f in out} == {"GROWTH", "STEADY"}
    assert all(f.status == "ok" and np.isfinite(f.expected_return) for f in out)
    # the model genuinely trained: full per-epoch trace and loss actually decreased
    assert len(m.training_trace) == 30
    assert m.training_trace[-1] < m.training_trace[0]


# --- REQ-H2-PARITY-001 ---------------------------------------------------------

def test_pytorch_matches_reference_within_documented_tolerance():
    from quantlab.models import NumpyMLPForecaster

    data, dates = _synthetic_market()
    cfg = dict(lookback=6, hidden=4, epochs=30, seed=0, min_obs=24)
    ref = NumpyMLPForecaster(["GROWTH", "STEADY"], backend="reference", **cfg)
    torch_m = NumpyMLPForecaster(["GROWTH", "STEADY"], backend="pytorch", **cfg)

    ref_out = {f.symbol: f.expected_return for f in ref.forecast(dates[-1], data)}
    torch_out = {f.symbol: f.expected_return for f in torch_m.forecast(dates[-1], data)}

    assert ref.backend == "reference" and torch_m.backend == "pytorch"
    for symbol in ("GROWTH", "STEADY"):
        assert abs(torch_out[symbol] - ref_out[symbol]) < PARITY_TOL
    # anti-masking: a loose tolerance must not let a no-op pass — torch really trained
    assert torch_m.training_trace[-1] < torch_m.training_trace[0]
    assert len(torch_m.training_trace) == len(ref.training_trace)


def test_pytorch_benchmark_report_shape_parity(tmp_path):
    from quantlab.models import run_deep_forecast_benchmark
    from quantlab.tracking import LocalResultStore

    data, dates = _synthetic_market()
    common = dict(symbols=["GROWTH", "STEADY"], lookback=6, hidden=4, epochs=20, seed=0)

    ref_report = run_deep_forecast_benchmark(
        data, dates, LocalResultStore(tmp_path / "ref.sqlite"), backend="reference", **common)
    torch_report = run_deep_forecast_benchmark(
        data, dates, LocalResultStore(tmp_path / "torch.sqlite"), backend="pytorch", **common)

    assert torch_report.keys() == ref_report.keys()
    assert torch_report["claim_boundary"] == "no_alpha_claim"
    assert torch_report["backend"] == "pytorch"
    assert ({r["strategy_name"] for r in torch_report["leaderboard"]}
            == {r["strategy_name"] for r in ref_report["leaderboard"]}
            == {"DeepForecastAllocationStrategy", "StaticWeights"})
    assert all(r["oos_net_sharpe"] is not None for r in torch_report["leaderboard"])


# --- REQ-H2-DETERMINISM-001 ----------------------------------------------------

def test_pytorch_training_is_deterministic():
    from quantlab.models import NumpyMLPForecaster

    data, dates = _synthetic_market()
    cfg = dict(lookback=6, hidden=4, epochs=30, seed=0, min_obs=24, backend="pytorch")
    a = NumpyMLPForecaster(["GROWTH", "STEADY"], **cfg)
    b = NumpyMLPForecaster(["GROWTH", "STEADY"], **cfg)

    fa = [f.expected_return for f in a.forecast(dates[-1], data)]
    fb = [f.expected_return for f in b.forecast(dates[-1], data)]

    assert fa == fb  # identical forecasts for equal seed/config/env
    assert a.training_trace == b.training_trace  # identical learning curve
