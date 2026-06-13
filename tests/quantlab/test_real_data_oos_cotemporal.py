"""Tests — CR-RDO-001 co-temporal universe + density-aware sufficiency.

Covers REQ-RDO-CR1-001/002/003: overlap-aware sufficiency, co-temporal universe
selection (degenerate long+short mix rejected; overlapping subset chosen), and
preserved no_alpha_claim / read-only boundary. TDD: authored before the change.
"""
from __future__ import annotations

import pandas as pd
import pytest

from quantlab.data.provider import InMemoryPITDataProvider
from quantlab.research.real_data_oos import (
    assess_data_sufficiency,
    build_real_data_oos_report,
    resolve_cotemporal_universe,
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
    """specs: list of (symbol, start_iso, n_months) — per-asset date ranges differ."""
    prows = []
    for si, (sym, start, n) in enumerate(specs):
        dates = pd.date_range(start, periods=n, freq="ME")
        for d, c in zip(dates, _closes(n, si)):
            prows.append({"symbol": sym, "event_date": d, "available_date": d, "close": c})
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("1990-01-01"),
                              "delist_date": pd.NaT} for s, _, _ in specs])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(pd.DataFrame(prows), listings, macro)


def _cfg() -> dict:
    return {"rebalance": "monthly", "mode": "net",
            "cost_config": {"commission_bps": 10, "slippage_bps": 5},
            "walk_forward": {"train_window_months": 12, "test_window_months": 6, "step_months": 6}}


# --- REQ-RDO-CR1-002: resolver ---

def test_resolver_picks_overlapping_subset_excludes_short_asset():
    provider = _make_provider([
        ("LONGA", "2010-01-31", 180),   # 15y
        ("LONGB", "2011-01-31", 168),   # overlaps LONGA for ~14y
        ("SHORT", "2026-01-31", 4),     # recent only, no long overlap
    ])
    assets, start, end = resolve_cotemporal_universe(provider, min_history_months=18.0, min_assets=2)
    assert set(assets) == {"LONGA", "LONGB"}
    assert "SHORT" not in assets
    assert start and end


def test_resolver_empty_when_no_pair_overlaps():
    provider = _make_provider([
        ("A", "2018-01-31", 12),
        ("B", "2023-01-31", 12),        # disjoint from A
    ])
    assets, start, end = resolve_cotemporal_universe(provider, min_history_months=18.0, min_assets=2)
    assert assets == ()
    assert start is None and end is None


# --- REQ-RDO-CR1-001: overlap-aware sufficiency ---

def test_sufficiency_ok_records_overlap_window():
    provider = _make_provider([("LONGA", "2010-01-31", 180), ("LONGB", "2010-01-31", 180)])
    suff = assess_data_sufficiency(provider, min_history_months=18.0)
    assert suff.sufficient is True
    assert suff.reason == "ok"
    assert set(suff.cotemporal_universe) == {"LONGA", "LONGB"}
    assert suff.overlap_months >= 18.0
    assert suff.overlap_start and suff.overlap_end


def test_sufficiency_disjoint_assets_no_cotemporal_overlap():
    provider = _make_provider([("A", "2018-01-31", 12), ("B", "2023-01-31", 12)])
    suff = assess_data_sufficiency(provider, min_history_months=18.0)
    assert suff.sufficient is False
    assert suff.reason == "no_cotemporal_overlap"


def test_sufficiency_thin_but_overlapping_is_history_below_window():
    # preserved reason: assets overlap but the shared window is < min
    provider = _make_provider([("A", "2026-01-31", 3), ("B", "2026-01-31", 3)])
    suff = assess_data_sufficiency(provider, min_history_months=18.0)
    assert suff.sufficient is False
    assert suff.reason == "history_below_min_window"


def test_sufficiency_single_asset_still_fewer_than_min():
    provider = _make_provider([("A", "2010-01-31", 180)])
    suff = assess_data_sufficiency(provider, min_history_months=18.0)
    assert suff.sufficient is False
    assert suff.reason == "fewer_than_min_assets"


# --- REQ-RDO-CR1-002/003: report uses co-temporal universe ---

def test_report_uses_cotemporal_universe_and_is_non_degenerate():
    provider = _make_provider([
        ("LONGA", "2010-01-31", 180),
        ("LONGB", "2010-01-31", 180),
        ("SHORT", "2026-01-31", 4),
    ])
    universe = list(resolve_cotemporal_universe(provider, min_history_months=18.0, min_assets=2)[0])
    report = build_real_data_oos_report(
        provider, candidate=RandomStrategy(universe, seed=0),
        baseline=BuyAndHold(universe), config=_cfg(),
    )
    assert set(report["asset_set"]) == {"LONGA", "LONGB"}
    assert "SHORT" not in report["asset_set"]
    assert set(report["data_provenance"]["cotemporal_universe"]) == {"LONGA", "LONGB"}
    assert report["claim_boundary"] == "no_alpha_claim"
    # baseline OOS-net is finite and both strategies present (non-degenerate)
    assert len(report["rows"]) == 2
    assert all(isinstance(r["oos_net_sharpe"], float) for r in report["rows"])


def test_report_fails_closed_when_no_cotemporal_overlap():
    provider = _make_provider([("A", "2018-01-31", 12), ("B", "2023-01-31", 12)])
    with pytest.raises(ValueError, match="insufficient"):
        build_real_data_oos_report(provider, candidate=BuyAndHold(["A", "B"]),
                                   baseline=BuyAndHold(["A", "B"]), config=_cfg())
