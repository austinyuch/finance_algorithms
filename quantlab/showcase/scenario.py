"""Canonical showcase scenario built from repo-side QuantLab records."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from quantlab.mlops import ExperimentRegistry
from quantlab.showcase.api import ShowcaseReadAPI, build_dashboard_summary
from quantlab.tracking import LocalResultStore


_FALLBACK_EVIDENCE_TESTS = [
    "424 passed",
    "frontend tests 46 passed",
    "Python mutation 118/118 killed",
    "frontend mutation 26/26 killed",
    "F Next.js coverage 90.00%",
    "E registry coverage 99%",
    "B source-health/Stooq proof coverage 90%",
]


def _read_required_text(root: Path, relative_path: str) -> str:
    path = root / relative_path
    if not path.exists():
        raise FileNotFoundError(f"missing showcase evidence artifact: {relative_path}")
    return path.read_text(encoding="utf-8")


def _read_required_json(root: Path, relative_path: str) -> Mapping[str, Any]:
    path = root / relative_path
    if not path.exists():
        raise FileNotFoundError(f"missing showcase evidence artifact: {relative_path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"showcase evidence artifact must be a JSON object: {relative_path}")
    return data


def _extract_count(pattern: str, text: str, *, label: str) -> int:
    match = re.search(pattern, text)
    if not match:
        raise ValueError(f"missing {label} evidence count")
    return int(match.group(1))


def _extract_successful_test_count(pattern: str, text: str, *, label: str) -> int:
    if re.search(r"\b[1-9]\d* failed\b", text):
        raise ValueError(f"{label} evidence includes failures")
    return _extract_count(pattern, text, label=label)


def _extract_ratio(pattern: str, text: str, *, label: str) -> str:
    match = re.search(pattern, text)
    if not match:
        raise ValueError(f"missing {label} evidence")
    return match.group(1)


def _validate_browser_visual_diff(visual_diff: Mapping[str, Any]) -> None:
    if visual_diff.get("artifactKind") != "browser_visual_diff":
        raise ValueError("browser visual diff evidence kind is unsupported")
    if visual_diff.get("status") != "passed":
        raise ValueError("browser visual diff evidence is not passed")
    if visual_diff.get("claimBoundary") != "no_alpha_claim":
        raise ValueError("browser visual diff evidence must preserve no_alpha_claim")

    try:
        mismatched = int(visual_diff["mismatchedPixels"])
        total = int(visual_diff["totalPixels"])
        mismatch_ratio = float(visual_diff["mismatchRatio"])
        max_mismatch_ratio = float(visual_diff["maxMismatchRatio"])
    except KeyError as exc:
        raise ValueError(f"browser visual diff evidence missing {exc.args[0]}") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError("browser visual diff evidence has invalid numeric fields") from exc

    if mismatched < 0 or total <= 0 or mismatched > total:
        raise ValueError("browser visual diff evidence has invalid pixel counts")
    if max_mismatch_ratio <= 0:
        raise ValueError("browser visual diff evidence has invalid threshold")

    expected_ratio = mismatched / total
    if abs(mismatch_ratio - expected_ratio) > 1e-12:
        raise ValueError("browser visual diff evidence ratio does not match pixel counts")
    if mismatch_ratio > max_mismatch_ratio:
        raise ValueError("browser visual diff evidence exceeds threshold")


def _classify_hosting_freshness(
    public_probe: Mapping[str, Any], asof: datetime
) -> str:
    """Return ``"fresh"`` or ``"stale"`` for a committed hosting observation.

    Integrity violations of ``observedAt`` (missing/non-UTC/unparseable/future)
    still raise — they signal a malformed probe rather than mere age. Time-based
    staleness (``observedAt + maxAgeHours <= asof``) or a self-declared
    ``freshnessStatus != "fresh"`` is reported as ``"stale"`` so the consumer can
    downgrade rather than crash (CR-FPS-011, consistent with the CR-FPS-008
    frontend contract).
    """
    max_age_hours = public_probe.get("maxAgeHours")
    if max_age_hours != 24:
        raise ValueError("public hosting probe evidence has unexpected freshness window")

    observed_at = public_probe.get("observedAt")
    if not isinstance(observed_at, str) or not observed_at.endswith("Z"):
        raise ValueError("public hosting probe evidence requires UTC observedAt")
    try:
        observed_at_dt = datetime.fromisoformat(observed_at.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise ValueError("public hosting probe evidence requires valid UTC observedAt") from exc
    if observed_at_dt.tzinfo != timezone.utc:
        raise ValueError("public hosting probe evidence requires valid UTC observedAt")
    if observed_at_dt > asof:
        raise ValueError("public hosting probe evidence observedAt is in the future")

    if public_probe.get("freshnessStatus") != "fresh":
        return "stale"
    if observed_at_dt + timedelta(hours=max_age_hours) <= asof:
        return "stale"
    return "fresh"


def _validate_public_hosting_probe(
    public_probe: Mapping[str, Any], *, asof: datetime
) -> str:
    """Validate probe integrity and return its freshness verdict.

    Raises on integrity violations (overclaim, malformed contract, bad
    ``observedAt``). Returns ``"fresh"``/``"stale"`` for time-based freshness so
    callers can downgrade a stale observation to ``configured_not_observed``
    instead of failing the build.
    """
    if public_probe.get("claimBoundary") != "no_alpha_claim":
        raise ValueError("public hosting probe evidence must preserve no_alpha_claim")

    status = public_probe.get("status")
    if status not in {"configured_not_observed", "proven"}:
        raise ValueError("public hosting probe evidence has unsupported status")

    if public_probe.get("targetUrl") != "https://austinyuch.github.io/finance_algorithms/":
        raise ValueError("public hosting probe evidence has unexpected targetUrl")
    if public_probe.get("httpStatus") != 200:
        raise ValueError("public hosting probe evidence requires HTTP 200")
    if public_probe.get("deployedManifestStatus") != 200:
        raise ValueError("public hosting probe evidence requires deployed manifest HTTP 200")
    if public_probe.get("manifestContractStatus") != "matched":
        raise ValueError("public hosting probe evidence requires matched manifest contract")

    freshness = _classify_hosting_freshness(public_probe, asof)

    hash_status = public_probe.get("hashStatus")
    if status == "proven":
        if hash_status != "matched":
            raise ValueError("proven public hosting evidence requires matched hash")
        if public_probe.get("deployedDataHash") != public_probe.get("expectedDataHash"):
            raise ValueError("proven public hosting evidence requires matching dataHash")
    elif hash_status not in {"mismatched", "missing", "not_checked"}:
        raise ValueError("configured public hosting evidence must not imply matched hash")

    return freshness


def _current_evidence_tests(
    evidence_root: str | Path | None, *, asof: datetime | None = None
) -> list[str]:
    """Read current dashboard evidence from committed proof artifacts.

    ``evidence_root=None`` is retained for direct unit-level callers that only
    exercise the read API scenario. Production/static payload generation passes
    the repository root and fails closed if proof artifacts are missing.
    """
    if evidence_root is None:
        return list(_FALLBACK_EVIDENCE_TESTS)

    root = Path(evidence_root)
    pytest_text = _read_required_text(root, "docs/review/assets/gate-pytest.txt")
    frontend_text = _read_required_text(root, "docs/review/assets/gate-frontend-test.txt")
    audit_text = _read_required_text(root, "docs/review/assets/gate-frontend-audit.txt")
    mutation_text = _read_required_text(
        root,
        ".agents/specs/a0-backtest-foundation/reports/mutation-automation-report.md",
    )
    fbp_review = _read_required_text(root, ".agents/specs/f-browser-pixel-baseline/review.md")
    visual_diff = _read_required_json(root, "docs/browser-visual-diff.json")
    public_probe = _read_required_json(root, "docs/public-hosting-probe.json")

    pytest_count = _extract_successful_test_count(r"(\d+) passed", pytest_text, label="pytest")
    frontend_count = _extract_successful_test_count(
        r"Tests\s+(\d+) passed",
        frontend_text,
        label="frontend test",
    )
    mutation_ratio = _extract_ratio(
        r"\*\*(\d+/\d+) configured/killed\*\*",
        mutation_text,
        label="Python mutation",
    )
    frontend_mutation = _extract_ratio(
        r"Frontend mutation: \*\*(\d+/\d+) killed\*\*",
        fbp_review,
        label="frontend mutation",
    )
    frontend_coverage = _extract_ratio(
        r"Frontend coverage: \*\*(\d+(?:\.\d+)?)% line coverage\*\*",
        fbp_review,
        label="frontend coverage",
    )

    if "found 0 vulnerabilities" not in audit_text:
        raise ValueError("frontend audit evidence is not clean")
    _validate_browser_visual_diff(visual_diff)
    if asof is None:
        asof = datetime.now(timezone.utc)
    freshness = _validate_public_hosting_probe(public_probe, asof=asof)

    hash_status = str(public_probe.get("hashStatus", "unknown"))
    if freshness == "stale":
        # A stale observation can never present as proven; downgrade honestly.
        hosting_line = f"public hosting configured_not_observed (stale, hash {hash_status})"
    else:
        probe_status = str(public_probe["status"])
        hosting_line = f"public hosting {probe_status} (hash {hash_status})"

    return [
        f"{pytest_count} passed",
        f"frontend tests {frontend_count} passed",
        f"Python mutation {mutation_ratio} killed",
        f"frontend mutation {frontend_mutation} killed",
        f"F Next.js coverage {frontend_coverage}%",
        "frontend audit 0 vulnerabilities",
        "browser visual diff passed",
        hosting_line,
    ]


def _metric(sharpe: float) -> dict[str, Any]:
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


def _record(
    run_id: str,
    strategy_name: str,
    sharpe: float,
    *,
    baseline: bool = False,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "strategy_name": strategy_name,
        "strategy_metadata": dict(metadata or {}),
        "config": {"seed": 7, "data_version": "canonical-showcase-scenario"},
        "rebalance_dates": ["2022-01-31", "2022-02-28", "2022-03-31"],
        "metrics": [_metric(sharpe)],
        "is_baseline": baseline,
    }


def _leaderboard_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "runId": str(row["run_id"]),
        "strategyName": str(row["strategy_name"]),
        "oosNetSharpe": float(row["oos_net_sharpe"]),
        "isBaseline": bool(row["is_baseline"]),
        "claimBoundary": str(row["claim_boundary"]),
    }


def _experiment_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "experimentId": str(row["experiment_id"]),
        "modelFamily": str(row["model_family"]),
        "strategyName": str(row["strategy_name"]),
        "runIds": [str(run_id) for run_id in row["run_ids"]],
        "claimBoundary": str(row["claim_boundary"]),
        "status": str(row["status"]),
        "readiness": str(row["readiness"]),
        "tags": [str(tag) for tag in row["tags"]],
    }


_REAL_DATA_ARTIFACT = ".agents/specs/real-data-oos-backtest/reports/real-data-oos-artifact.json"


def _real_data_section(evidence_root: str | Path | None) -> dict[str, Any] | None:
    """Surface the committed real-data OOS-net comparison (research, no_alpha_claim).

    Returns None when the artifact is absent or not a computed comparison, so the
    dashboard degrades to the canonical scenario without overclaiming.
    """
    if evidence_root is None:
        return None
    path = Path(evidence_root) / _REAL_DATA_ARTIFACT
    if not path.exists():
        return None
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if artifact.get("artifact_kind") != "real_data_oos_backtest_artifact":
        return None
    if artifact.get("status") != "computed" or artifact.get("claim_boundary") != "no_alpha_claim":
        return None
    report = artifact.get("report") or {}
    provenance = report.get("data_provenance") or {}
    rows: list[dict[str, Any]] = [
        {
            "strategyName": str(row.get("strategy_name") or ""),
            "oosNetSharpe": float(row["oos_net_sharpe"]),
            "isBaseline": bool(row.get("is_baseline")),
        }
        for row in report.get("rows") or []
    ]
    rows.sort(key=lambda row: row["oosNetSharpe"], reverse=True)
    if len(rows) < 2 or not any(row["isBaseline"] for row in rows):
        return None
    return {
        "source": "real_data_oos_backtest_artifact",
        "status": "computed",
        "claimBoundary": "no_alpha_claim",
        "assetSet": list(report.get("asset_set") or []),
        "overlapStart": str(provenance.get("overlap_start") or ""),
        "overlapEnd": str(provenance.get("overlap_end") or ""),
        "overlapMonths": float(provenance.get("overlap_months") or 0.0),
        "rows": rows,
    }


def _frontend_payload(
    summary: Mapping[str, Any],
    *,
    source_record_count: int,
    evidence_tests: list[str],
    visual_regression_status: str,
    real_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    warnings = list(summary.get("warnings") or [])
    if "local_runtime_only" not in warnings:
        warnings.append("local_runtime_only")
    payload: dict[str, Any] = {
        "activeRunId": str(summary["active_run_id"]),
        "strategyName": str(summary["strategy_name"]),
        "claimBoundary": str(summary["claim_boundary"]),
        "regime": dict(summary["regime"]),
        "allocation": dict(summary["allocation"]),
        "rebalanceDates": list(summary["rebalance_dates"]),
        "leaderboard": [_leaderboard_row(row) for row in summary["leaderboard"]],
        "experiments": [_experiment_row(row) for row in summary["experiments"]],
        "warnings": warnings,
        "evidence": {
            "readiness": "local_runtime_only",
            "tests": list(evidence_tests),
        },
        "demoReadiness": {
            "publicHosting": "not_proven",
            "visualRegression": visual_regression_status,
            "dependencyAudit": "clean",
            "claim": "local_demo_only",
        },
        "sourceMetadata": {
            "source": "local_result_store",
            "sourceRecordCount": source_record_count,
            "experimentRegistry": "experiment_registry",
        },
    }
    if real_data is not None:
        payload["realData"] = real_data
    return payload


def build_canonical_dashboard_artifact(
    work_dir: str | Path,
    *,
    evidence_root: str | Path | None = None,
    asof: datetime | None = None,
) -> dict[str, Any]:
    """Build the frontend dashboard artifact from real local stores.

    The scenario remains a deterministic local demo, but the payload is generated
    through the same repo-side read surfaces that production-facing consumers use.
    """
    root = Path(work_dir)
    root.mkdir(parents=True, exist_ok=True)
    with LocalResultStore(root / "showcase.db") as store:
        forecast_run = store.log(_record(
            "forecast-run",
            "ForecastAllocationStrategy",
            1.21,
            metadata={
                "last_regime": "risk_on",
                "last_regime_confidence": 0.6,
                "weights": {"GROWTH": 0.62, "STEADY": 0.38},
                "claim_boundary": "no_alpha_claim",
            },
        ))
        baseline_run = store.log(_record(
            "baseline-run",
            "StaticWeights",
            0.74,
            baseline=True,
            metadata={"claim_boundary": "no_alpha_claim"},
        ))
        registry = ExperimentRegistry(root / "experiments.jsonl")
        registry.register(
            "return-risk-forecast",
            "ForecastAllocationStrategy",
            {"lookback": 12, "vol_cap": 0.3},
            run_ids=[forecast_run, baseline_run],
            metrics={"oos_net_sharpe": 1.21},
            tags=["D2", "F", "E-lite"],
        )
        api = ShowcaseReadAPI(store, experiment_registry=registry)
        summary = build_dashboard_summary(
            api.run_detail(forecast_run),
            api.leaderboard(),
            experiments=api.experiments(),
        )
        return _frontend_payload(
            summary,
            source_record_count=len(api.leaderboard()),
            evidence_tests=_current_evidence_tests(evidence_root, asof=asof),
            visual_regression_status="proven" if evidence_root is not None else "not_proven",
            real_data=_real_data_section(evidence_root),
        )


def write_canonical_dashboard_artifact(
    target: str | Path,
    work_dir: str | Path,
    *,
    evidence_root: str | Path | None = None,
    asof: datetime | None = None,
) -> dict[str, Any]:
    artifact = build_canonical_dashboard_artifact(
        work_dir, evidence_root=evidence_root, asof=asof
    )
    output = Path(target)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return artifact
