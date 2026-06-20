"""A0-2 vectorized engine — chaos hardening (CR-A0-CHAOS-001).

Extreme-market / invalid-data inputs that the dashboard must never render as a
fabricated number. Complements the happy-path + PBT coverage in
``test_a0_2_engine.py``. Each test pins fail-closed / degrade-honestly behaviour:
the engine treats invalid prices as *missing legs* and never emits NaN/inf metrics.

Trace: REQ-A0-BT-005, FMEA-A0-CHAOS-01 (garbage-in → fabricated OOS-net metric).
"""
from __future__ import annotations

import math

import pandas as pd

from quantlab.data.provider import InMemoryPITDataProvider
from quantlab.engine import VectorizedEngine
from quantlab.engine.metrics import compute_metrics
from quantlab.strategies import BuyAndHold

_TS = pd.Timestamp
_LISTINGS = pd.DataFrame([{"symbol": "X", "list_date": _TS("2019-01-01"), "delist_date": pd.NaT}])
_MACRO = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])


def _provider(closes: list[float]) -> InMemoryPITDataProvider:
    dates = pd.date_range("2020-01-31", periods=len(closes), freq="ME")
    prices = pd.DataFrame(
        [
            {"symbol": "X", "event_date": d, "available_date": d, "close": c}
            for d, c in zip(dates, closes)
        ]
    )
    return InMemoryPITDataProvider(prices, _LISTINGS.copy(), _MACRO.copy())


def _config(n_months: int) -> dict:
    dates = pd.date_range("2020-01-31", periods=n_months, freq="ME")
    return {
        "start": str(dates[0].date()), "end": str(dates[-1].date()),
        "rebalance": "monthly", "fill": "same_close", "mode": "gross",
        "cost_config": {}, "seed": 0, "data_version": "chaos",
    }


def _run(closes: list[float]) -> dict:
    return VectorizedEngine().run(BuyAndHold(["X"]), _provider(closes), _config(len(closes)))


def _all_metrics_finite(result: dict) -> None:
    for m in result["metrics"]:
        for key in ("cumulative_return", "annualized_return", "annualized_vol",
                    "max_drawdown", "sharpe"):
            assert math.isfinite(m[key]), f"{m['segment']}.{key} is non-finite: {m[key]!r}"


# --- CHAOS-1: all-NaN closes must not fabricate NaN metrics ---

def test_chaos_all_nan_close_does_not_fabricate_metrics():
    result = _run([float("nan")] * 4)
    _all_metrics_finite(result)
    full = next(m for m in result["metrics"] if m["segment"] == "full")
    # Every leg is missing → zero realised return, not a NaN-poisoned series.
    assert full["cumulative_return"] == 0.0
    assert full["sharpe"] == 0.0


# --- CHAOS-2: a single NaN mid-series only drops that leg ---

def test_chaos_partial_nan_close_drops_only_affected_leg():
    clean = _run([100.0, 110.0, 121.0, 133.1])
    holed = _run([100.0, float("nan"), 121.0, 133.1])
    _all_metrics_finite(holed)
    # The NaN month cannot fabricate a return, so cumulative differs from the clean run.
    assert holed["metrics"][0]["cumulative_return"] != clean["metrics"][0]["cumulative_return"]


# --- CHAOS-3: non-positive (zero/negative) close is invalid, not a tradable price ---

def test_chaos_negative_close_treated_as_missing():
    result = _run([100.0, -110.0, 121.0, 133.1])
    _all_metrics_finite(result)
    # A negative price must never produce a fabricated negative-price return.
    assert result["metrics"][0]["cumulative_return"] > -1.0


def test_chaos_infinite_close_treated_as_missing():
    result = _run([100.0, float("inf"), 121.0])
    _all_metrics_finite(result)


# --- CHAOS-4: zero-volatility path yields a finite (zero) Sharpe, never NaN/inf ---

def test_chaos_zero_volatility_returns_finite_sharpe():
    # Doubling closes → every period return is exactly 1.0 (exact in float) → std == 0,
    # so a degenerate zero-vol path must yield Sharpe 0.0, never a divide-by-zero inf/NaN.
    result = _run([100.0, 200.0, 400.0, 800.0, 1600.0])
    _all_metrics_finite(result)
    full = next(m for m in result["metrics"] if m["segment"] == "full")
    assert full["annualized_vol"] == 0.0
    assert full["sharpe"] == 0.0


# --- CHAOS-5: total-loss path caps annualized return at -100%, drawdown stays finite ---

def test_chaos_total_loss_path_metrics_bounded():
    m = compute_metrics(pd.Series([-1.0, 0.0]), turnover=1.0, periods_per_year=12,
                        basis="gross", segment="full")
    assert m["annualized_return"] == -1.0
    assert m["max_drawdown"] == -1.0
    assert math.isfinite(m["sharpe"])
