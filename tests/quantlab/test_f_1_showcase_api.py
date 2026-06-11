"""F-1 showcase read API/dashboard tests.

RED/GREEN/REFACTOR trace:
- RED: this module was added before `quantlab.showcase` exists.
- GREEN: implement the smallest read API/render surface that satisfies F requirements.
- REFACTOR: keep the public payload deterministic while simplifying helpers.
"""
from __future__ import annotations

from copy import deepcopy

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


def _metric(sharpe: float) -> dict:
    return {
        "cumulative_return": 0.1,
        "annualized_return": 0.05,
        "annualized_vol": 0.2,
        "max_drawdown": -0.1,
        "sharpe": sharpe,
        "turnover": 1.0,
        "basis": "net",
        "segment": "out_of_sample",
    }


def _record(name: str, sharpe: float, *, run_id: str = "", baseline: bool = False,
            metadata: dict | None = None) -> dict:
    return {
        "run_id": run_id,
        "strategy_name": name,
        "strategy_metadata": metadata or {},
        "config": {"seed": 7, "data_version": "showcase-fixture"},
        "rebalance_dates": ["2022-01-31", "2022-02-28"],
        "metrics": [_metric(sharpe)],
        "is_baseline": baseline,
    }


def _store(tmp_path):
    from quantlab.tracking import LocalResultStore

    store = LocalResultStore(tmp_path / "showcase.db")
    rid_a = store.log(_record("model", 0.8, metadata={
        "last_regime": "risk_on",
        "last_regime_confidence": 0.6,
        "weights": {"SP500": 0.7, "BOND": 0.3},
        "claim_boundary": "no_alpha_claim",
    }))
    rid_b = store.log(_record("baseline", 0.2, baseline=True))
    return store, rid_a, rid_b


def test_showcase_api_returns_sorted_leaderboard_and_run_detail(tmp_path):
    from quantlab.showcase import ShowcaseReadAPI

    store, rid_a, _ = _store(tmp_path)
    api = ShowcaseReadAPI(store)

    board = api.leaderboard()
    assert [row["strategy_name"] for row in board] == ["model", "baseline"]
    assert [row["oos_net_sharpe"] for row in board] == [0.8, 0.2]
    assert all(row["claim_boundary"] == "no_alpha_claim" for row in board)
    assert api.run_detail(rid_a)["run_id"] == rid_a

    with pytest.raises(KeyError):
        api.run_detail("missing-run")


def test_dashboard_summary_conservative_defaults_and_no_mutation(tmp_path):
    from quantlab.showcase import ShowcaseReadAPI, build_dashboard_summary

    store, _, rid_b = _store(tmp_path)
    api = ShowcaseReadAPI(store)
    source = api.run_detail(rid_b)
    before = deepcopy(source)

    summary = build_dashboard_summary(source, api.leaderboard())

    assert source == before
    assert summary["active_run_id"] == rid_b
    assert summary["regime"]["label"] == "unknown"
    assert summary["regime"]["confidence"] == 0.0
    assert summary["claim_boundary"] == "no_alpha_claim"
    assert summary["warnings"] == ["missing_regime_metadata"]


@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(scores=st.lists(st.floats(min_value=-5, max_value=5, allow_nan=False,
                                 allow_infinity=False), min_size=1, max_size=12))
def test_pbt_dashboard_preserves_leaderboard_order(tmp_path, scores):
    from quantlab.showcase import ShowcaseReadAPI, build_dashboard_summary
    from quantlab.tracking import LocalResultStore

    store = LocalResultStore(tmp_path / "pbt.db")
    for i, score in enumerate(scores):
        store.log(_record(f"run-{i}", float(score)))

    api = ShowcaseReadAPI(store)
    board = api.leaderboard()
    summary = build_dashboard_summary(api.run_detail(board[0]["run_id"]), board)

    assert summary["leaderboard"] == board
    extracted = [row["oos_net_sharpe"] for row in summary["leaderboard"]]
    assert extracted == sorted(extracted, reverse=True)


def test_dashboard_html_smoke_contains_sections_and_warning(tmp_path):
    from quantlab.showcase import ShowcaseReadAPI, build_dashboard_summary, render_dashboard_html

    store, _, rid_b = _store(tmp_path)
    api = ShowcaseReadAPI(store)
    summary = build_dashboard_summary(api.run_detail(rid_b), api.leaderboard())

    html = render_dashboard_html(summary)

    assert "<section id=\"leaderboard\">" in html
    assert "<section id=\"allocation-regime\">" in html
    assert "<section id=\"rebalance\">" in html
    assert "<section id=\"evidence\">" in html
    assert "missing_regime_metadata" in html
    assert "no_alpha_claim" in html
