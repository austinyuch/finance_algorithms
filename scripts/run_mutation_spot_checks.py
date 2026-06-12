"""Run deterministic mutation spot-checks for critical QuantLab logic.

This is a repo-local fallback for cases where mutmut's sandbox layout is too narrow
for top-level imports. Each mutation is applied, its targeted tests must fail, and
the original file is restored before the next check.
"""
from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class MutationSpec:
    name: str
    path: str
    original: str
    mutated: str
    test_command: tuple[str, ...]


@dataclass(frozen=True)
class MutationToken:
    path: Path
    original_text: str


MUTATIONS: tuple[MutationSpec, ...] = (
    MutationSpec(
        name="engine-regime-selector",
        path="quantlab/engine/vectorized.py",
        original="return select_rebalance_dates(candidates, labels, frequency=frequency)",
        mutated="return candidates",
        test_command=("uv", "run", "pytest", "-q", "tests/quantlab/test_a0_2_engine.py", "-k", "regime_rebalance"),
    ),
    MutationSpec(
        name="c3-regime-change",
        path="quantlab/portfolio/rebalance.py",
        original="regime_changed = previous_label is not None and label != previous_label",
        mutated="regime_changed = previous_label is not None and label == previous_label",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_c_3_rebalance.py::test_pbt_regime_rebalance_is_ordered_subset_and_captures_changes"),
    ),
    MutationSpec(
        name="yahoo-latest-close",
        path="scripts/daily_snapshot.py",
        original="valid = [(ts, close) for ts, close in zip(timestamps, closes) if close is not None]",
        mutated="valid = [(ts, close) for ts, close in zip(timestamps, closes)]",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_pbt_yahoo_latest_event_date_matches_last_valid_close"),
    ),
    MutationSpec(
        name="showcase-claim-boundary",
        path="quantlab/showcase/api.py",
        original='return str(metadata.get("claim_boundary") or "no_alpha_claim")',
        mutated='return str(metadata.get("claim_boundary") or "alpha_claim")',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_f_1_showcase_api.py::test_dashboard_summary_conservative_defaults_and_no_mutation"),
    ),
    MutationSpec(
        name="d2-forecast-claim-boundary",
        path="quantlab/models/return_risk.py",
        original='"claim_boundary": "no_alpha_claim",\n            "weights": dict(self._last_weights),',
        mutated='"claim_boundary": "alpha_claim",\n            "weights": dict(self._last_weights),',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_d_4_return_risk_forecast.py::test_forecast_strategy_fallback_metadata_for_degraded_history"),
    ),
    MutationSpec(
        name="d3-robust-claim-boundary",
        path="quantlab/models/robust_optimization.py",
        original='"claim_boundary": "no_alpha_claim",\n            "weights": dict(self._last_weights),',
        mutated='"claim_boundary": "alpha_claim",\n            "weights": dict(self._last_weights),',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_d_5_robust_optimization.py::test_robust_strategy_degraded_history_falls_back_and_preserves_claim_boundary"),
    ),
    MutationSpec(
        name="e-registry-claim-boundary",
        path="quantlab/mlops/experiment_registry.py",
        original='claim_boundary: str = "no_alpha_claim",',
        mutated='claim_boundary: str = "alpha_claim",',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_experiment_registry_dedupes_same_config_and_preserves_no_alpha_claim"),
    ),
    MutationSpec(
        name="b-source-health-claim-boundary",
        path="quantlab/data/source_health.py",
        original='out: dict[str, object] = {"claim_boundary": "source_contract_status_only"}',
        mutated='out: dict[str, object] = {"claim_boundary": "source_contract_ready"}',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_b_6_source_health.py::test_source_health_summary_marks_stooq_blocked_without_reenabling_defaults"),
    ),
    MutationSpec(
        name="snapshot-report-stooq-default",
        path="scripts/daily_snapshot.py",
        original='registry.record("stooq", "*", status="blocked", default_enabled=False,',
        mutated='registry.record("stooq", "*", status="available", default_enabled=True,',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_main_writes_machine_readable_report_for_dry_run"),
    ),
    MutationSpec(
        name="snapshot-scoped-source-health",
        path="scripts/daily_snapshot.py",
        original="yahoo_symbols=yahoo_symbols,\n                include_noaa=include_noaa,",
        mutated="yahoo_symbols=YAHOO_SYMBOLS,\n                include_noaa=include_noaa,",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_main_scoped_live_write_uses_out_root_and_scoped_source_health"),
    ),
    MutationSpec(
        name="showcase-experiment-readiness",
        path="quantlab/showcase/api.py",
        original='"readiness": entry.readiness,',
        mutated='"readiness": "tier3_ready",',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_f_1_showcase_api.py::test_showcase_api_exposes_e_lite_registry_without_tier3_overclaim"),
    ),
    MutationSpec(
        name="g-alt-data-pit-gate",
        path="quantlab/data/alt_data.py",
        original="if available_date > asof:",
        mutated="if available_date < asof:",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_g_1_alt_data.py::test_pbt_alt_data_loader_never_returns_future_available_rows"),
    ),
    MutationSpec(
        name="b-snapshot-ops-stooq-gate",
        path="scripts/snapshot_ops_gate.py",
        original='stooq.get("status") != "blocked" or stooq.get("default_enabled") is not False',
        mutated='stooq.get("status") != "available" or stooq.get("default_enabled") is not True',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_snapshot_ops_gate_accepts_partial_live_report_when_allowed"),
    ),
    MutationSpec(
        name="b-source-quorum-status-gate",
        path="scripts/snapshot_ops_gate.py",
        original='if source_id in source_ids and status in {"ok", "skip"}:',
        mutated='if source_id in source_ids and status in {"ok", "skip", "dry", "fail"}:',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_source_quorum_gate_rejects_dry_or_failed_critical_sources"),
    ),
    MutationSpec(
        name="b-source-quorum-proof-exit-gate",
        path="scripts/source_quorum_proof.py",
        original="if snapshot_exit_code != 0:",
        mutated="if snapshot_exit_code == 0:",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_source_quorum_proof_rejects_scoped_or_failed_attempts"),
    ),
    MutationSpec(
        name="b-source-quorum-proof-file-gate",
        path="scripts/source_quorum_proof.py",
        original="if not path.exists():",
        mutated="if path.exists():",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_source_quorum_proof_rejects_replayed_report_without_snapshot_files"),
    ),
    MutationSpec(
        name="e-registry-snapshot-checksum",
        path="quantlab/mlops/experiment_registry.py",
        original='if artifact.get("checksum") != _checksum(entries):',
        mutated='if artifact.get("checksum") == _checksum(entries):',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_experiment_registry_writes_checksum_snapshot_and_detects_tampering"),
    ),
    MutationSpec(
        name="d-model-evaluation-alpha-gate",
        path="quantlab/models/evaluation.py",
        original='if _claim_boundary(record) != "no_alpha_claim":',
        mutated='if _claim_boundary(record) == "no_alpha_claim":',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_d_6_model_family_evaluation.py::test_model_family_evaluation_rejects_alpha_claim_and_missing_baseline"),
    ),
    MutationSpec(
        name="e-tier3-manifest-serving-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='"serving_status": "not_serving",\n        "retraining_status": "not_configured",\n        "drift_monitoring_status": "skeleton_only",',
        mutated='"serving_status": "serving",\n        "retraining_status": "not_configured",\n        "drift_monitoring_status": "skeleton_only",',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_tier3_manifest_and_drift_skeleton_remain_non_serving"),
    ),
    MutationSpec(
        name="e-tier3-readiness-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='"readiness": "tier3_ready" if not missing else "not_ready",',
        mutated='"readiness": "tier3_ready",',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_tier3_readiness_gate_fails_closed_for_artifact_only_manifest"),
    ),
    MutationSpec(
        name="e-tier3-production-tier-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='and value.get("evidence_tier") == "production"',
        mutated='and value.get("evidence_tier") != "production"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_tier3_readiness_gate_requires_all_live_evidence"),
    ),
    MutationSpec(
        name="e-serving-smoke-health-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='if str(health.get("status") or "").lower() != "ok":',
        mutated='if str(health.get("status") or "").lower() == "ok":',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_serving_smoke_evidence_proves_only_serving_slice"),
    ),
    MutationSpec(
        name="e-retraining-smoke-status-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='if str(result.get("status") or "").lower() != "completed":',
        mutated='if str(result.get("status") or "").lower() == "completed":',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_retraining_smoke_evidence_proves_only_retraining_slice"),
    ),
    MutationSpec(
        name="e-automated-drift-status-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='if result.get("status") not in {"stable", "drift_detected"}:',
        mutated='if result.get("status") in {"stable", "drift_detected"}:',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_automated_drift_monitoring_local_evidence_does_not_make_tier3_ready"),
    ),
    MutationSpec(
        name="e-production-serving-endpoint-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='if parsed.scheme != "https" or not parsed.netloc or _is_local_identity(normalized):',
        mutated='if parsed.scheme == "https" and parsed.netloc and not _is_local_identity(normalized):',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_production_evidence_triplet_satisfies_tier3_gate"),
    ),
    MutationSpec(
        name="e-production-retraining-status-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='if str(payload.get("status") or "").lower() != "completed":',
        mutated='if str(payload.get("status") or "").lower() == "completed":',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_production_evidence_triplet_satisfies_tier3_gate"),
    ),
    MutationSpec(
        name="e-tier3-cli-serving-validator",
        path="scripts/tier3_readiness_gate.py",
        original="validate_production_serving_evidence(serving)",
        mutated="None  # validator bypassed by mutation",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_tier3_readiness_gate_cli.py::test_tier3_readiness_gate_cli_rejects_spoofed_production_map"),
    ),
    MutationSpec(
        name="d-result-store-evaluation-source",
        path="quantlab/models/evaluation.py",
        original='"source": "local_result_store"',
        mutated='"source": "fixture_records"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_d_6_model_family_evaluation.py::test_result_store_family_evaluation_uses_real_run_records"),
    ),
    MutationSpec(
        name="b-schedule-append-only-retention",
        path="scripts/snapshot_schedule_report.py",
        original='"retention": "append_only",\n        "latest_pointer": "latest-schedule-report.json",',
        mutated='"retention": "overwrite_allowed",\n        "latest_pointer": "latest-schedule-report.json",',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_schedule_report_records_retention_and_latest_pointer"),
    ),
    MutationSpec(
        name="b-stooq-decision-default-disabled",
        path="quantlab/data/source_health.py",
        original='"decision": "keep_default_disabled",',
        mutated='"decision": "requires_live_close_rows",',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_stooq_source_contract_decision_requires_live_proof"),
    ),
    MutationSpec(
        name="b-schedule-proof-exit-status",
        path="scripts/snapshot_schedule_report.py",
        original='status = "degraded" if exit_code != 0 else str(schedule.get("status") or "unknown")',
        mutated='status = str(schedule.get("status") or "unknown")',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_schedule_run_proof_records_smoke_tier_and_degraded_exit"),
    ),
    MutationSpec(
        name="e-drift-threshold-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='abs(delta) > threshold',
        mutated='abs(delta) < threshold',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_drift_assessment_report_detects_metric_drift_without_serving_claim"),
    ),
    MutationSpec(
        name="b-stooq-live-close-positive",
        path="quantlab/data/source_health.py",
        original="if not isinstance(close, (int, float)) or not math.isfinite(float(close)) or close <= 0:",
        mutated="if not isinstance(close, (int, float)) or close < 0:",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_pbt_stooq_reopen_evidence_rejects_missing_positive_close"),
    ),
    MutationSpec(
        name="b-stooq-proof-exit-gate",
        path="scripts/stooq_contract_proof.py",
        original="if exit_code != 0:",
        mutated="if exit_code == 0:",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_stooq_contract_proof_rejects_failed_or_replayed_reports"),
    ),
    MutationSpec(
        name="b-stooq-proof-file-gate",
        path="scripts/stooq_contract_proof.py",
        original="if not path.exists():",
        mutated="if False:",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_stooq_contract_proof_rejects_failed_or_replayed_reports"),
    ),
    MutationSpec(
        name="d-evaluation-artifact-checksum",
        path="quantlab/models/evaluation.py",
        original='if artifact.get("checksum") != expected:',
        mutated='if artifact.get("checksum") == expected:',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_d_6_model_family_evaluation.py::test_model_family_evaluation_artifact_is_checksumed_and_written"),
    ),
    MutationSpec(
        name="root-torch-default-dependency",
        path="pyproject.toml",
        original='    "statsmodels>=0.14.6",\n    "uvicorn[standard]>=0.49.0",',
        mutated='    "statsmodels>=0.14.6",\n    "torch>=2.12.0",\n    "uvicorn[standard]>=0.49.0",',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_dependency_security.py::test_default_project_dependencies_exclude_torch"),
    ),
    MutationSpec(
        name="governance-stale-next-steps-alert",
        path=".agents/specs/NEXT_STEPS.md",
        original="Dependabot alert #7 fixed",
        mutated="Dependabot alert #7 post-merge rescan pending",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_next_steps_reflects_post_merge_torch_alert_state"),
    ),
    MutationSpec(
        name="governance-stale-post-merge-sync-promotion",
        path=".agents/specs/NEXT_STEPS.md",
        original="Authoritative promotion state lives in GitHub PR state and spec-local reports",
        mutated="Open/promote `spec/post-merge-scheduled-observer-sync` after the governance guard confirms the observer promotion memo is no longer stale.",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_next_steps_reflects_post_merge_governance_sync_state"),
    ),
    MutationSpec(
        name="governance-stale-cron-proof-pending",
        path=".agents/specs/NEXT_STEPS.md",
        original="Live observation artifact: `reports/scheduled-run-observation-2026-06-12-cron.json` records `status=proven`, `schedule_run_count=1`, and latest schedule success `27392471359`.",
        mutated="Live observation artifact: `reports/scheduled-run-observation-2026-06-12.json` records `status=pending`, `schedule_run_count=0`, and latest manual success `27387041974`.",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_next_steps_reflects_post_merge_scheduled_observer_state"),
    ),
    MutationSpec(
        name="governance-exhaustive-pr-ledger-regression",
        path=".agents/specs/NEXT_STEPS.md",
        original="do not append every squash PR to this rolling memo",
        mutated="append every squash PR to this rolling memo as exact dev/main promotion text",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_next_steps_uses_non_self_staling_promotion_boundary"),
    ),
    MutationSpec(
        name="public-hosting-manifest-status-regression",
        path="docs/deployment-manifest.json",
        original='"status": "proven"',
        mutated='"status": "configured_not_observed"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_public_hosting_manifest_carries_observed_proof"),
    ),
    MutationSpec(
        name="public-hosting-manifest-hash-regression",
        path="docs/deployment-manifest.json",
        original='"hashStatus": "matched"',
        mutated='"hashStatus": "mismatched"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_public_hosting_manifest_carries_observed_proof"),
    ),
    MutationSpec(
        name="public-hosting-manifest-contract-regression",
        path="docs/deployment-manifest.json",
        original='"manifestContractStatus": "matched"',
        mutated='"manifestContractStatus": "mismatched"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_public_hosting_manifest_carries_observed_proof"),
    ),
    MutationSpec(
        name="b-scheduled-observer-manual-pending",
        path="scripts/scheduled_run_observer.py",
        original='status = "proven" if latest_schedule_success is not None else "pending"',
        mutated='status = "proven"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_scheduled_run_observer_keeps_manual_dispatch_as_pending"),
    ),
)


def apply_mutation(root: Path, spec: MutationSpec) -> MutationToken:
    path = root / spec.path
    text = path.read_text(encoding="utf-8")
    occurrences = text.count(spec.original)
    if occurrences != 1:
        raise ValueError(f"{spec.name}: original text must occur exactly once, found {occurrences}")
    path.write_text(text.replace(spec.original, spec.mutated, 1), encoding="utf-8")
    return MutationToken(path=path, original_text=text)


def restore_mutation(token: MutationToken) -> None:
    token.path.write_text(token.original_text, encoding="utf-8")


def purge_python_bytecode(root: Path) -> None:
    importlib.invalidate_caches()
    for cache_dir in root.rglob("__pycache__"):
        shutil.rmtree(cache_dir, ignore_errors=True)


def selected_specs(names: Sequence[str]) -> list[MutationSpec]:
    if not names:
        return list(MUTATIONS)
    wanted = set(names)
    found = [spec for spec in MUTATIONS if spec.name in wanted]
    missing = wanted - {spec.name for spec in found}
    if missing:
        raise ValueError(f"unknown mutation(s): {', '.join(sorted(missing))}")
    return found


def run_mutation(root: Path, spec: MutationSpec) -> bool:
    token = apply_mutation(root, spec)
    purge_python_bytecode(root)
    try:
        result = subprocess.run(spec.test_command, cwd=root)
        killed = result.returncode != 0
        status = "KILLED" if killed else "SURVIVED"
        print(f"{spec.name}: {status}")
        return killed
    finally:
        restore_mutation(token)
        purge_python_bytecode(root)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list available mutation names")
    parser.add_argument("--only", action="append", default=[], help="run one mutation by name; repeatable")
    args = parser.parse_args(argv)

    if args.list:
        for spec in MUTATIONS:
            print(spec.name)
        return 0

    root = Path(__file__).resolve().parents[1]
    specs = selected_specs(args.only)
    results = [run_mutation(root, spec) for spec in specs]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
