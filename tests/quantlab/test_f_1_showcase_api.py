"""F-1 showcase read API/dashboard tests.

RED/GREEN/REFACTOR trace:
- RED: this module was added before `quantlab.showcase` exists.
- GREEN: implement the smallest read API/render surface that satisfies F requirements.
- REFACTOR: keep the public payload deterministic while simplifying helpers.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

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
    if metadata is None:
        metadata = {"claim_boundary": "no_alpha_claim"}
    return {
        "run_id": run_id,
        "strategy_name": name,
        "strategy_metadata": metadata,
        "config": {"seed": 7, "data_version": "canonical-showcase-scenario"},
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


def test_showcase_api_rejects_missing_claim_boundary_metadata(tmp_path):
    from quantlab.showcase import ShowcaseReadAPI, build_dashboard_summary
    from quantlab.tracking import LocalResultStore

    store = LocalResultStore(tmp_path / "missing-claim.db")
    run_id = store.log(_record("missing-claim", 0.4, metadata={}))
    api = ShowcaseReadAPI(store)

    with pytest.raises(ValueError, match="claim_boundary"):
        api.leaderboard()
    with pytest.raises(ValueError, match="claim_boundary"):
        build_dashboard_summary(api.run_detail(run_id), [])


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


def test_showcase_api_exposes_e_lite_registry_without_tier3_overclaim(tmp_path):
    from quantlab.mlops import ExperimentRegistry
    from quantlab.showcase import ShowcaseReadAPI, build_dashboard_summary

    store, rid_a, _ = _store(tmp_path)
    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    entry = registry.register(
        "return-risk-forecast",
        "ForecastAllocationStrategy",
        {"lookback": 12, "vol_cap": 0.3},
        run_ids=[rid_a],
        metrics={"oos_net_sharpe": 0.8},
        tags=["D2", "F"],
    )
    api = ShowcaseReadAPI(store, experiment_registry=registry)

    experiments = api.experiments()
    summary = build_dashboard_summary(api.run_detail(rid_a), api.leaderboard(),
                                      experiments=experiments)

    assert experiments == [{
        "experiment_id": entry.experiment_id,
        "model_family": "return-risk-forecast",
        "strategy_name": "ForecastAllocationStrategy",
        "run_ids": [rid_a],
        "claim_boundary": "no_alpha_claim",
        "status": "research_only",
        "readiness": "registry_only",
        "tags": ["D2", "F"],
    }]
    assert summary["experiments"] == experiments
    assert summary["warnings"] == []


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


def test_dashboard_html_rejects_missing_claim_boundary_rows():
    from quantlab.showcase import render_dashboard_html

    summary = {
        "claim_boundary": "no_alpha_claim",
        "leaderboard": [{"strategy_name": "model", "run_id": "r1", "oos_net_sharpe": 0.1}],
        "experiments": [],
        "warnings": [],
    }

    with pytest.raises(ValueError, match="claim_boundary"):
        render_dashboard_html(summary)


def test_canonical_showcase_artifact_uses_result_store_source(tmp_path):
    from quantlab.showcase import build_canonical_dashboard_artifact

    artifact = build_canonical_dashboard_artifact(tmp_path)

    assert artifact["sourceMetadata"] == {
        "source": "local_result_store",
        "sourceRecordCount": 2,
        "experimentRegistry": "experiment_registry",
    }
    assert artifact["activeRunId"] == "forecast-run"
    assert artifact["claimBoundary"] == "no_alpha_claim"
    assert [row["runId"] for row in artifact["leaderboard"]] == [
        "forecast-run",
        "baseline-run",
    ]


def _write_current_evidence_root(root: Path) -> None:
    (root / "docs/review/assets").mkdir(parents=True)
    (root / ".agents/specs/a0-backtest-foundation/reports").mkdir(parents=True)
    (root / ".agents/specs/f-browser-pixel-baseline").mkdir(parents=True)
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs/review/assets/gate-pytest.txt").write_text(
        "253 passed in 20.00s\n",
        encoding="utf-8",
    )
    (root / "docs/review/assets/gate-frontend-test.txt").write_text(
        " Test Files  3 passed (3)\n      Tests  32 passed (32)\n",
        encoding="utf-8",
    )
    (root / "docs/review/assets/gate-frontend-audit.txt").write_text(
        "found 0 vulnerabilities\n",
        encoding="utf-8",
    )
    (root / ".agents/specs/a0-backtest-foundation/reports/mutation-automation-report.md").write_text(
        "Current evidence is **70/70 configured/killed**.\n",
        encoding="utf-8",
    )
    (root / ".agents/specs/f-browser-pixel-baseline/review.md").write_text(
        "- Frontend coverage: **91.05% line coverage**.\n"
        "- Frontend mutation: **15/15 killed**.\n",
        encoding="utf-8",
    )
    (root / "docs/browser-visual-diff.json").write_text(
        json.dumps({
            "artifactKind": "browser_visual_diff",
            "claimBoundary": "no_alpha_claim",
            "status": "passed",
            "mismatchedPixels": 1049,
            "totalPixels": 1296000,
        }),
        encoding="utf-8",
    )
    (root / "docs/public-hosting-probe.json").write_text(
        json.dumps({
            "claimBoundary": "no_alpha_claim",
            "status": "configured_not_observed",
            "hashStatus": "mismatched",
        }),
        encoding="utf-8",
    )


def test_canonical_showcase_artifact_reads_current_evidence_artifacts(tmp_path):
    from quantlab.showcase import build_canonical_dashboard_artifact

    evidence_root = tmp_path / "evidence"
    _write_current_evidence_root(evidence_root)

    artifact = build_canonical_dashboard_artifact(tmp_path / "work", evidence_root=evidence_root)

    assert artifact["evidence"]["tests"] == [
        "253 passed",
        "frontend tests 32 passed",
        "Python mutation 70/70 killed",
        "frontend mutation 15/15 killed",
        "F Next.js coverage 91.05%",
        "frontend audit 0 vulnerabilities",
        "browser visual diff 1049/1296000 passed",
        "public hosting configured_not_observed (hash mismatched)",
    ]


def test_canonical_showcase_artifact_fails_closed_without_evidence_artifacts(tmp_path):
    from quantlab.showcase import build_canonical_dashboard_artifact

    with pytest.raises(FileNotFoundError, match="gate-pytest"):
        build_canonical_dashboard_artifact(tmp_path / "work", evidence_root=tmp_path / "missing")


def test_showcase_api_tests_do_not_reintroduce_retired_fixture_marker():
    """Current F test data must not point future work back to the retired fixture source."""
    test_source = Path(__file__).read_text(encoding="utf-8")
    retired_marker = "showcase" + "-fixture"

    assert retired_marker not in test_source
