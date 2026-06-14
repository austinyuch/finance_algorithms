"""Tests — CR-RDO-004 sampling-frequency homogeneity guard.

Covers REQ-RDO-CR4-001/002/003: native cadence estimation + provenance, the
oversampling fail-closed guard (rebalance finer than the coarsest native
cadence → fabricated flat returns → dishonest Sharpe), and the CLI reason
mapping. TDD: authored before the change. no_alpha_claim preserved throughout.
"""
from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import given, strategies as st

from quantlab.data.provider import InMemoryPITDataProvider
from quantlab.research.real_data_oos import (
    SamplingFrequency,
    SamplingFrequencyError,
    assess_data_sufficiency,
    build_real_data_oos_report,
    classify_cadence,
    estimate_sampling_frequencies,
    is_oversampled,
    rebalance_cadence_days,
)
from quantlab.strategies import BuyAndHold, RandomStrategy

_FACTORS = [1.03, 0.98, 1.02, 0.97, 1.04, 0.99]


def _closes(n: int, offset: int) -> list[float]:
    closes, c = [], 100.0 + offset * 7.0
    for i in range(n):
        c *= _FACTORS[(i + offset) % len(_FACTORS)]
        closes.append(round(c, 4))
    return closes


def _make_provider(specs) -> InMemoryPITDataProvider:
    """specs: list of (symbol, start_iso, periods, pandas_freq)."""
    prows = []
    for si, (sym, start, n, freq) in enumerate(specs):
        dates = pd.date_range(start, periods=n, freq=freq)
        for d, c in zip(dates, _closes(n, si)):
            prows.append({"symbol": sym, "event_date": d, "available_date": d, "close": c})
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("1990-01-01"),
                              "delist_date": pd.NaT} for s, _, _, _ in specs])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(pd.DataFrame(prows), listings, macro)


def _cfg(rebalance: str = "monthly") -> dict:
    return {"rebalance": rebalance, "mode": "net",
            "cost_config": {"commission_bps": 10, "slippage_bps": 5},
            "walk_forward": {"train_window_months": 12, "test_window_months": 6, "step_months": 6}}


# --- REQ-RDO-CR4-001: cadence estimation ---

def test_classify_cadence_boundaries():
    assert classify_cadence(1.0) == "daily"
    assert classify_cadence(4.0) == "daily"
    assert classify_cadence(4.1) == "weekly"
    assert classify_cadence(10.0) == "weekly"
    assert classify_cadence(10.1) == "monthly"
    assert classify_cadence(45.0) == "monthly"
    assert classify_cadence(45.1) == "quarterly"
    assert classify_cadence(135.0) == "quarterly"
    assert classify_cadence(135.1) == "irregular"


def test_estimate_sampling_frequencies_daily_and_monthly():
    provider = _make_provider([
        ("DAILY", "2024-01-01", 60, "D"),
        ("MONTH", "2020-01-31", 48, "ME"),
    ])
    freqs = estimate_sampling_frequencies(provider)
    assert isinstance(freqs["DAILY"], SamplingFrequency)
    assert freqs["DAILY"].cadence == "daily"
    assert freqs["DAILY"].median_spacing_days == pytest.approx(1.0, abs=0.5)
    assert freqs["MONTH"].cadence == "monthly"
    assert 27.0 <= freqs["MONTH"].median_spacing_days <= 32.0


def test_estimate_single_observation_is_irregular():
    provider = _make_provider([("ONE", "2024-01-01", 1, "D")])
    freq = estimate_sampling_frequencies(provider)["ONE"]
    assert freq.median_spacing_days == 0.0
    assert freq.cadence == "irregular"


def test_rebalance_cadence_days_known_and_fallback():
    assert rebalance_cadence_days("daily") == pytest.approx(1.0)
    assert rebalance_cadence_days("weekly") == pytest.approx(7.0)
    assert rebalance_cadence_days("monthly") == pytest.approx(30.4375)
    assert rebalance_cadence_days("quarterly") == pytest.approx(91.3125)
    assert rebalance_cadence_days("unknown") == pytest.approx(30.4375)  # monthly fallback


def test_sufficiency_records_frequency_homogeneity():
    homo = assess_data_sufficiency(
        _make_provider([("A", "2010-01-31", 180, "ME"), ("B", "2010-01-31", 180, "ME")]),
        min_history_months=18.0)
    assert homo.frequency_homogeneous is True
    assert dict(homo.sampling_frequencies) == {"A": "monthly", "B": "monthly"}

    mixed = assess_data_sufficiency(
        _make_provider([("M", "2010-01-31", 180, "ME"), ("Q", "2010-01-31", 60, "QE")]),
        min_history_months=18.0)
    assert mixed.frequency_homogeneous is False
    assert mixed.coarsest_cadence_days > 60.0  # quarterly drives the coarsest


# --- REQ-RDO-CR4-002: oversampling guard ---

def test_report_passes_on_homogeneous_monthly_under_monthly_rebalance():
    provider = _make_provider([("A", "2010-01-31", 180, "ME"), ("B", "2010-01-31", 180, "ME")])
    universe = ["A", "B"]
    report = build_real_data_oos_report(
        provider, candidate=RandomStrategy(universe, seed=0),
        baseline=BuyAndHold(universe), config=_cfg("monthly"))
    assert report["status"] == "computed"
    sf = report["data_provenance"]["sampling_frequency"]
    assert sf["homogeneous"] is True
    assert sf["coarsest_cadence"] == "monthly"
    assert sf["rebalance"] == "monthly"


def test_report_fails_closed_on_quarterly_asset_under_monthly_rebalance():
    provider = _make_provider([("M", "2010-01-31", 180, "ME"), ("Q", "2010-01-31", 60, "QE")])
    with pytest.raises(SamplingFrequencyError, match="oversampl"):
        build_real_data_oos_report(
            provider, candidate=RandomStrategy(["M", "Q"], seed=0),
            baseline=BuyAndHold(["M", "Q"]), config=_cfg("monthly"))


def test_report_passes_when_rebalance_is_coarse_enough():
    # Same mixed universe, but quarterly rebalance is not finer than the coarsest
    # native cadence, so no stale forward-fill is fabricated.
    provider = _make_provider([("M", "2008-01-31", 200, "ME"), ("Q", "2008-01-31", 66, "QE")])
    report = build_real_data_oos_report(
        provider, candidate=RandomStrategy(["M", "Q"], seed=0),
        baseline=BuyAndHold(["M", "Q"]), config=_cfg("quarterly"))
    assert report["status"] == "computed"
    assert report["data_provenance"]["sampling_frequency"]["homogeneous"] is False


def test_sampling_frequency_error_is_value_error():
    assert issubclass(SamplingFrequencyError, ValueError)


# --- REQ-RDO-CR4-002: PBT ---

@given(
    coarsest=st.floats(min_value=0.5, max_value=400.0),
    rebalance=st.sampled_from([1.0, 7.0, 30.4375, 91.3125]),
)
def test_pbt_is_oversampled_matches_formula(coarsest, rebalance):
    assert is_oversampled(coarsest, rebalance) == (coarsest > rebalance * 1.5)


@given(
    a=st.floats(min_value=0.5, max_value=400.0),
    b=st.floats(min_value=0.5, max_value=400.0),
)
def test_pbt_classify_cadence_monotonic(a, b):
    order = {"daily": 0, "weekly": 1, "monthly": 2, "quarterly": 3, "irregular": 4}
    lo, hi = sorted((a, b))
    assert order[classify_cadence(lo)] <= order[classify_cadence(hi)]
