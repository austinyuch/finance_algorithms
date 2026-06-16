"""Tests — CR-RDO-005 multi-cycle, multi-asset OOS-net evaluation across D families.

Covers REQ-RDO5-001..005: shared-universe multi-family leaderboard ranked OOS-net
only with the baseline visible, multi-cycle provenance, inherited honesty guards
(sufficiency / sampling-frequency / degeneracy), a checksummed self-validating
artifact, and explicit-overclaim rejection (while accepting a claim-silent dumb
baseline). TDD: authored against the design contract. no_alpha_claim throughout.
"""
from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st

from quantlab.data.provider import InMemoryPITDataProvider
from quantlab.models.return_risk import ForecastAllocationStrategy, ReturnRiskForecaster
from quantlab.models.robust_optimization import RobustOptimizationStrategy, RobustPortfolioModel
from quantlab.research.real_data_oos import SamplingFrequencyError
from quantlab.research import multi_cycle_oos as mco
from quantlab.strategies import BuyAndHold

_FACTORS = [1.03, 0.98, 1.02, 0.97, 1.04, 0.99, 1.01, 0.96]


def _closes(n: int, offset: int) -> list[float]:
    closes, c = [], 100.0 + offset * 11.0
    for i in range(n):
        c *= _FACTORS[(i * (offset + 1)) % len(_FACTORS)]
        closes.append(round(c, 4))
    return closes


def _make_provider(specs, *, flat: bool = False) -> InMemoryPITDataProvider:
    """specs: list of (symbol, start_iso, periods, pandas_freq). approximate availability."""
    prows = []
    for si, (sym, start, n, freq) in enumerate(specs):
        dates = pd.date_range(start, periods=n, freq=freq)
        closes = [100.0] * n if flat else _closes(n, si)
        for d, c in zip(dates, closes):
            prows.append({"symbol": sym, "event_date": d, "available_date": d, "close": c})
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("1990-01-01"),
                              "delist_date": pd.NaT} for s, _, _, _ in specs])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(pd.DataFrame(prows), listings, macro)


_CONFIG = {
    "rebalance": "monthly", "mode": "net", "seed": 0,
    "cost_config": {"commission_bps": 5, "slippage_bps": 5},
    "walk_forward": {"train_window_months": 12, "test_window_months": 6, "step_months": 6},
}


def _families():
    return {
        "return_risk": lambda u: ForecastAllocationStrategy(ReturnRiskForecaster(list(u))),
        "robust": lambda u: RobustOptimizationStrategy(RobustPortfolioModel(list(u))),
    }


def _two_asset_provider():
    # ~7 years of daily data over two assets sharing the full window.
    return _make_provider([
        ("AAA", "2014-01-01", 2600, "D"),
        ("BBB", "2014-01-01", 2600, "D"),
    ])


# --- REQ-RDO5-001: shared-universe multi-family leaderboard -----------------

def test_report_runs_all_families_plus_baseline_on_one_shared_window():
    report = mco.build_multi_cycle_family_oos_report(
        _two_asset_provider(), families=_families(), baseline_build=lambda u: BuyAndHold(list(u)),
        config=_CONFIG, min_assets=2, min_history_months=18.0,
    )
    assert report["status"] == "computed"
    families = {r["model_family"] for r in report["rows"]}
    assert families == {"baseline", "return_risk", "robust"}
    # one shared as-of window for every row
    windows = {(r.get("run_id") is not None) for r in report["rows"]}
    assert windows == {True}
    assert report["asof_window"]["start"] and report["asof_window"]["end"]


def test_rows_sorted_descending_with_baseline_visible():
    report = mco.build_multi_cycle_family_oos_report(
        _two_asset_provider(), families=_families(), baseline_build=lambda u: BuyAndHold(list(u)),
        config=_CONFIG, min_assets=2, min_history_months=18.0,
    )
    sharpes = [r["oos_net_sharpe"] for r in report["rows"]]
    assert sharpes == sorted(sharpes, reverse=True)
    baseline_rows = [r for r in report["rows"] if r["is_baseline"]]
    assert len(baseline_rows) == 1 and baseline_rows[0]["model_family"] == "baseline"
    assert report["baseline_run_ids"] == [baseline_rows[0]["run_id"]]


class _OverclaimStrategy:
    def __init__(self, symbols): self._s = list(symbols)
    def fit(self, train=None, **k): return None
    def generate_signal(self, asof, data=None):
        n = len(self._s); return {s: 1.0 / n for s in self._s}
    @property
    def metadata(self): return {"name": "Overclaim", "framework": "none", "claim_boundary": "alpha"}


def test_explicit_overclaim_record_fails_closed():
    with pytest.raises(ValueError, match="overclaim"):
        mco.build_multi_cycle_family_oos_report(
            _two_asset_provider(),
            families={"bad": lambda u: _OverclaimStrategy(u)},
            baseline_build=lambda u: BuyAndHold(list(u)),
            config=_CONFIG, min_assets=2, min_history_months=18.0,
        )


def test_claim_silent_baseline_is_accepted():
    # BuyAndHold omits claim_boundary entirely; it must NOT be rejected.
    report = mco.build_multi_cycle_family_oos_report(
        _two_asset_provider(), families=_families(), baseline_build=lambda u: BuyAndHold(list(u)),
        config=_CONFIG, min_assets=2, min_history_months=18.0,
    )
    assert any(r["is_baseline"] for r in report["rows"])


def test_empty_families_fails_closed():
    with pytest.raises(ValueError, match="at least one model family"):
        mco.build_multi_cycle_family_oos_report(
            _two_asset_provider(), families={}, baseline_build=lambda u: BuyAndHold(list(u)),
            config=_CONFIG,
        )


# --- REQ-RDO5-002: multi-cycle provenance ------------------------------------

def test_provenance_records_universe_window_and_family_status():
    report = mco.build_multi_cycle_family_oos_report(
        _two_asset_provider(), families=_families(), baseline_build=lambda u: BuyAndHold(list(u)),
        config=_CONFIG, min_assets=2, min_history_months=18.0,
    )
    prov = report["data_provenance"]
    assert set(prov["universe"]) == {"AAA", "BBB"}
    assert prov["availability_mode"] == "approximate_event_date"
    assert prov["overlap_months"] >= 18.0
    assert set(prov["family_status"]) == {"baseline", "return_risk", "robust"}
    assert "sampling_frequency" in prov and "cycles_covered" in prov


def test_cycles_in_window_subset_and_named():
    cycles = mco.cycles_in_window("1995-01-01", "2026-01-01")
    names = {c["name"] for c in cycles}
    assert names == {"dot_com", "gfc", "covid", "rate_shock_2022"}
    # narrow window excludes earlier episodes
    late = {c["name"] for c in mco.cycles_in_window("2010-01-01", "2026-01-01")}
    assert late == {"covid", "rate_shock_2022"}
    assert mco.cycles_in_window(None, "2026-01-01") == ()


# --- REQ-RDO5-003: inherited honesty guards (fail closed) --------------------

def test_insufficient_assets_fails_closed():
    provider = _make_provider([("AAA", "2014-01-01", 2600, "D")])
    with pytest.raises(ValueError, match="insufficient real data"):
        mco.build_multi_cycle_family_oos_report(
            provider, families=_families(), baseline_build=lambda u: BuyAndHold(list(u)),
            config=_CONFIG, min_assets=2, min_history_months=18.0,
        )


def test_window_below_minimum_fails_closed():
    provider = _make_provider([("AAA", "2024-01-01", 120, "D"), ("BBB", "2024-01-01", 120, "D")])
    with pytest.raises(ValueError, match="insufficient real data"):
        mco.build_multi_cycle_family_oos_report(
            provider, families=_families(), baseline_build=lambda u: BuyAndHold(list(u)),
            config=_CONFIG, min_assets=2, min_history_months=240.0,
        )


def test_oversampled_vs_native_cadence_raises():
    # quarterly-native asset under a monthly rebalance -> fabricated flat returns.
    provider = _make_provider([
        ("DLY", "2010-01-01", 4000, "D"),
        ("QTR", "2010-01-01", 64, "QE"),
    ])
    with pytest.raises(SamplingFrequencyError):
        mco.build_multi_cycle_family_oos_report(
            provider, families=_families(), baseline_build=lambda u: BuyAndHold(list(u)),
            config=_CONFIG, min_assets=2, min_history_months=18.0,
        )


def test_degenerate_flat_oos_fails_closed():
    provider = _make_provider([("AAA", "2014-01-01", 2600, "D"),
                               ("BBB", "2014-01-01", 2600, "D")], flat=True)
    with pytest.raises(ValueError, match="degenerate"):
        mco.build_multi_cycle_family_oos_report(
            provider, families=_families(), baseline_build=lambda u: BuyAndHold(list(u)),
            config=_CONFIG, min_assets=2, min_history_months=18.0,
        )


def test_non_net_mode_fails_closed():
    with pytest.raises(ValueError, match="mode=net"):
        mco.build_multi_cycle_family_oos_report(
            _two_asset_provider(), families=_families(),
            baseline_build=lambda u: BuyAndHold(list(u)),
            config={**_CONFIG, "mode": "gross"}, min_assets=2, min_history_months=18.0,
        )


# --- REQ-RDO5-004: checksummed self-validating artifact ----------------------

def _computed_report():
    return mco.build_multi_cycle_family_oos_report(
        _two_asset_provider(), families=_families(), baseline_build=lambda u: BuyAndHold(list(u)),
        config=_CONFIG, min_assets=2, min_history_months=18.0,
    )


def test_artifact_roundtrip_validates():
    art = mco.build_multi_cycle_artifact(_computed_report(),
                                         artifact_uri="file://x.json", generated_at="2026-06-16T00:00:00Z")
    assert art["artifact_kind"] == "multi_cycle_family_oos_artifact"
    assert art["claim_boundary"] == "no_alpha_claim"
    assert art["row_count"] == len(art["report"]["rows"])
    mco.validate_multi_cycle_artifact(art)  # no raise


def test_artifact_rejects_tampered_checksum():
    art = mco.build_multi_cycle_artifact(_computed_report(),
                                         artifact_uri="file://x.json", generated_at="2026-06-16T00:00:00Z")
    art["report"]["rows"][0]["oos_net_sharpe"] += 1.0
    with pytest.raises(ValueError, match="checksum mismatch"):
        mco.validate_multi_cycle_artifact(art)


def test_artifact_rejects_missing_baseline():
    report = _computed_report()
    report["rows"] = [r for r in report["rows"] if not r["is_baseline"]]
    with pytest.raises(ValueError, match="visible baseline"):
        mco.build_multi_cycle_artifact(report, artifact_uri="file://x.json",
                                       generated_at="2026-06-16T00:00:00Z")


def test_artifact_rejects_wrong_claim_boundary():
    report = _computed_report()
    report["claim_boundary"] = "alpha"
    with pytest.raises(ValueError, match="no_alpha_claim"):
        mco.build_multi_cycle_artifact(report, artifact_uri="file://x.json",
                                       generated_at="2026-06-16T00:00:00Z")


def test_insufficient_artifact_has_no_rows(tmp_path):
    provider = _make_provider([("AAA", "2024-01-01", 60, "D"), ("BBB", "2024-01-01", 60, "D")])
    from quantlab.research.real_data_oos import assess_data_sufficiency
    suff = assess_data_sufficiency(provider, min_assets=2, min_history_months=240.0)
    report = mco.build_multi_cycle_insufficient_report(suff, config=_CONFIG)
    art = mco.build_multi_cycle_artifact(report, artifact_uri="file://x.json",
                                         generated_at="2026-06-16T00:00:00Z")
    assert art["status"] == "insufficient_data" and art["row_count"] == 0
    path = mco.write_multi_cycle_artifact(art, tmp_path / "a.json")
    assert path.exists()


def test_row_count_mismatch_rejected():
    art = mco.build_multi_cycle_artifact(_computed_report(),
                                         artifact_uri="file://x.json", generated_at="2026-06-16T00:00:00Z")
    art["row_count"] = 999
    with pytest.raises(ValueError, match="row_count mismatch"):
        mco.validate_multi_cycle_artifact(art)


# --- Property-based -----------------------------------------------------------

@given(
    lo_year=st.integers(min_value=1990, max_value=2026),
    span_years=st.integers(min_value=0, max_value=40),
)
@settings(max_examples=60, deadline=None)
def test_pbt_cycles_subset_and_window_monotone(lo_year, span_years):
    start = f"{lo_year}-01-01"
    end = f"{min(lo_year + span_years, 2030)}-12-31"
    cycles = mco.cycles_in_window(start, end)
    names = [c["name"] for c in cycles]
    canonical = [n for n, _ in mco.CANONICAL_CYCLES]
    assert set(names) <= set(canonical)
    # widening the window can only add (monotone) episodes
    wider = mco.cycles_in_window(start, "2030-12-31")
    assert set(names) <= {c["name"] for c in wider}


@given(perm=st.permutations(list(range(5))))
@settings(max_examples=40, deadline=None)
def test_pbt_checksum_invariant_under_key_reorder(perm):
    report = _computed_report()
    art1 = mco.build_multi_cycle_artifact(dict(report), artifact_uri="file://x", generated_at="t")
    # reorder report dict keys; canonical JSON must yield the same checksum
    items = list(report.items())
    reordered = {items[i][0]: items[i][1] for i in perm if i < len(items)}
    reordered.update(report)
    art2 = mco.build_multi_cycle_artifact(reordered, artifact_uri="file://x", generated_at="t")
    assert art1["checksum"] == art2["checksum"]


# --- Chaos --------------------------------------------------------------------

def test_chaos_empty_provider_fails_closed_not_crash():
    empty = InMemoryPITDataProvider(
        pd.DataFrame(columns=["symbol", "event_date", "available_date", "close"]),
        pd.DataFrame(columns=["symbol", "list_date", "delist_date"]),
        pd.DataFrame(columns=["series", "event_date", "available_date", "value"]),
    )
    with pytest.raises(ValueError):
        mco.build_multi_cycle_family_oos_report(
            empty, families=_families(), baseline_build=lambda u: BuyAndHold(list(u)),
            config=_CONFIG, min_assets=2, min_history_months=18.0,
        )


def test_chaos_nan_closes_do_not_crash():
    provider = _make_provider([("AAA", "2014-01-01", 2600, "D"), ("BBB", "2014-01-01", 2600, "D")])
    provider._prices.loc[provider._prices["symbol"] == "AAA", "close"] = float("nan")
    # NaN-heavy series should fail closed (degenerate / insufficient), never crash uncaught.
    with pytest.raises((ValueError, SamplingFrequencyError)):
        mco.build_multi_cycle_family_oos_report(
            provider, families=_families(), baseline_build=lambda u: BuyAndHold(list(u)),
            config=_CONFIG, min_assets=2, min_history_months=18.0,
        )


def test_chaos_regime_degraded_when_macro_missing_does_not_crash():
    # regime price-trend-only mode: no T10Y2Y macro present (mirrors CR-B21 residual).
    from quantlab.models.regime import FirstRegimeClassifier, RegimeAllocationStrategy
    provider = _two_asset_provider()

    def regime_factory(u):
        return RegimeAllocationStrategy(
            FirstRegimeClassifier(price_symbol=u[0]),
            risk_on_weights={u[-1]: 1.0}, defensive_weights={u[0]: 1.0},
        )

    report = mco.build_multi_cycle_family_oos_report(
        provider, families={"regime": regime_factory},
        baseline_build=lambda u: BuyAndHold(list(u)),
        config=_CONFIG, min_assets=2, min_history_months=18.0,
    )
    status = report["data_provenance"]["family_status"]["regime"]
    assert status["name"] == "RegimeAllocationStrategy"
