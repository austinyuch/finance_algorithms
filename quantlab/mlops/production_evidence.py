"""Production-tier evidence builders for E-lite readiness gates."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping
from urllib.parse import urlparse


_EXTERNAL_ARTIFACT_URI_SCHEMES = frozenset({"https", "s3", "gs", "az", "abfs", "abfss"})
_EXTERNAL_IDENTITY_URI_SCHEMES = frozenset({"https", "github-actions"})


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_native(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _digest_payload(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(_json_native(dict(value))).encode("utf-8")).hexdigest()


def _require_no_alpha_claim(payload: Mapping[str, Any], label: str) -> None:
    if payload.get("claim_boundary") != "no_alpha_claim":
        raise ValueError(f"{label} must preserve no_alpha_claim")


def _is_local_identity(value: str) -> bool:
    normalized = value.strip().lower()
    parsed = urlparse(normalized)
    host = parsed.hostname or ""
    return (
        normalized in {"in_process", "local", "local_smoke", "localhost"}
        or host in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
        or normalized.startswith(("file://", "memory://"))
    )


def _require_production_https(endpoint: str) -> str:
    normalized = endpoint.strip()
    parsed = urlparse(normalized)
    if parsed.scheme != "https" or not parsed.netloc or _is_local_identity(normalized):
        raise ValueError("production serving evidence requires a production HTTPS endpoint")
    return normalized


def _require_external_identity(value: str, label: str) -> str:
    normalized = value.strip()
    parsed = urlparse(normalized)
    if (
        not normalized
        or parsed.scheme not in _EXTERNAL_IDENTITY_URI_SCHEMES
        or not parsed.netloc
        or _is_local_identity(normalized)
    ):
        raise ValueError(f"production evidence requires an external {label} URI")
    return normalized


def _is_external_artifact_uri(value: str) -> bool:
    normalized = value.strip()
    parsed = urlparse(normalized)
    return bool(
        normalized
        and parsed.scheme in _EXTERNAL_ARTIFACT_URI_SCHEMES
        and parsed.netloc
        and not _is_local_identity(normalized)
    )


def _require_positive_threshold(value: Any, label: str) -> float:
    try:
        threshold = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} requires a positive threshold") from exc
    if threshold <= 0:
        raise ValueError(f"{label} requires a positive threshold")
    return threshold


def _require_utc_observed_at(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} requires observed_at")
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} requires observed_at as a UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(None):
        raise ValueError(f"{label} requires observed_at as a UTC timestamp")
    return normalized


def _require_external_proof_id(value: str) -> str:
    proof_id = value.strip()
    if not proof_id:
        raise ValueError("production evidence requires external_proof_id")
    parsed = urlparse(proof_id)
    if parsed.scheme != "https" or not parsed.netloc or _is_local_identity(proof_id):
        raise ValueError("production evidence requires external_proof_id to be a traceable external HTTPS URL")
    return proof_id


def _require_sha256_digest(value: Any, label: str) -> str:
    digest = str(value or "").strip()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest.lower()):
        raise ValueError(f"production evidence requires {label} to be a 64-character SHA-256 hex digest")
    return digest


def _oos_net_metrics(record: Mapping[str, Any]) -> dict[str, float]:
    metrics = record.get("metrics") or record.get("oos_net_metrics") or []
    if isinstance(metrics, Mapping):
        return {str(k): float(v) for k, v in metrics.items()}
    for metric in metrics:
        if metric.get("segment") == "out_of_sample" and metric.get("basis") == "net":
            return {
                str(key): float(value)
                for key, value in metric.items()
                if key not in {"segment", "basis"} and isinstance(value, int | float)
            }
    raise ValueError("result store run must include out_of_sample net metrics")


def build_production_serving_evidence(
    entry: Any,
    *,
    endpoint: str,
    health: Mapping[str, Any],
    sample_request: Mapping[str, Any],
    prediction: Mapping[str, Any],
    observed_at: str,
    external_proof_id: str,
) -> dict[str, Any]:
    """Build production serving evidence from externally observed health and prediction payloads."""
    if entry.claim_boundary != "no_alpha_claim":
        raise ValueError("production serving evidence only accepts no_alpha_claim entries")
    observed = _require_utc_observed_at(observed_at, "production serving evidence")
    production_endpoint = _require_production_https(endpoint)
    proof_id = _require_external_proof_id(external_proof_id)
    request = _json_native(dict(sample_request))
    if not isinstance(request, Mapping) or not request:
        raise ValueError("production serving evidence requires a non-empty sample_request")
    health_payload = _json_native(dict(health))
    if str(health_payload.get("status") or "").lower() != "ok":
        raise ValueError("production serving evidence requires healthy health payload")
    prediction_payload = _json_native(dict(prediction))
    if not isinstance(prediction_payload, Mapping) or not prediction_payload:
        raise ValueError("production serving evidence requires a non-empty prediction")
    _require_no_alpha_claim(prediction_payload, "production serving prediction")
    return {
        "artifact_kind": "production_serving_evidence",
        "claim_boundary": "no_alpha_claim",
        "readiness_evidence_for": "serving_evidence",
        "evidence_tier": "production",
        "status": "proven",
        "serving_status": "production_serving",
        "experiment_id": entry.experiment_id,
        "model_family": entry.model_family,
        "strategy_name": entry.strategy_name,
        "observed_at": observed,
        "endpoint": production_endpoint,
        "external_proof_id": proof_id,
        "health": health_payload,
        "request_digest": _digest_payload(request),
        "prediction_digest": _digest_payload(prediction_payload),
    }


def validate_production_serving_evidence(evidence: Mapping[str, Any]) -> None:
    if evidence.get("artifact_kind") != "production_serving_evidence":
        raise ValueError("unknown production serving evidence artifact")
    if evidence.get("claim_boundary") != "no_alpha_claim":
        raise ValueError("production serving evidence must preserve no_alpha_claim")
    if evidence.get("readiness_evidence_for") != "serving_evidence":
        raise ValueError("production serving evidence has wrong readiness target")
    if evidence.get("evidence_tier") != "production":
        raise ValueError("production serving evidence must remain production tier")
    if evidence.get("status") != "proven":
        raise ValueError("production serving evidence must be proven")
    if evidence.get("serving_status") != "production_serving":
        raise ValueError("production serving evidence must remain production_serving")
    _require_production_https(str(evidence.get("endpoint") or ""))
    _require_external_proof_id(str(evidence.get("external_proof_id") or ""))
    health = evidence.get("health")
    if not isinstance(health, Mapping) or str(health.get("status") or "").lower() != "ok":
        raise ValueError("production serving evidence requires healthy health payload")
    _require_utc_observed_at(str(evidence.get("observed_at") or ""), "production serving evidence")
    if not str(evidence.get("experiment_id") or "").strip():
        raise ValueError("production serving evidence missing experiment_id")
    _require_sha256_digest(evidence.get("request_digest"), "request_digest")
    _require_sha256_digest(evidence.get("prediction_digest"), "prediction_digest")


def build_production_retraining_evidence(
    entry: Any,
    *,
    orchestrator: str,
    result: Mapping[str, Any],
    observed_at: str,
    external_proof_id: str,
) -> dict[str, Any]:
    """Build production retraining evidence from an externally orchestrated run result."""
    if entry.claim_boundary != "no_alpha_claim":
        raise ValueError("production retraining evidence only accepts no_alpha_claim entries")
    observed = _require_utc_observed_at(observed_at, "production retraining evidence")
    external_orchestrator = _require_external_identity(orchestrator, "orchestrator")
    proof_id = _require_external_proof_id(external_proof_id)
    payload = _json_native(dict(result))
    if not isinstance(payload, Mapping) or not payload:
        raise ValueError("production retraining evidence requires a non-empty result")
    if str(payload.get("status") or "").lower() != "completed":
        raise ValueError("production retraining evidence requires completed status")
    _require_no_alpha_claim(payload, "production retraining result")
    run_id = str(payload.get("run_id") or "").strip()
    artifact_uri = str(payload.get("artifact_uri") or "").strip()
    if not run_id:
        raise ValueError("production retraining evidence requires run_id")
    if not _is_external_artifact_uri(artifact_uri):
        raise ValueError("production retraining evidence requires external artifact_uri")
    return {
        "artifact_kind": "production_retraining_evidence",
        "claim_boundary": "no_alpha_claim",
        "readiness_evidence_for": "retraining_evidence",
        "evidence_tier": "production",
        "status": "proven",
        "retraining_status": "production_retraining",
        "experiment_id": entry.experiment_id,
        "model_family": entry.model_family,
        "strategy_name": entry.strategy_name,
        "observed_at": observed,
        "orchestrator": external_orchestrator,
        "external_proof_id": proof_id,
        "run_id": run_id,
        "artifact_uri": artifact_uri,
        "oos_net_metrics": _oos_net_metrics(payload),
        "result_digest": _digest_payload(payload),
    }


def validate_production_retraining_evidence(evidence: Mapping[str, Any]) -> None:
    if evidence.get("artifact_kind") != "production_retraining_evidence":
        raise ValueError("unknown production retraining evidence artifact")
    if evidence.get("claim_boundary") != "no_alpha_claim":
        raise ValueError("production retraining evidence must preserve no_alpha_claim")
    if evidence.get("readiness_evidence_for") != "retraining_evidence":
        raise ValueError("production retraining evidence has wrong readiness target")
    if evidence.get("evidence_tier") != "production":
        raise ValueError("production retraining evidence must remain production tier")
    if evidence.get("status") != "proven":
        raise ValueError("production retraining evidence must be proven")
    if evidence.get("retraining_status") != "production_retraining":
        raise ValueError("production retraining evidence must remain production_retraining")
    _require_external_identity(str(evidence.get("orchestrator") or ""), "orchestrator")
    _require_external_proof_id(str(evidence.get("external_proof_id") or ""))
    if not _is_external_artifact_uri(str(evidence.get("artifact_uri") or "")):
        raise ValueError("production retraining evidence requires external artifact_uri")
    metrics = evidence.get("oos_net_metrics")
    if not isinstance(metrics, Mapping) or not metrics:
        raise ValueError("production retraining evidence requires out_of_sample net metrics")
    _require_utc_observed_at(str(evidence.get("observed_at") or ""), "production retraining evidence")
    for key in ["experiment_id", "run_id", "artifact_uri"]:
        if not str(evidence.get(key) or "").strip():
            raise ValueError(f"production retraining evidence missing {key}")
    _require_sha256_digest(evidence.get("result_digest"), "result_digest")


def build_production_automated_drift_monitoring_evidence(
    entry: Any,
    *,
    monitor: str,
    result: Mapping[str, Any],
    observed_at: str,
    external_proof_id: str,
) -> dict[str, Any]:
    """Build production automated drift-monitoring evidence from an external monitor result."""
    if entry.claim_boundary != "no_alpha_claim":
        raise ValueError("production drift monitoring evidence only accepts no_alpha_claim entries")
    observed = _require_utc_observed_at(observed_at, "production drift monitoring evidence")
    external_monitor = _require_external_identity(monitor, "monitor")
    proof_id = _require_external_proof_id(external_proof_id)
    payload = _json_native(dict(result))
    if not isinstance(payload, Mapping) or not payload:
        raise ValueError("production drift monitoring evidence requires a non-empty result")
    _require_no_alpha_claim(payload, "production drift monitoring result")
    if payload.get("status") not in {"stable", "drift_detected"}:
        raise ValueError("production drift monitoring status must be stable or drift_detected")
    deltas = payload.get("metric_deltas")
    if not isinstance(deltas, Mapping) or not deltas:
        raise ValueError("production drift monitoring evidence requires metric_deltas")
    threshold = _require_positive_threshold(payload.get("threshold"), "production drift monitoring evidence")
    return {
        "artifact_kind": "production_automated_drift_monitoring_evidence",
        "claim_boundary": "no_alpha_claim",
        "readiness_evidence_for": "automated_drift_monitoring_evidence",
        "evidence_tier": "production",
        "status": "proven",
        "monitoring_status": "production_automated_monitoring",
        "drift_status": str(payload["status"]),
        "experiment_id": entry.experiment_id,
        "model_family": entry.model_family,
        "strategy_name": entry.strategy_name,
        "observed_at": observed,
        "monitor": external_monitor,
        "external_proof_id": proof_id,
        "metric_deltas": {str(key): float(value) for key, value in deltas.items()},
        "threshold": threshold,
        "result_digest": _digest_payload(payload),
    }


def validate_production_automated_drift_monitoring_evidence(evidence: Mapping[str, Any]) -> None:
    if evidence.get("artifact_kind") != "production_automated_drift_monitoring_evidence":
        raise ValueError("unknown production automated drift monitoring evidence artifact")
    if evidence.get("claim_boundary") != "no_alpha_claim":
        raise ValueError("production drift monitoring evidence must preserve no_alpha_claim")
    if evidence.get("readiness_evidence_for") != "automated_drift_monitoring_evidence":
        raise ValueError("production drift monitoring evidence has wrong readiness target")
    if evidence.get("evidence_tier") != "production":
        raise ValueError("production drift monitoring evidence must remain production tier")
    if evidence.get("status") != "proven":
        raise ValueError("production drift monitoring evidence must be proven")
    if evidence.get("monitoring_status") != "production_automated_monitoring":
        raise ValueError("production drift monitoring evidence must remain production_automated_monitoring")
    if evidence.get("drift_status") not in {"stable", "drift_detected"}:
        raise ValueError("unknown production drift monitoring status")
    _require_external_identity(str(evidence.get("monitor") or ""), "monitor")
    _require_external_proof_id(str(evidence.get("external_proof_id") or ""))
    deltas = evidence.get("metric_deltas")
    if not isinstance(deltas, Mapping) or not deltas:
        raise ValueError("production drift monitoring evidence requires metric_deltas")
    _require_positive_threshold(evidence.get("threshold"), "production drift monitoring evidence")
    _require_utc_observed_at(str(evidence.get("observed_at") or ""), "production drift monitoring evidence")
    if not str(evidence.get("experiment_id") or "").strip():
        raise ValueError("production drift monitoring evidence missing experiment_id")
    _require_sha256_digest(evidence.get("result_digest"), "result_digest")
