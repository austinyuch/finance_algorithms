"""H-2 framework-isolation + honest-fallback guards (run in any environment).

These assert the invariants that must hold whether or not torch is installed: requesting
the `pytorch` backend never raises, degrades honestly to `reference` when torch is absent,
and — critically — importing the forecaster never eagerly imports torch (the lazy
framework boundary). They run in the default (torch-excluded) env, not just the UAT lane.

Requirements: REQ-H2-OPTLANE-001, REQ-H2-ISOLATION-001.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys

import numpy as np
import pandas as pd


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


# --- REQ-H2-OPTLANE-001 --------------------------------------------------------

def test_pytorch_request_never_raises_and_degrades_honestly():
    """`backend="pytorch"` resolves to torch when present, else honest `reference` fallback."""
    from quantlab.models import NumpyMLPForecaster

    data, dates = _synthetic_market()
    m = NumpyMLPForecaster(["GROWTH", "STEADY"], lookback=6, hidden=4, epochs=20, seed=0,
                           min_obs=24, backend="pytorch")  # must not raise for a known label
    out = m.forecast(dates[-1], data)

    torch_present = importlib.util.find_spec("torch") is not None
    expected_backend = "pytorch" if torch_present else "reference"
    assert m.backend == expected_backend
    # either way the forecaster produces a finite, usable result
    assert {f.symbol for f in out} == {"GROWTH", "STEADY"}
    assert all(np.isfinite(f.expected_return) for f in out)
    assert len(m.training_trace) == 20


# --- REQ-H2-ISOLATION-001 ------------------------------------------------------

def test_importing_forecaster_does_not_eagerly_import_torch():
    """The framework boundary is lazy: importing the forecaster must not import torch.

    Run in a clean subprocess so the result is independent of whatever the rest of the
    test session has already imported (the torch lane may have imported torch elsewhere).
    """
    code = (
        "import sys; import quantlab.models.dl_forecaster as _m; "
        "import quantlab.models.dl.torch_trainer as _t; "
        "assert 'torch' not in sys.modules, 'torch was eagerly imported'; print('ok')"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout
