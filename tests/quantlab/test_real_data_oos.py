"""Tests — Real-data >=2-asset OOS-net backtest slice (spec: real-data-oos-backtest).

Covers REQ-RDO-001 (real OOS-net comparison + ranking), REQ-RDO-002 (PIT /
survivorship / net!=gross under cost), REQ-RDO-003 (fail-closed insufficient_data
+ no_alpha_claim). TDD: authored before the module exists.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from quantlab.data.provider import InMemoryPITDataProvider
from quantlab.engine import VectorizedEngine
from quantlab.research.real_data_oos import (
    assess_data_sufficiency,
    build_insufficient_data_report,
    build_real_data_oos_artifact,
    build_real_data_oos_report,
    validate_real_data_oos_artifact,
    write_real_data_oos_artifact,
)
from quantlab.strategies import BuyAndHold, RandomStrategy

_FACTORS = [1.03, 0.98, 1.02, 0.97, 1.04, 0.99]


def _close_path(n: int, offset: int) -> list[float]:
    closes, c = [], 100.0 + offset * 7.0
    for i in range(n):
        c *= _FACTORS[(i + offset) % len(_FACTORS)]
        closes.append(round(c, 4))
    return closes


def _make_provider(symbols, *, n_months=24, start="2023-01-31",
                   delistings=None, late_revision=None) -> InMemoryPITDataProvider:
    dates = pd.date_range(start, periods=n_months, freq="ME")
    prows = []
    for si, sym in enumerate(symbols):
        for d, c in zip(dates, _close_path(n_months, si)):
            prows.append({"symbol": sym, "event_date": d, "available_date": d, "close": c})
    if late_revision is not None:
        # A revision for an *in-window* event_date that only becomes available
        # long after the backtest window: at every asof <= window end its
        # available_date > asof, so a PIT-safe path must ignore it (no lookahead).
        sym, close = late_revision
        future_avail = dates[-1] + pd.DateOffset(months=12)
        prows.append({"symbol": sym, "event_date": dates[0], "available_date": future_avail,
                      "close": close})
    prices = pd.DataFrame(prows)
    lrows = []
    for sym in symbols:
        delist = pd.Timestamp(delistings[sym]) if (delistings and sym in delistings) else pd.NaT
        lrows.append({"symbol": sym, "list_date": pd.Timestamp(start) - pd.DateOffset(years=1),
                      "delist_date": delist})
    listings = pd.DataFrame(lrows)
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro)


def _cfg(*, cost=True, mode="net") -> dict:
    cc = {"commission_bps": 10, "slippage_bps": 5, "tw_transaction_tax_bps": 0,
          "us_dividend_withholding_pct": 0, "fx_spread_bps": 0} if cost else {}
    return {"rebalance": "monthly", "mode": mode, "cost_config": cc,
            "walk_forward": {"train_window_months": 12, "test_window_months": 6, "step_months": 6}}


# --- REQ-RDO-003: data sufficiency gating ---

def test_sufficiency_two_assets_enough_history_is_ok():
    suff = assess_data_sufficiency(_make_provider(["AAA", "BBB"], n_months=24))
    assert suff.sufficient is True
    assert suff.reason == "ok"
    assert suff.asset_count == 2
    assert suff.history_span_months >= 18.0


def test_sufficiency_single_asset_fails_closed():
    suff = assess_data_sufficiency(_make_provider(["AAA"], n_months=24))
    assert suff.sufficient is False
    assert suff.reason == "fewer_than_min_assets"


def test_sufficiency_thin_history_fails_closed():
    suff = assess_data_sufficiency(_make_provider(["AAA", "BBB"], n_months=3))
    assert suff.sufficient is False
    assert suff.reason == "history_below_min_window"


# --- REQ-RDO-001: real OOS-net comparison + ranking, baseline visible ---

def test_report_ranks_oos_net_desc_with_baseline_visible():
    provider = _make_provider(["AAA", "BBB"], n_months=24)
    universe = ["AAA", "BBB"]
    report = build_real_data_oos_report(
        provider,
        candidate=RandomStrategy(universe, seed=0),
        baseline=BuyAndHold(universe),
        config=_cfg(),
    )
    assert report["status"] == "computed"
    assert report["claim_boundary"] == "no_alpha_claim"
    assert report["metric_authority"] == "out_of_sample_net_only"
    rows = report["rows"]
    assert len(rows) == 2
    sharpes = [r["oos_net_sharpe"] for r in rows]
    assert sharpes == sorted(sharpes, reverse=True)        # ranked OOS-net desc
    assert any(r["is_baseline"] for r in rows)              # baseline visible
    assert set(report["asset_set"]) == {"AAA", "BBB"}
    assert report["data_provenance"]["asset_count"] == 2
    assert report["asof_window"]["start"] and report["asof_window"]["end"]


def test_report_oos_net_sharpe_uses_out_of_sample_not_in_sample():
    # Pins the OOS-net extraction segment: flipping out_of_sample -> in_sample
    # must change the reported value (kills the segment mutation).
    provider = _make_provider(["AAA", "BBB"], n_months=24)
    universe = ["AAA", "BBB"]
    cfg = _cfg()
    report = build_real_data_oos_report(provider, candidate=RandomStrategy(universe, seed=0),
                                        baseline=BuyAndHold(universe), config=cfg)
    cand_row = next(r for r in report["rows"] if not r["is_baseline"])
    span = provider._prices["event_date"]
    res = VectorizedEngine().run(
        RandomStrategy(universe, seed=0), provider,
        {"start": str(span.min().date()), "end": str(span.max().date()), "rebalance": "monthly",
         "mode": "net", "cost_config": cfg["cost_config"], "walk_forward": cfg["walk_forward"]},
    )
    oos = next(m["sharpe"] for m in res["metrics"]
               if m["segment"] == "out_of_sample" and m["basis"] == "net")
    in_sample = next(m["sharpe"] for m in res["metrics"]
                     if m["segment"] == "in_sample" and m["basis"] == "net")
    assert cand_row["oos_net_sharpe"] == oos
    assert oos != in_sample


def test_report_provenance_records_survivorship_safe_universe():
    # REQ-RDO-002 AC2: a security that delists *after* the window stays in the
    # as-of universe during its listed life.
    provider = _make_provider(["AAA", "BBB"], n_months=24, delistings={"BBB": "2099-01-01"})
    report = build_real_data_oos_report(
        provider, candidate=RandomStrategy(["AAA", "BBB"], seed=1),
        baseline=BuyAndHold(["AAA", "BBB"]), config=_cfg(),
    )
    assert "BBB" in report["data_provenance"]["universe_asof"]


# --- REQ-RDO-002: PIT no-lookahead + net != gross under cost ---

def test_future_revision_does_not_change_oos_output():
    base = _make_provider(["AAA", "BBB"], n_months=24)
    leaky = _make_provider(["AAA", "BBB"], n_months=24,
                           late_revision=("AAA", 99999.0))  # revision available only post-window
    cfg = _cfg()
    r_base = build_real_data_oos_report(base, candidate=RandomStrategy(["AAA", "BBB"], seed=0),
                                        baseline=BuyAndHold(["AAA", "BBB"]), config=cfg)
    r_leaky = build_real_data_oos_report(leaky, candidate=RandomStrategy(["AAA", "BBB"], seed=0),
                                         baseline=BuyAndHold(["AAA", "BBB"]), config=cfg)
    assert r_base["rows"] == r_leaky["rows"]                # no lookahead leakage


def test_net_differs_from_gross_under_nonzero_cost():
    provider = _make_provider(["AAA", "BBB"], n_months=24)
    universe = ["AAA", "BBB"]
    span = provider._prices["event_date"]
    base_cfg = {"start": str(span.min().date()), "end": str(span.max().date()),
                "rebalance": "monthly",
                "walk_forward": {"train_window_months": 12, "test_window_months": 6, "step_months": 6}}

    def _oos(mode):
        res = VectorizedEngine().run(RandomStrategy(universe, seed=3), provider,
                                     {**base_cfg, "mode": mode,
                                      "cost_config": {"commission_bps": 25, "slippage_bps": 10}})
        return next(m["sharpe"] for m in res["metrics"]
                    if m["segment"] == "out_of_sample" and m["basis"] == mode)

    assert _oos("net") != _oos("gross")


# --- artifact build / validate / write ---

def test_artifact_checksum_roundtrip_and_write(tmp_path: Path):
    provider = _make_provider(["AAA", "BBB"], n_months=24)
    report = build_real_data_oos_report(provider, candidate=RandomStrategy(["AAA", "BBB"], seed=0),
                                        baseline=BuyAndHold(["AAA", "BBB"]), config=_cfg())
    art = build_real_data_oos_artifact(report, artifact_uri="file://run.json",
                                       generated_at="2026-06-13T00:00:00Z")
    validate_real_data_oos_artifact(art)                   # no raise
    assert art["artifact_kind"] == "real_data_oos_backtest_artifact"
    assert art["status"] == "computed"
    assert art["row_count"] == len(report["rows"])
    out = write_real_data_oos_artifact(art, tmp_path / "art.json")
    assert out.exists()


def test_validate_rejects_tampered_checksum():
    provider = _make_provider(["AAA", "BBB"], n_months=24)
    report = build_real_data_oos_report(provider, candidate=RandomStrategy(["AAA", "BBB"], seed=0),
                                        baseline=BuyAndHold(["AAA", "BBB"]), config=_cfg())
    art = dict(build_real_data_oos_artifact(report, artifact_uri="u", generated_at="t"))
    art["checksum"] = "0" * 64
    with pytest.raises(ValueError):
        validate_real_data_oos_artifact(art)


def test_validate_rejects_computed_without_visible_baseline():
    provider = _make_provider(["AAA", "BBB"], n_months=24)
    report = build_real_data_oos_report(provider, candidate=RandomStrategy(["AAA", "BBB"], seed=0),
                                        baseline=BuyAndHold(["AAA", "BBB"]), config=_cfg())
    report["rows"] = [{**r, "is_baseline": False} for r in report["rows"]]
    with pytest.raises(ValueError):
        build_real_data_oos_artifact(report, artifact_uri="u", generated_at="t")


# --- REQ-RDO-003: insufficient artifact ---

def test_insufficient_artifact_has_empty_rows_and_claim_boundary():
    suff = assess_data_sufficiency(_make_provider(["AAA"], n_months=24))
    report = build_insufficient_data_report(suff)
    art = build_real_data_oos_artifact(report, artifact_uri="u", generated_at="t")
    validate_real_data_oos_artifact(art)
    assert art["status"] == "insufficient_data"
    assert art["row_count"] == 0
    assert art["claim_boundary"] == "no_alpha_claim"


# --- PBT ---

# --- builder / validator guard branches + injected store + config window ---

def test_report_with_store_logs_and_marks_baseline(tmp_path: Path):
    from quantlab.tracking import LocalResultStore

    provider = _make_provider(["AAA", "BBB"], n_months=24)
    with LocalResultStore(tmp_path / "runs.db") as store:
        report = build_real_data_oos_report(
            provider, candidate=RandomStrategy(["AAA", "BBB"], seed=0),
            baseline=BuyAndHold(["AAA", "BBB"]), config=_cfg(), store=store,
        )
        leaderboard = store.leaderboard()
    assert report["status"] == "computed"
    assert len(leaderboard) == 2
    assert any(row["is_baseline"] for row in leaderboard)


def test_report_honours_explicit_config_window():
    provider = _make_provider(["AAA", "BBB"], n_months=24)
    report = build_real_data_oos_report(
        provider, candidate=RandomStrategy(["AAA", "BBB"], seed=0),
        baseline=BuyAndHold(["AAA", "BBB"]),
        config={**_cfg(), "start": "2023-06-30", "end": "2024-12-31"},
    )
    assert report["asof_window"] == {"start": "2023-06-30", "end": "2024-12-31"}


def test_report_requires_sufficient_data():
    with pytest.raises(ValueError, match="insufficient"):
        build_real_data_oos_report(_make_provider(["AAA"], n_months=24),
                                   candidate=BuyAndHold(["AAA"]), baseline=BuyAndHold(["AAA"]),
                                   config=_cfg())


def test_report_requires_mode_net():
    with pytest.raises(ValueError, match="mode=net"):
        build_real_data_oos_report(_make_provider(["AAA", "BBB"], n_months=24),
                                   candidate=RandomStrategy(["AAA", "BBB"], seed=0),
                                   baseline=BuyAndHold(["AAA", "BBB"]), config=_cfg(mode="gross"))


def test_report_requires_out_of_sample_segment():
    cfg = _cfg()
    cfg.pop("walk_forward")  # no OOS segment -> OOS-net Sharpe missing
    with pytest.raises(ValueError, match="out_of_sample net Sharpe"):
        build_real_data_oos_report(_make_provider(["AAA", "BBB"], n_months=24),
                                   candidate=RandomStrategy(["AAA", "BBB"], seed=0),
                                   baseline=BuyAndHold(["AAA", "BBB"]), config=cfg)


def _good_report():
    provider = _make_provider(["AAA", "BBB"], n_months=24)
    return build_real_data_oos_report(provider, candidate=RandomStrategy(["AAA", "BBB"], seed=0),
                                      baseline=BuyAndHold(["AAA", "BBB"]), config=_cfg())


@pytest.mark.parametrize("mutate, match", [
    (lambda r: {**r, "status": "bogus"}, "unknown real-data OOS report status"),
    (lambda r: {**r, "claim_boundary": "alpha!"}, "no_alpha_claim"),
    (lambda r: {**r, "metric_authority": "anything"}, "out_of_sample_net_only"),
    (lambda r: {**r, "rows": "notalist"}, "rows list"),
    (lambda r: {**r, "rows": []}, "requires rows"),
])
def test_build_artifact_rejects_bad_report(mutate, match):
    with pytest.raises(ValueError, match=match):
        build_real_data_oos_artifact(mutate(_good_report()), artifact_uri="u", generated_at="t")


def test_build_artifact_requires_uri_and_generated_at():
    with pytest.raises(ValueError, match="artifact_uri and generated_at"):
        build_real_data_oos_artifact(_good_report(), artifact_uri="  ", generated_at="t")


def test_build_insufficient_rejects_rows():
    suff = assess_data_sufficiency(_make_provider(["AAA"], n_months=24))
    report = {**build_insufficient_data_report(suff), "rows": [{"is_baseline": True}]}
    with pytest.raises(ValueError, match="must not carry comparison rows"):
        build_real_data_oos_artifact(report, artifact_uri="u", generated_at="t")


@pytest.mark.parametrize("mutate, match", [
    (lambda a: {**a, "artifact_kind": "x"}, "unknown real-data OOS"),
    (lambda a: {**a, "status": "x"}, "unknown status"),
    (lambda a: {**a, "claim_boundary": "x"}, "no_alpha_claim"),
    (lambda a: {**a, "metric_authority": "x"}, "out_of_sample_net_only"),
    (lambda a: {**a, "report": "x"}, "requires report"),
    (lambda a: {**a, "row_count": 99}, "row_count mismatch"),
])
def test_validate_artifact_rejects_tampering(mutate, match):
    art = build_real_data_oos_artifact(_good_report(), artifact_uri="u", generated_at="t")
    with pytest.raises(ValueError, match=match):
        validate_real_data_oos_artifact(mutate(art))


@given(asset_count=st.integers(min_value=2, max_value=4),
       n_months=st.integers(min_value=20, max_value=36))
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_pbt_sufficiency_true_for_valid_panels(asset_count, n_months):
    syms = [f"S{i}" for i in range(asset_count)]
    suff = assess_data_sufficiency(_make_provider(syms, n_months=n_months))
    assert suff.sufficient is True
    assert suff.asset_count == asset_count


@given(extra=st.dictionaries(st.text(min_size=1, max_size=4), st.integers(), max_size=4))
@settings(max_examples=25, deadline=None)
def test_pbt_artifact_checksum_canonicalization_invariant(extra):
    provider = _make_provider(["AAA", "BBB"], n_months=24)
    report = build_real_data_oos_report(provider, candidate=RandomStrategy(["AAA", "BBB"], seed=0),
                                        baseline=BuyAndHold(["AAA", "BBB"]), config=_cfg())
    a1 = build_real_data_oos_artifact(report, artifact_uri="u", generated_at="t")
    # reorder report keys: checksum must be identical (canonical sort_keys)
    reordered = dict(reversed(list(report.items())))
    a2 = build_real_data_oos_artifact(reordered, artifact_uri="u", generated_at="t")
    assert a1["checksum"] == a2["checksum"]
