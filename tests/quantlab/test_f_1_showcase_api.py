"""F-1 showcase read API/dashboard tests.

RED/GREEN/REFACTOR trace:
- RED: this module was added before `quantlab.showcase` exists.
- GREEN: implement the smallest read API/render surface that satisfies F requirements.
- REFACTOR: keep the public payload deterministic while simplifying helpers.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
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
    assert "frontend mutation 26/26 killed" in artifact["evidence"]["tests"]
    assert "frontend mutation 21/21 killed" not in artifact["evidence"]["tests"]
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
        "288 passed in 20.00s\n",
        encoding="utf-8",
    )
    (root / "docs/review/assets/gate-frontend-test.txt").write_text(
        " Test Files  6 passed (6)\n      Tests  44 passed (44)\n",
        encoding="utf-8",
    )
    (root / "docs/review/assets/gate-frontend-audit.txt").write_text(
        "found 0 vulnerabilities\n",
        encoding="utf-8",
    )
    (root / ".agents/specs/a0-backtest-foundation/reports/mutation-automation-report.md").write_text(
        "Current evidence is **100/100 configured/killed**.\n",
        encoding="utf-8",
    )
    (root / ".agents/specs/f-browser-pixel-baseline/review.md").write_text(
        "- Frontend coverage: **89.85% line coverage**.\n"
        "- Frontend mutation: **26/26 killed**.\n",
        encoding="utf-8",
    )
    (root / "docs/browser-visual-diff.json").write_text(
        json.dumps({
            "artifactKind": "browser_visual_diff",
            "claimBoundary": "no_alpha_claim",
            "status": "passed",
            "mismatchedPixels": 86,
            "totalPixels": 1296000,
            "mismatchRatio": 86 / 1296000,
            "maxMismatchRatio": 0.001,
        }),
        encoding="utf-8",
    )
    (root / "docs/public-hosting-probe.json").write_text(
        json.dumps({
            "claimBoundary": "no_alpha_claim",
            "status": "configured_not_observed",
            "targetUrl": "https://austinyuch.github.io/finance_algorithms/",
            "httpStatus": 200,
            "deployedManifestStatus": 200,
            "manifestContractStatus": "matched",
            "freshnessStatus": "fresh",
            "maxAgeHours": 24,
            "observedAt": "2026-06-13T07:24:50.456Z",
            "hashStatus": "mismatched",
            "deployedDataHash": "old",
            "expectedDataHash": "new",
        }),
        encoding="utf-8",
    )


def test_canonical_showcase_artifact_reads_current_evidence_artifacts(tmp_path):
    from quantlab.showcase import build_canonical_dashboard_artifact
    from quantlab.showcase.scenario import write_canonical_dashboard_artifact

    evidence_root = tmp_path / "evidence"
    _write_current_evidence_root(evidence_root)
    # Fixed asof within the fixture observedAt window keeps this exact-string
    # assertion deterministic (CR-FPS-011 freshness is asof-relative).
    fixture_asof = datetime(2026, 6, 13, 8, 0, 0, tzinfo=timezone.utc)

    artifact = build_canonical_dashboard_artifact(
        tmp_path / "work", evidence_root=evidence_root, asof=fixture_asof
    )

    assert artifact["demoReadiness"]["publicHosting"] == "not_proven"
    assert artifact["demoReadiness"]["visualRegression"] == "proven"
    assert artifact["evidence"]["tests"] == [
        "288 passed",
        "frontend tests 44 passed",
        "Python mutation 100/100 killed",
        "frontend mutation 26/26 killed",
        "F Next.js coverage 89.85%",
        "frontend audit 0 vulnerabilities",
        "browser visual diff passed",
        "public hosting configured_not_observed (hash mismatched)",
    ]

    output = tmp_path / "dashboard" / "showcase.json"
    written = write_canonical_dashboard_artifact(
        output,
        tmp_path / "write-work",
        evidence_root=evidence_root,
        asof=fixture_asof,
    )
    assert written == json.loads(output.read_text(encoding="utf-8"))
    assert written["demoReadiness"]["visualRegression"] == "proven"


def test_canonical_showcase_artifact_surfaces_real_data_section(tmp_path):
    from quantlab.showcase import build_canonical_dashboard_artifact

    repo_root = Path(__file__).resolve().parents[2]
    artifact = build_canonical_dashboard_artifact(tmp_path / "work", evidence_root=repo_root)
    real = artifact.get("realData")
    assert real is not None
    assert real["source"] == "real_data_oos_backtest_artifact"
    assert real["status"] == "computed"
    assert real["claimBoundary"] == "no_alpha_claim"
    assert len(real["rows"]) >= 2
    assert any(row["isBaseline"] for row in real["rows"])
    sharpes = [row["oosNetSharpe"] for row in real["rows"]]
    assert sharpes == sorted(sharpes, reverse=True)


def test_canonical_showcase_artifact_omits_real_data_without_evidence_root(tmp_path):
    from quantlab.showcase import build_canonical_dashboard_artifact

    artifact = build_canonical_dashboard_artifact(tmp_path / "work")
    assert "realData" not in artifact


def test_canonical_showcase_artifact_rejects_failed_frontend_transcript(tmp_path):
    from quantlab.showcase import build_canonical_dashboard_artifact

    evidence_root = tmp_path / "evidence"
    _write_current_evidence_root(evidence_root)
    (evidence_root / "docs/review/assets/gate-frontend-test.txt").write_text(
        " Test Files  1 failed | 3 passed (4)\n      Tests  1 failed | 35 passed (36)\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="frontend test evidence includes failures"):
        build_canonical_dashboard_artifact(tmp_path / "work", evidence_root=evidence_root)

    pytest_evidence_root = tmp_path / "pytest-evidence"
    _write_current_evidence_root(pytest_evidence_root)
    (pytest_evidence_root / "docs/review/assets/gate-pytest.txt").write_text(
        "1 failed, 288 passed in 20.00s\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="pytest evidence includes failures"):
        build_canonical_dashboard_artifact(tmp_path / "pytest-work", evidence_root=pytest_evidence_root)


def test_canonical_showcase_artifact_rejects_failed_browser_visual_evidence(tmp_path):
    from quantlab.showcase import build_canonical_dashboard_artifact

    evidence_root = tmp_path / "evidence"
    _write_current_evidence_root(evidence_root)
    (evidence_root / "docs/browser-visual-diff.json").write_text(
        json.dumps({
            "artifactKind": "browser_visual_diff",
            "claimBoundary": "no_alpha_claim",
            "status": "failed",
            "mismatchedPixels": 2000,
            "totalPixels": 1296000,
            "mismatchRatio": 2000 / 1296000,
            "maxMismatchRatio": 0.001,
        }),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="browser visual diff evidence is not passed"):
        build_canonical_dashboard_artifact(tmp_path / "work", evidence_root=evidence_root)

    invalid_cases = [
        (
            {"artifactKind": "hash_only_visual"},
            "browser visual diff evidence kind",
        ),
        (
            {"claimBoundary": "alpha_claim"},
            "browser visual diff evidence must preserve no_alpha_claim",
        ),
        (
            {"mismatchRatio": None},
            "browser visual diff evidence has invalid numeric fields",
        ),
        (
            {"mismatchRatio": 86 / 1296000, "maxMismatchRatio": -0.001},
            "browser visual diff evidence has invalid threshold",
        ),
        (
            {
                "mismatchedPixels": 2000,
                "mismatchRatio": 2000 / 1296000,
                "maxMismatchRatio": 0.001,
            },
            "browser visual diff evidence exceeds threshold",
        ),
        (
            {"mismatchRatio": 0.0, "maxMismatchRatio": 0.001},
            "browser visual diff evidence ratio",
        ),
        (
            {"mismatchedPixels": -1},
            "browser visual diff evidence has invalid pixel counts",
        ),
    ]
    for patch, message in invalid_cases:
        invalid_root = tmp_path / f"evidence-{len(message)}"
        _write_current_evidence_root(invalid_root)
        visual_diff = json.loads((invalid_root / "docs/browser-visual-diff.json").read_text(encoding="utf-8"))
        visual_diff.update(patch)
        (invalid_root / "docs/browser-visual-diff.json").write_text(
            json.dumps(visual_diff),
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match=message):
            build_canonical_dashboard_artifact(tmp_path / f"work-{len(message)}", evidence_root=invalid_root)

    missing_field_root = tmp_path / "missing-field-evidence"
    _write_current_evidence_root(missing_field_root)
    visual_diff = json.loads((missing_field_root / "docs/browser-visual-diff.json").read_text(encoding="utf-8"))
    del visual_diff["mismatchRatio"]
    (missing_field_root / "docs/browser-visual-diff.json").write_text(
        json.dumps(visual_diff),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="browser visual diff evidence missing mismatchRatio"):
        build_canonical_dashboard_artifact(tmp_path / "missing-field-work", evidence_root=missing_field_root)

    json_shape_root = tmp_path / "json-shape-evidence"
    _write_current_evidence_root(json_shape_root)
    (json_shape_root / "docs/browser-visual-diff.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="showcase evidence artifact must be a JSON object"):
        build_canonical_dashboard_artifact(tmp_path / "json-shape-work", evidence_root=json_shape_root)

    public_probe_root = tmp_path / "public-probe-evidence"
    _write_current_evidence_root(public_probe_root)
    (public_probe_root / "docs/public-hosting-probe.json").write_text(
        json.dumps({
            "claimBoundary": "alpha_claim",
            "status": "configured_not_observed",
            "hashStatus": "mismatched",
        }),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="public hosting probe evidence must preserve no_alpha_claim"):
        build_canonical_dashboard_artifact(tmp_path / "public-probe-work", evidence_root=public_probe_root)

    public_status_root = tmp_path / "public-status-evidence"
    _write_current_evidence_root(public_status_root)
    (public_status_root / "docs/public-hosting-probe.json").write_text(
        json.dumps({
            "claimBoundary": "no_alpha_claim",
            "status": "planned",
            "hashStatus": "mismatched",
        }),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="public hosting probe evidence has unsupported status"):
        build_canonical_dashboard_artifact(tmp_path / "public-status-work", evidence_root=public_status_root)

    public_incomplete_root = tmp_path / "public-incomplete-evidence"
    _write_current_evidence_root(public_incomplete_root)
    (public_incomplete_root / "docs/public-hosting-probe.json").write_text(
        json.dumps({
            "claimBoundary": "no_alpha_claim",
            "status": "configured_not_observed",
            "hashStatus": "mismatched",
        }),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="public hosting probe evidence has unexpected targetUrl"):
        build_canonical_dashboard_artifact(
            tmp_path / "public-incomplete-work",
            evidence_root=public_incomplete_root,
        )

    # CR-FPS-011: time-based staleness no longer raises here — it downgrades to
    # configured_not_observed. See test_hosting_freshness_downgrades_deterministically.

    public_bad_observed_root = tmp_path / "public-bad-observed-evidence"
    _write_current_evidence_root(public_bad_observed_root)
    public_probe = json.loads(
        (public_bad_observed_root / "docs/public-hosting-probe.json").read_text(encoding="utf-8")
    )
    public_probe["observedAt"] = "not-a-dateZ"
    (public_bad_observed_root / "docs/public-hosting-probe.json").write_text(
        json.dumps(public_probe),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="public hosting probe evidence requires valid UTC observedAt"):
        build_canonical_dashboard_artifact(
            tmp_path / "public-bad-observed-work",
            evidence_root=public_bad_observed_root,
        )

    public_future_observed_root = tmp_path / "public-future-observed-evidence"
    _write_current_evidence_root(public_future_observed_root)
    public_probe = json.loads(
        (public_future_observed_root / "docs/public-hosting-probe.json").read_text(encoding="utf-8")
    )
    public_probe["observedAt"] = "2999-06-13T07:24:50.456Z"
    (public_future_observed_root / "docs/public-hosting-probe.json").write_text(
        json.dumps(public_probe),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="public hosting probe evidence observedAt is in the future"):
        build_canonical_dashboard_artifact(
            tmp_path / "public-future-observed-work",
            evidence_root=public_future_observed_root,
        )

    public_hash_overclaim_root = tmp_path / "public-hash-overclaim-evidence"
    _write_current_evidence_root(public_hash_overclaim_root)
    public_probe = json.loads(
        (public_hash_overclaim_root / "docs/public-hosting-probe.json").read_text(encoding="utf-8")
    )
    public_probe["status"] = "proven"
    public_probe["hashStatus"] = "mismatched"
    (public_hash_overclaim_root / "docs/public-hosting-probe.json").write_text(
        json.dumps(public_probe),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="proven public hosting evidence requires matched hash"):
        build_canonical_dashboard_artifact(
            tmp_path / "public-hash-overclaim-work",
            evidence_root=public_hash_overclaim_root,
        )

    public_configured_overclaim_root = tmp_path / "public-configured-overclaim-evidence"
    _write_current_evidence_root(public_configured_overclaim_root)
    public_probe = json.loads(
        (public_configured_overclaim_root / "docs/public-hosting-probe.json").read_text(encoding="utf-8")
    )
    public_probe["hashStatus"] = "matched"
    (public_configured_overclaim_root / "docs/public-hosting-probe.json").write_text(
        json.dumps(public_probe),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="configured public hosting evidence must not imply matched hash"):
        build_canonical_dashboard_artifact(
            tmp_path / "public-configured-overclaim-work",
            evidence_root=public_configured_overclaim_root,
        )

    audit_root = tmp_path / "audit-evidence"
    _write_current_evidence_root(audit_root)
    (audit_root / "docs/review/assets/gate-frontend-audit.txt").write_text(
        "found 1 vulnerability\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="frontend audit evidence is not clean"):
        build_canonical_dashboard_artifact(tmp_path / "audit-work", evidence_root=audit_root)


_PROVEN_OBSERVED_AT = "2026-06-14T02:00:00.000Z"
_PROVEN_ASOF = datetime(2026, 6, 14, 3, 0, 0, tzinfo=timezone.utc)
_HOSTING_LINE_BY_FRESHNESS = {
    True: "public hosting proven (hash matched)",
    False: "public hosting configured_not_observed (stale, hash matched)",
}


def _set_probe(root: Path, **patch) -> None:
    path = root / "docs/public-hosting-probe.json"
    probe = json.loads(path.read_text(encoding="utf-8"))
    probe.update(patch)
    path.write_text(json.dumps(probe), encoding="utf-8")


def _make_proven_root(root: Path) -> None:
    _write_current_evidence_root(root)
    _set_probe(
        root,
        status="proven",
        hashStatus="matched",
        deployedDataHash="same",
        expectedDataHash="same",
        observedAt=_PROVEN_OBSERVED_AT,
        freshnessStatus="fresh",
    )


def _hosting_line(artifact: dict) -> str:
    return next(t for t in artifact["evidence"]["tests"] if t.startswith("public hosting"))


def test_hosting_freshness_downgrades_deterministically(tmp_path):
    """CR-FPS-011: a fresh proven probe reads proven; once stale-by-asof or
    self-declared stale it downgrades to configured_not_observed and never crashes."""
    from quantlab.showcase import build_canonical_dashboard_artifact

    fresh_root = tmp_path / "fresh"
    _make_proven_root(fresh_root)
    fresh = build_canonical_dashboard_artifact(
        tmp_path / "fresh-work", evidence_root=fresh_root, asof=_PROVEN_ASOF
    )
    assert _hosting_line(fresh) == "public hosting proven (hash matched)"
    assert fresh["demoReadiness"]["publicHosting"] == "not_proven"

    # Same proven probe, but asof is past the 24h window -> downgrade, no raise.
    stale_asof = _PROVEN_ASOF + timedelta(hours=48)
    stale = build_canonical_dashboard_artifact(
        tmp_path / "stale-work", evidence_root=fresh_root, asof=stale_asof
    )
    assert _hosting_line(stale) == "public hosting configured_not_observed (stale, hash matched)"
    assert stale["demoReadiness"]["publicHosting"] == "not_proven"

    # Self-declared freshnessStatus=stale also downgrades (no raise).
    selfstale_root = tmp_path / "selfstale"
    _make_proven_root(selfstale_root)
    _set_probe(selfstale_root, freshnessStatus="stale")
    selfstale = build_canonical_dashboard_artifact(
        tmp_path / "selfstale-work", evidence_root=selfstale_root, asof=_PROVEN_ASOF
    )
    assert _hosting_line(selfstale).startswith("public hosting configured_not_observed (stale")


def test_hosting_freshness_window_boundary_is_inclusive(tmp_path):
    """Exactly at the 24h window the observation is stale (boundary is `<=`)."""
    from quantlab.showcase import build_canonical_dashboard_artifact

    asof = _PROVEN_ASOF
    root = tmp_path / "boundary"
    _make_proven_root(root)
    at_window = (asof - timedelta(hours=24)).isoformat().replace("+00:00", "Z")
    _set_probe(root, observedAt=at_window)
    artifact = build_canonical_dashboard_artifact(
        tmp_path / "boundary-work", evidence_root=root, asof=asof
    )
    assert _hosting_line(artifact) == "public hosting configured_not_observed (stale, hash matched)"

    just_inside = (asof - timedelta(hours=24) + timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
    _set_probe(root, observedAt=just_inside)
    artifact2 = build_canonical_dashboard_artifact(
        tmp_path / "boundary-work-2", evidence_root=root, asof=asof
    )
    assert _hosting_line(artifact2) == "public hosting proven (hash matched)"


def test_hosting_freshness_default_asof_does_not_crash_when_stale(tmp_path):
    """The committed-evidence path must not rot by wall-clock: an old observedAt
    degrades instead of raising even with the default (now) asof."""
    from quantlab.showcase import build_canonical_dashboard_artifact

    root = tmp_path / "old"
    _make_proven_root(root)
    _set_probe(root, observedAt="2000-01-01T00:00:00.000Z")
    artifact = build_canonical_dashboard_artifact(tmp_path / "old-work", evidence_root=root)
    assert _hosting_line(artifact) == "public hosting configured_not_observed (stale, hash matched)"


@settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(age_seconds=st.integers(min_value=0, max_value=72 * 60 * 60))
def test_pbt_hosting_freshness_window(tmp_path, age_seconds):
    """For observedAt <= asof, the effective status is proven iff within the
    24h window; a stale proven probe never presents as proven."""
    from quantlab.showcase import build_canonical_dashboard_artifact

    asof = _PROVEN_ASOF
    observed = (asof - timedelta(seconds=age_seconds)).isoformat().replace("+00:00", "Z")
    root = tmp_path / f"pbt-root-{age_seconds}"
    _make_proven_root(root)
    _set_probe(root, observedAt=observed)
    expected_line = _HOSTING_LINE_BY_FRESHNESS[age_seconds < 24 * 60 * 60]
    artifact = build_canonical_dashboard_artifact(
        tmp_path / f"pbt-work-{age_seconds}", evidence_root=root, asof=asof
    )
    assert _hosting_line(artifact) == expected_line
    assert artifact["demoReadiness"]["publicHosting"] == "not_proven"


def test_canonical_showcase_artifact_fails_closed_without_evidence_artifacts(tmp_path):
    from quantlab.showcase import build_canonical_dashboard_artifact

    with pytest.raises(FileNotFoundError, match="gate-pytest"):
        build_canonical_dashboard_artifact(tmp_path / "work", evidence_root=tmp_path / "missing")


def test_showcase_api_tests_do_not_reintroduce_retired_fixture_marker():
    """Current F test data must not point future work back to the retired fixture source."""
    test_source = Path(__file__).read_text(encoding="utf-8")
    retired_marker = "showcase" + "-fixture"

    assert retired_marker not in test_source
