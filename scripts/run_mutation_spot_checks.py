"""Run deterministic mutation spot-checks for critical QuantLab logic.

This is a repo-local fallback for cases where mutmut's sandbox layout is too narrow
for top-level imports. Each mutation is applied, its targeted tests must fail, and
the original file is restored before the next check.
"""
from __future__ import annotations

import argparse
import importlib
import json
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


def _public_probe_expected_hash() -> str:
    probe_path = Path(__file__).resolve().parents[1] / "docs/public-hosting-probe.json"
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    expected = probe.get("expectedDataHash")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError("public-hosting probe expectedDataHash must be a 64-character hash")
    return expected


def _showcase_pytest_label() -> str:
    showcase_path = Path(__file__).resolve().parents[1] / "docs/showcase.json"
    showcase = json.loads(showcase_path.read_text(encoding="utf-8"))
    tests = (showcase.get("evidence") or {}).get("tests") or []
    if not isinstance(tests, list):
        raise ValueError("showcase evidence tests must be a list")
    for item in tests:
        if isinstance(item, str) and item.endswith(" passed") and item.split(" ", 1)[0].isdigit():
            return item
    raise ValueError("showcase evidence tests must include a pytest passed label")


MUTATIONS: tuple[MutationSpec, ...] = (
    MutationSpec(
        name="engine-regime-selector",
        path="quantlab/engine/vectorized.py",
        original="return select_rebalance_dates(candidates, labels, frequency=frequency)",
        mutated="return candidates",
        test_command=("uv", "run", "pytest", "-q", "tests/quantlab/test_a0_2_engine.py", "-k", "regime_rebalance"),
    ),
    MutationSpec(
        name="engine-event-driven-date-gate",
        path="quantlab/engine/vectorized.py",
        original='if engine != "event_driven" or "event_dates" not in config:',
        mutated='if engine != "event_driven" or "event_dates" in config:',
        test_command=("uv", "run", "pytest", "-q", "tests/quantlab/test_a0_2_engine.py", "-k", "event_driven"),
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
        name="result-store-finite-oos-net-sharpe",
        path="quantlab/tracking/local_store.py",
        original="if not math.isfinite(value):\n                raise ValueError(\"result record requires finite oos_net_sharpe\")",
        mutated="if False and not math.isfinite(value):\n                raise ValueError(\"result record requires finite oos_net_sharpe\")",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_a0_4_tracking.py::test_result_store_rejects_non_finite_oos_net_sharpe",
                      "tests/quantlab/test_a0_4_tracking.py::test_pbt_result_store_only_accepts_finite_oos_net_sharpe"),
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
        original='if claim != "no_alpha_claim":\n        raise ValueError("showcase records must explicitly preserve claim_boundary=no_alpha_claim")',
        mutated='if False and claim != "no_alpha_claim":\n        raise ValueError("showcase records must explicitly preserve claim_boundary=no_alpha_claim")',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_f_1_showcase_api.py::test_showcase_api_rejects_missing_claim_boundary_metadata"),
    ),
    MutationSpec(
        name="showcase-frontend-transcript-failure-gate",
        path="quantlab/showcase/scenario.py",
        original='if re.search(r"\\b[1-9]\\d* failed\\b", text):\n        raise ValueError(f"{label} evidence includes failures")',
        mutated='if False and re.search(r"\\b[1-9]\\d* failed\\b", text):\n        raise ValueError(f"{label} evidence includes failures")',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_f_1_showcase_api.py::test_canonical_showcase_artifact_rejects_failed_frontend_transcript"),
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
        name="e-evidence-explicit-claim-boundary",
        path="quantlab/mlops/experiment_registry.py",
        original='if payload.get("claim_boundary") != "no_alpha_claim":\n        raise ValueError(f"{label} must explicitly preserve no_alpha_claim")',
        mutated='if False and payload.get("claim_boundary") != "no_alpha_claim":\n        raise ValueError(f"{label} must explicitly preserve no_alpha_claim")',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_serving_smoke_evidence_rejects_unhealthy_or_alpha_claim"),
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
        name="e-tier3-gate-proof-digest",
        path="quantlab/mlops/experiment_registry.py",
        original='"manifest_digest": _digest_payload(dict(manifest)),',
        mutated='"manifest_digest": "",',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_production_evidence_triplet_satisfies_tier3_gate"),
    ),
    MutationSpec(
        name="e-tier3-gate-production-validator",
        path="quantlab/mlops/experiment_registry.py",
        original="validate_production_serving_evidence(value)",
        mutated="None  # production serving validator bypassed by mutation",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_tier3_gate_rejects_spoofed_production_serving_map"),
    ),
    MutationSpec(
        name="e-tier3-manifest-artifact-uri-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='if not missing and not _is_external_artifact_uri(str(manifest.get("artifact_uri") or "")):',
        mutated='if False and not missing and not _is_external_artifact_uri(str(manifest.get("artifact_uri") or "")):',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_production_evidence_triplet_requires_external_manifest_artifact"),
    ),
    MutationSpec(
        name="e-production-artifact-scheme-allowlist-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='and parsed.scheme in _EXTERNAL_ARTIFACT_URI_SCHEMES\n        and parsed.netloc',
        mutated='and parsed.scheme\n        and parsed.netloc',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_pbt_production_retraining_artifact_uri_requires_external_authority"),
    ),
    MutationSpec(
        name="e-tier3-experiment-binding-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='if not missing and not _is_bound_to_manifest_experiment(manifest, evidence):',
        mutated='if False and not missing and not _is_bound_to_manifest_experiment(manifest, evidence):',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_tier3_gate_rejects_production_evidence_for_different_experiment"),
    ),
    MutationSpec(
        name="e-tier3-production-tier-gate",
        path="quantlab/mlops/experiment_registry.py",
        original="    return True\n\n\ndef _is_bound_to_manifest_experiment(",
        mutated="    return False\n\n\ndef _is_bound_to_manifest_experiment(",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_production_evidence_triplet_satisfies_tier3_gate"),
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
        name="e-production-external-proof-uri-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='if parsed.scheme != "https" or not parsed.netloc or _is_local_identity(proof_id):',
        mutated='if False and (parsed.scheme != "https" or not parsed.netloc or _is_local_identity(proof_id)):',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_pbt_production_external_proof_id_requires_https_url"),
    ),
    MutationSpec(
        name="e-production-observed-at-utc-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(None):',
        mutated='if False and (parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(None)):',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_pbt_production_evidence_requires_utc_observed_at"),
    ),
    MutationSpec(
        name="e-production-external-identity-uri-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='or parsed.scheme not in _EXTERNAL_IDENTITY_URI_SCHEMES\n        or not parsed.netloc',
        mutated='or not parsed.scheme\n        or not parsed.netloc',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_pbt_production_external_identities_require_uri_authority"),
    ),
    MutationSpec(
        name="e-production-retraining-artifact-uri-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='if not _is_external_artifact_uri(artifact_uri):\n        raise ValueError("production retraining evidence requires external artifact_uri")',
        mutated='if not artifact_uri:\n        raise ValueError("production retraining evidence requires artifact_uri")',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_pbt_production_retraining_artifact_uri_requires_external_authority"),
    ),
    MutationSpec(
        name="e-production-drift-threshold-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='threshold = _require_positive_threshold(payload.get("threshold"), "production drift monitoring evidence")',
        mutated='threshold = float(payload.get("threshold", 0.0))',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_pbt_production_drift_monitoring_requires_positive_threshold"),
    ),
    MutationSpec(
        name="e-production-digest-format-gate",
        path="quantlab/mlops/experiment_registry.py",
        original='if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest.lower()):',
        mutated='if not digest:',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_e_1_experiment_registry.py::test_production_evidence_validators_reject_handwritten_short_digests"),
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
        name="f-showcase-canonical-source",
        path="quantlab/showcase/scenario.py",
        original='"source": "local_result_store"',
        mutated='"source": "fixture_records"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_f_1_showcase_api.py::test_canonical_showcase_artifact_uses_result_store_source"),
    ),
    MutationSpec(
        name="f-showcase-evidence-artifact-source",
        path="quantlab/showcase/scenario.py",
        original="evidence_tests=_current_evidence_tests(evidence_root),",
        mutated="evidence_tests=list(_FALLBACK_EVIDENCE_TESTS),",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_f_1_showcase_api.py::test_canonical_showcase_artifact_reads_current_evidence_artifacts"),
    ),
    MutationSpec(
        name="f-showcase-visual-diff-contract-gate",
        path="quantlab/showcase/scenario.py",
        original='if visual_diff.get("artifactKind") != "browser_visual_diff":',
        mutated='if False and visual_diff.get("artifactKind") != "browser_visual_diff":',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_f_1_showcase_api.py::test_canonical_showcase_artifact_rejects_failed_browser_visual_evidence"),
    ),
    MutationSpec(
        name="f-showcase-public-probe-freshness-gate",
        path="quantlab/showcase/scenario.py",
        original='if public_probe.get("freshnessStatus") != "fresh":',
        mutated='if False and public_probe.get("freshnessStatus") != "fresh":',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_f_1_showcase_api.py::test_canonical_showcase_artifact_rejects_failed_browser_visual_evidence"),
    ),
    MutationSpec(
        name="f-showcase-public-probe-observed-at-gate",
        path="quantlab/showcase/scenario.py",
        original="if observed_at_dt > now:",
        mutated="if False and observed_at_dt > now:",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_f_1_showcase_api.py::test_canonical_showcase_artifact_rejects_failed_browser_visual_evidence"),
    ),
    MutationSpec(
        name="f-showcase-public-probe-observed-at-age-gate",
        path="quantlab/showcase/scenario.py",
        original="if observed_at_dt + timedelta(hours=max_age_hours) < now:",
        mutated="if False and observed_at_dt + timedelta(hours=max_age_hours) < now:",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_f_1_showcase_api.py::test_canonical_showcase_artifact_rejects_failed_browser_visual_evidence"),
    ),
    MutationSpec(
        name="f-showcase-retired-fixture-marker",
        path="tests/quantlab/test_f_1_showcase_api.py",
        original='"config": {"seed": 7, "data_version": "canonical-showcase-scenario"}',
        mutated='"config": {"seed": 7, "data_version": "showcase-fixture"}',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_f_1_showcase_api.py::test_showcase_api_tests_do_not_reintroduce_retired_fixture_marker"),
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
        name="demo-tsmc-store-close-gate",
        path="scripts/run_tsmc_hedge_slice.py",
        original='with LocalResultStore(Path(tmp) / "slice.db") as store:',
        mutated='with LocalResultStore(Path(tmp) / "slice.db") as store:\n            store.close = lambda: None',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_demo_script_tempstores.py::test_run_tsmc_hedge_slice_closes_temp_store_when_hedge_run_fails"),
    ),
    MutationSpec(
        name="demo-vintage-store-close-gate",
        path="scripts/run_vintage_slice.py",
        original='with LocalResultStore(Path(tmp) / "vintage_slice.db") as store:',
        mutated='with LocalResultStore(Path(tmp) / "vintage_slice.db") as store:\n            store.close = lambda: None',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_demo_script_tempstores.py::test_run_vintage_slice_closes_temp_store_when_backtest_fails"),
    ),
    MutationSpec(
        name="demo-showcase-payload-tempdir-gate",
        path="scripts/build_showcase_payload.py",
        original='with tempfile.TemporaryDirectory(prefix="quantlab-showcase-") as tmp:',
        mutated='tmp = "/tmp/quantlab-showcase"\n    if True:',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_demo_script_tempstores.py::test_build_showcase_payload_cleans_temp_workspace_when_write_fails"),
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
        name="governance-stale-mutation-count-regression",
        path=".agents/specs/NEXT_STEPS.md",
        original="current suite is governed by the latest evidence row above (**100/100 configured/killed**, including CR-A0 event replay and cross-spec governance mutations)",
        mutated="current suite kills 6/6 configured mutations",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_governance_surfaces_do_not_publish_stale_gate_counts"),
    ),
    MutationSpec(
        name="governance-stale-python-count-regression",
        path=".agents/specs/RTM.md",
        original="current registries use 288 suite evidence",
        mutated="current registries use 275 suite evidence",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_governance_surfaces_do_not_publish_stale_gate_counts"),
    ),
    MutationSpec(
        name="governance-stale-spec-report-pytest-count",
        path=".agents/specs/e-tier3-production-probes/reports/implementation-report.md",
        original="Full Python: `uv run pytest -q` -> 288 passed.",
        mutated="Full Python: `uv run pytest -q` -> 279 passed.",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_governance_surfaces_do_not_publish_stale_gate_counts"),
    ),
    MutationSpec(
        name="governance-stale-import-linter-count-regression",
        path=".agents/specs/NEXT_STEPS.md",
        original="`uv run lint-imports` → KEPT over 75 files / 189 dependencies",
        mutated="`uv run lint-imports` → KEPT over 75 files / 186 dependencies",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_governance_surfaces_do_not_publish_stale_gate_counts"),
    ),
    MutationSpec(
        name="governance-stale-import-linter-formalization-regression",
        path=".agents/specs/a0-backtest-foundation/review.md",
        original="框架隔離已由 `test_a0_0` AST 測試與 `uv run lint-imports` 契約共同守住;目前 import-linter KEPT over 75 files / 189 dependencies。",
        mutated="框架隔離目前由 AST 測試守住(`test_a0_0`);import-linter 正式化列為待辦。",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_governance_surfaces_do_not_publish_stale_gate_counts"),
    ),
    MutationSpec(
        name="governance-local-first-ci-default-regression",
        path="AGENTS.md",
        original="When this repo has an equivalent command",
        mutated="Normal tests and workflow steps should be queued in hosted CI first so local subagents only inspect failures after Actions finish.",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_local_first_ci_policy_is_repo_guided_and_skill_backed"),
    ),
    MutationSpec(
        name="governance-local-first-ci-skill-default-regression",
        path=".agents/skills/local-first-ci/SKILL.md",
        original="normal CI loop as local/subagent-owned work first",
        mutated="normal CI loop as hosted Actions-owned work first",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_local_first_ci_policy_is_repo_guided_and_skill_backed"),
    ),
    MutationSpec(
        name="governance-workflow-hosted-only-contract",
        path=".github/workflows/daily-snapshot.yml",
        original="hosted-only: schedule event semantics and artifact upload transport.",
        mutated="hosted-only: ordinary CI test execution and broad readiness discovery.",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_github_workflows_are_hosted_only_not_routine_ci_queue"),
    ),
    MutationSpec(
        name="local-ci-matrix-report-command-placeholder-regression",
        path="scripts/local_ci_matrix.py",
        original='"command": resolved_command,\n                "exit_code": exit_code,',
        mutated='"command": list(gate.command),\n                "exit_code": exit_code,',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_local_ci_matrix.py::test_local_ci_matrix_run_writes_report_and_replaces_timestamps"),
    ),
    MutationSpec(
        name="governance-refresh-review-stale-evidence-regression",
        path=".agents/specs/governance-evidence-refresh/review.md",
        original="- `uv run pytest -q tests/quantlab/test_governance_guards.py` -> 25 passed.",
        mutated="- `uv run pytest -q tests/quantlab/test_governance_guards.py` -> 19 passed.",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_governance_surfaces_do_not_publish_stale_gate_counts"),
    ),
    MutationSpec(
        name="governance-stale-dashboard-source-wording",
        path=".agents/specs/f-browser-pixel-baseline/review.md",
        original="Data source boundary: dashboard data now comes from the generated canonical `local_result_store` payload introduced by CR-FPS-006; no live backend/live market data dashboard path is claimed.",
        mutated="Still fixture-backed: dashboard data from `frontend/lib/showcase-fixture.ts`; no live backend/live market data dashboard path is claimed.",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_dashboard_source_wording_tracks_canonical_payload"),
    ),
    MutationSpec(
        name="governance-stale-f-nextjs-requirements-fixture",
        path=".agents/specs/f-nextjs-showcase-dashboard/requirements.md",
        original="generated canonical local `local_result_store` payload contract",
        mutated="deterministic fixture",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_dashboard_source_wording_tracks_canonical_payload"),
    ),
    MutationSpec(
        name="governance-stale-f-nextjs-fixture-review",
        path=".agents/specs/f-nextjs-showcase-dashboard/review.md",
        original="CR-FPS-006 replaced the initial inline dashboard\npayload with a generated canonical local `LocalResultStore` /\n`ExperimentRegistry` scenario.",
        mutated="The dashboard still uses fixture-backed showcase data.\nNo public hosted URL or visual screenshot baseline is claimed.",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_f_nextjs_showcase_review_tracks_superseding_public_and_payload_lanes"),
    ),
    MutationSpec(
        name="governance-f-cr-superseded-fixture-boundary",
        path=".agents/specs/f-public-static-showcase/change-requests/cr-fps-002-hosting-content-hash-proof.md",
        original="The current dashboard payload boundary is superseded by CR-FPS-006: generated canonical local `LocalResultStore` / `ExperimentRegistry` scenario evidence, still `local_demo_only`.",
        mutated="The dashboard payload remains fixture-backed and `local_demo_only`.",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_f_public_static_showcase_crs_do_not_republish_superseded_fixture_boundary"),
    ),
    MutationSpec(
        name="governance-stale-visual-evidence-regression",
        path=".agents/specs/SPECS.md",
        original="current CR-FPS-006/009 browser visual diff is `236 / 1,296,000`",
        mutated="visual diff `1089 / 1,296,000`",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_traceability_visual_evidence_tracks_current_pixel_diff"),
    ),
    MutationSpec(
        name="browser-visual-doc-sync-gate-regression",
        path="frontend/scripts/browser-visual-smoke.mjs",
        original="assertCommittedDocsFresh(evidence, diff);",
        mutated="assertCommittedDocsFreshSkipped(evidence, diff);",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_browser_visual_smoke_fails_closed_on_stale_committed_docs"),
    ),
    MutationSpec(
        name="public-hosting-manifest-status-overclaim",
        path="docs/deployment-manifest.json",
        original='"status": "configured_not_observed"',
        mutated='"status": "proven"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_public_hosting_manifest_carries_observed_proof"),
    ),
    MutationSpec(
        name="public-hosting-probe-status-overclaim",
        path="docs/public-hosting-probe.json",
        original='"status": "configured_not_observed"',
        mutated='"status": "proven"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_public_hosting_manifest_carries_observed_proof"),
    ),
    MutationSpec(
        name="review-public-hosting-probe-status-overclaim",
        path="docs/review/assets/public-hosting-probe.json",
        original='"status": "configured_not_observed"',
        mutated='"status": "proven"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_public_hosting_manifest_carries_observed_proof"),
    ),
    MutationSpec(
        name="public-hosting-manifest-hash-overclaim",
        path="docs/deployment-manifest.json",
        original='"hashStatus": "mismatched"',
        mutated='"hashStatus": "matched"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_public_hosting_manifest_carries_observed_proof"),
    ),
    MutationSpec(
        name="public-hosting-probe-hash-overclaim",
        path="docs/public-hosting-probe.json",
        original='"hashStatus": "mismatched"',
        mutated='"hashStatus": "matched"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_public_hosting_manifest_carries_observed_proof"),
    ),
    MutationSpec(
        name="public-hosting-probe-expected-hash-drift",
        path="docs/public-hosting-probe.json",
        original=f'"expectedDataHash": "{_public_probe_expected_hash()}"',
        mutated='"expectedDataHash": "269bb251c5480976e98ec6533b1fdbbbc2b383b85fd0cae4852aec859be1922c"',
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
        name="public-hosting-taxonomy-authority-regression",
        path="docs/DEMO_RISK_WARNING_TAXONOMY.md",
        original="CR-FPS-001 + CR-FPS-002 + CR-FPS-003 + CR-FPS-007 + CR-FPS-008",
        mutated="CR-FPS-001 + CR-FPS-002 + CR-FPS-003 + CR-FPS-007",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_demo_risk_taxonomy_names_current_public_hosting_authority"),
    ),
    MutationSpec(
        name="manual-showcase-payload-sync-regression",
        path="docs/manual/assets/showcase.json",
        original=f'"{_showcase_pytest_label()}"',
        mutated='"271 passed"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_stakeholder_payload_assets_are_synchronized"),
    ),
    MutationSpec(
        name="frontend-showcase-payload-sync-regression",
        path="frontend/lib/showcase-payload.json",
        original=f'"{_showcase_pytest_label()}"',
        mutated='"271 passed"',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_stakeholder_payload_assets_are_synchronized"),
    ),
    MutationSpec(
        name="review-pytest-gate-transcript-regression",
        path="docs/review/assets/gate-pytest.txt",
        original=_showcase_pytest_label(),
        mutated="271 passed",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_review_gate_transcripts_match_published_evidence"),
    ),
    MutationSpec(
        name="governance-test-registry-count-drift",
        path=".agents/specs/TESTS.md",
        original="Python F 12 passed",
        mutated="Python F 11 passed",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_quantlab_test_registry_governance_rows_match_current_test_inventory"),
    ),
    MutationSpec(
        name="mutation-test-registry-count-drift",
        path="quantlab/TESTS.md",
        original="test_mutation_spot_checks` | mutation runner apply/restore PBT, ambiguity rejection, killed/survived behavior, bytecode purge, CLI smoke, machine-readable JSON report summary, A0 event replay mutation listing, root Torch dependency, scheduled observer, E production-tier gate, E production probe, and E readiness CLI mutation listing | A0 mutation automation + CR-A0 event replay + B/F/G mutation registry + ops-visual-drift-artifacts + a-torch-default-dependency-isolation + b-scheduled-run-observer + e-tier3-production-evidence-gate + e-tier3-production-probes + e-tier3-readiness-proof-cli | 10 pass |",
        mutated="test_mutation_spot_checks` | mutation runner apply/restore PBT, ambiguity rejection, killed/survived behavior, bytecode purge, CLI smoke, machine-readable JSON report summary, A0 event replay mutation listing, root Torch dependency, scheduled observer, E production-tier gate, E production probe, and E readiness CLI mutation listing | A0 mutation automation + CR-A0 event replay + B/F/G mutation registry + ops-visual-drift-artifacts + a-torch-default-dependency-isolation + b-scheduled-run-observer + e-tier3-production-evidence-gate + e-tier3-production-probes + e-tier3-readiness-proof-cli | 9 pass |",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_quantlab_test_registry_governance_rows_match_current_test_inventory"),
    ),
    MutationSpec(
        name="python-mutation-report-survivor-drift",
        path="docs/review/assets/gate-python-mutation.json",
        original='"survived": 0',
        mutated='"survived": 1',
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_mutation_count_is_single_source_synced_across_governance_surfaces"),
    ),
    MutationSpec(
        name="review-frontend-count-shorthand-regression",
        path="docs/review/index.html",
        original="<b>44</b><span>frontend tests passing</span>",
        mutated="<b>29</b><span>frontend tests passing</span>",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_review_gate_transcripts_match_published_evidence"),
    ),
    MutationSpec(
        name="review-frontend-coverage-artifact-drift",
        path="docs/review/assets/gate-frontend-coverage.txt",
        original="F Next.js line coverage 89.85%",
        mutated="F Next.js line coverage 88.00%",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_review_gate_transcripts_match_published_evidence"),
    ),
    MutationSpec(
        name="review-audit-gate-transcript-regression",
        path="docs/review/assets/gate-frontend-audit.txt",
        original="found 0 vulnerabilities",
        mutated="found 1 vulnerability",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_governance_guards.py::test_current_review_gate_transcripts_match_published_evidence"),
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


def build_report(specs: Sequence[MutationSpec], results: Sequence[bool]) -> dict[str, object]:
    if len(specs) != len(results):
        raise ValueError("mutation report requires one result per selected mutation")
    mutations = [
        {"name": spec.name, "status": "killed" if killed else "survived"}
        for spec, killed in zip(specs, results)
    ]
    killed_count = sum(1 for killed in results if killed)
    survived_count = len(results) - killed_count
    return {
        "status": "passed" if survived_count == 0 else "failed",
        "total": len(results),
        "killed": killed_count,
        "survived": survived_count,
        "mutations": mutations,
    }


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(report, indent=2)}\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list available mutation names")
    parser.add_argument("--only", action="append", default=[], help="run one mutation by name; repeatable")
    parser.add_argument("--report-json", type=Path, help="write machine-readable mutation summary JSON")
    args = parser.parse_args(argv)

    if args.list:
        for spec in MUTATIONS:
            print(spec.name)
        return 0

    root = Path(__file__).resolve().parents[1]
    specs = selected_specs(args.only)
    results = [run_mutation(root, spec) for spec in specs]
    if args.report_json:
        write_report(args.report_json, build_report(specs, results))
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
