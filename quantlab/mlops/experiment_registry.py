"""Registry-first experiment lineage for E-lite.

This is intentionally not a serving, retraining, or drift-monitoring layer. It
keeps reproducible research configs discoverable and preserves the no-alpha
claim boundary for dashboard consumers.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlparse


@dataclass(frozen=True)
class ExperimentEntry:
    experiment_id: str
    model_family: str
    strategy_name: str
    config: dict[str, Any]
    run_ids: list[str]
    metrics: dict[str, float]
    claim_boundary: str
    tags: list[str]
    status: str = "research_only"
    readiness: str = "registry_only"


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_native(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _checksum(entries: Sequence[Mapping[str, Any]]) -> str:
    return hashlib.sha256(_canonical_json({"entries": _json_native(list(entries))}).encode("utf-8")).hexdigest()


def _experiment_id(model_family: str, strategy_name: str, config: Mapping[str, Any]) -> str:
    payload = _canonical_json({
        "model_family": model_family.strip(),
        "strategy_name": strategy_name.strip(),
        "config": dict(config),
    })
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class ExperimentRegistry:
    """Append-backed JSONL registry with deterministic experiment ids."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def register(
        self,
        model_family: str,
        strategy_name: str,
        config: Mapping[str, Any],
        *,
        run_ids: Sequence[str] | None = None,
        metrics: Mapping[str, float] | None = None,
        claim_boundary: str = "no_alpha_claim",
        tags: Sequence[str] | None = None,
    ) -> ExperimentEntry:
        if claim_boundary != "no_alpha_claim":
            raise ValueError("experiment registry only accepts no_alpha_claim entries")
        family = model_family.strip()
        strategy = strategy_name.strip()
        if not family or not strategy:
            raise ValueError("model_family and strategy_name are required")
        entry = ExperimentEntry(
            experiment_id=_experiment_id(family, strategy, config),
            model_family=family,
            strategy_name=strategy,
            config=dict(config),
            run_ids=[str(run_id) for run_id in (run_ids or [])],
            metrics={str(key): float(value) for key, value in (metrics or {}).items()},
            claim_boundary=claim_boundary,
            tags=[str(tag) for tag in (tags or [])],
        )
        if self.get(entry.experiment_id) is None:
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(asdict(entry), ensure_ascii=False, sort_keys=True) + "\n")
        return entry

    def list(self) -> list[ExperimentEntry]:
        if not self._path.exists():
            return []
        entries = []
        with self._path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                entries.append(ExperimentEntry(**json.loads(line)))
        return entries

    def get(self, experiment_id: str) -> ExperimentEntry | None:
        for entry in self.list():
            if entry.experiment_id == experiment_id:
                return entry
        return None

    def snapshot_artifact(self) -> dict[str, Any]:
        entries = [asdict(entry) for entry in self.list()]
        return {
            "artifact_kind": "experiment_registry_snapshot",
            "claim_boundary": "no_alpha_claim",
            "readiness": "registry_only",
            "entries": entries,
            "checksum": _checksum(entries),
        }

    def write_snapshot(self, path: str | Path) -> dict[str, Any]:
        artifact = self.snapshot_artifact()
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                          encoding="utf-8")
        return artifact


def validate_registry_snapshot(artifact: Mapping[str, Any]) -> None:
    if artifact.get("artifact_kind") != "experiment_registry_snapshot":
        raise ValueError("unknown registry snapshot artifact")
    if artifact.get("claim_boundary") != "no_alpha_claim":
        raise ValueError("registry snapshot must preserve no_alpha_claim")
    if artifact.get("readiness") != "registry_only":
        raise ValueError("registry snapshot must remain registry_only")
    entries = artifact.get("entries")
    if not isinstance(entries, list):
        raise ValueError("registry snapshot entries must be a list")
    for entry in entries:
        if not isinstance(entry, Mapping) or entry.get("claim_boundary") != "no_alpha_claim":
            raise ValueError("registry snapshot entry must preserve no_alpha_claim")
    if artifact.get("checksum") != _checksum(entries):
        raise ValueError("registry snapshot checksum mismatch")


def load_registry_snapshot(path: str | Path) -> list[ExperimentEntry]:
    artifact = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_registry_snapshot(artifact)
    return [ExperimentEntry(**entry) for entry in artifact["entries"]]


def build_tier3_run_manifest(
    registry_snapshot: Mapping[str, Any],
    *,
    artifact_uri: str,
) -> dict[str, Any]:
    validate_registry_snapshot(registry_snapshot)
    uri = artifact_uri.strip()
    if not uri:
        raise ValueError("artifact_uri is required")
    entries = registry_snapshot["entries"]
    return {
        "artifact_kind": "tier3_run_manifest",
        "claim_boundary": "no_alpha_claim",
        "readiness": "artifact_manifest_only",
        "serving_status": "not_serving",
        "retraining_status": "not_configured",
        "drift_monitoring_status": "skeleton_only",
        "artifact_uri": uri,
        "entry_count": len(entries),
        "experiment_ids": [str(entry["experiment_id"]) for entry in entries],
        "registry_checksum": registry_snapshot["checksum"],
    }


def validate_tier3_run_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("artifact_kind") != "tier3_run_manifest":
        raise ValueError("unknown tier3 manifest artifact")
    if manifest.get("claim_boundary") != "no_alpha_claim":
        raise ValueError("tier3 manifest must preserve no_alpha_claim")
    if manifest.get("readiness") != "artifact_manifest_only":
        raise ValueError("tier3 manifest must remain artifact_manifest_only")
    if manifest.get("serving_status") != "not_serving":
        raise ValueError("tier3 manifest must not claim serving")
    if not isinstance(manifest.get("experiment_ids"), list):
        raise ValueError("tier3 manifest experiment_ids must be a list")


_TIER3_READY_EVIDENCE_KEYS = [
    "serving_evidence",
    "retraining_evidence",
    "automated_drift_monitoring_evidence",
]


def _is_production_evidence(value: Mapping[str, Any] | None, target: str) -> bool:
    if not isinstance(value, Mapping):
        return False
    try:
        if target == "serving_evidence":
            validate_production_serving_evidence(value)
        elif target == "retraining_evidence":
            validate_production_retraining_evidence(value)
        elif target == "automated_drift_monitoring_evidence":
            validate_production_automated_drift_monitoring_evidence(value)
        else:
            return False
    except ValueError:
        return False
    return True


def build_tier3_readiness_gate(
    manifest: Mapping[str, Any],
    *,
    serving_evidence: Mapping[str, Any] | None = None,
    retraining_evidence: Mapping[str, Any] | None = None,
    automated_drift_monitoring_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    validate_tier3_run_manifest(manifest)
    evidence = {
        "serving_evidence": dict(serving_evidence or {}),
        "retraining_evidence": dict(retraining_evidence or {}),
        "automated_drift_monitoring_evidence": dict(automated_drift_monitoring_evidence or {}),
    }
    evidence_digests = {
        key: _digest_payload(payload)
        for key, payload in evidence.items()
    }
    missing = [
        key for key in _TIER3_READY_EVIDENCE_KEYS
        if not _is_production_evidence(evidence[key], key)
    ]
    return {
        "artifact_kind": "tier3_readiness_gate",
        "claim_boundary": "no_alpha_claim",
        "readiness": "tier3_ready" if not missing else "not_ready",
        "source_manifest_readiness": manifest["readiness"],
        "manifest_digest": _digest_payload(dict(manifest)),
        "required_evidence": list(_TIER3_READY_EVIDENCE_KEYS),
        "missing_evidence": missing,
        "evidence_digests": evidence_digests,
        "serving_evidence_digest": evidence_digests["serving_evidence"],
        "retraining_evidence_digest": evidence_digests["retraining_evidence"],
        "automated_drift_monitoring_evidence_digest": evidence_digests["automated_drift_monitoring_evidence"],
        "serving_evidence": evidence["serving_evidence"],
        "retraining_evidence": evidence["retraining_evidence"],
        "automated_drift_monitoring_evidence": evidence["automated_drift_monitoring_evidence"],
    }


def _digest_payload(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(_json_native(value)).encode("utf-8")).hexdigest()


def build_serving_smoke_evidence(
    entry: ExperimentEntry,
    *,
    health_check: Callable[[], Mapping[str, Any]],
    predict: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    sample_request: Mapping[str, Any],
    observed_at: str,
    endpoint: str = "in_process",
) -> dict[str, Any]:
    """Build local serving smoke evidence from a real health + predict call."""
    if entry.claim_boundary != "no_alpha_claim":
        raise ValueError("serving smoke only accepts no_alpha_claim entries")
    if not observed_at.strip():
        raise ValueError("serving smoke requires observed_at")
    request = _json_native(dict(sample_request))
    if not isinstance(request, Mapping) or not request:
        raise ValueError("serving smoke requires a non-empty sample_request")
    health = _json_native(dict(health_check()))
    if str(health.get("status") or "").lower() != "ok":
        raise ValueError("serving smoke requires a healthy endpoint")
    prediction = _json_native(dict(predict(request)))
    if not isinstance(prediction, Mapping) or not prediction:
        raise ValueError("serving smoke requires a non-empty prediction")
    if prediction.get("claim_boundary", "no_alpha_claim") != "no_alpha_claim":
        raise ValueError("serving smoke prediction must preserve no_alpha_claim")
    return {
        "artifact_kind": "serving_smoke_evidence",
        "claim_boundary": "no_alpha_claim",
        "readiness_evidence_for": "serving_evidence",
        "evidence_tier": "local_smoke",
        "status": "proven",
        "serving_status": "local_smoke",
        "experiment_id": entry.experiment_id,
        "model_family": entry.model_family,
        "strategy_name": entry.strategy_name,
        "observed_at": observed_at,
        "endpoint": endpoint,
        "health": health,
        "request_digest": _digest_payload(request),
        "prediction_digest": _digest_payload(prediction),
    }


def validate_serving_smoke_evidence(evidence: Mapping[str, Any]) -> None:
    if evidence.get("artifact_kind") != "serving_smoke_evidence":
        raise ValueError("unknown serving smoke evidence artifact")
    if evidence.get("claim_boundary") != "no_alpha_claim":
        raise ValueError("serving smoke evidence must preserve no_alpha_claim")
    if evidence.get("readiness_evidence_for") != "serving_evidence":
        raise ValueError("serving smoke evidence has wrong readiness target")
    if evidence.get("evidence_tier") != "local_smoke":
        raise ValueError("serving smoke evidence must remain local_smoke tier")
    if evidence.get("status") != "proven":
        raise ValueError("serving smoke evidence must be proven")
    if evidence.get("serving_status") != "local_smoke":
        raise ValueError("serving smoke evidence must remain local_smoke")
    health = evidence.get("health")
    if not isinstance(health, Mapping) or str(health.get("status") or "").lower() != "ok":
        raise ValueError("serving smoke evidence requires healthy health payload")
    for key in ["experiment_id", "observed_at", "request_digest", "prediction_digest"]:
        if not str(evidence.get(key) or "").strip():
            raise ValueError(f"serving smoke evidence missing {key}")


def build_retraining_smoke_evidence(
    entry: ExperimentEntry,
    *,
    retrain: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    training_request: Mapping[str, Any],
    observed_at: str,
    runner: str = "in_process",
) -> dict[str, Any]:
    """Build local retraining smoke evidence from a real retrain callable."""
    if entry.claim_boundary != "no_alpha_claim":
        raise ValueError("retraining smoke only accepts no_alpha_claim entries")
    if not observed_at.strip():
        raise ValueError("retraining smoke requires observed_at")
    request = _json_native(dict(training_request))
    if not isinstance(request, Mapping) or not request:
        raise ValueError("retraining smoke requires a non-empty training_request")
    result = _json_native(dict(retrain(request)))
    if not isinstance(result, Mapping) or not result:
        raise ValueError("retraining smoke requires a non-empty result")
    if str(result.get("status") or "").lower() != "completed":
        raise ValueError("retraining smoke requires completed status")
    if result.get("claim_boundary", "no_alpha_claim") != "no_alpha_claim":
        raise ValueError("retraining smoke result must preserve no_alpha_claim")
    run_id = str(result.get("run_id") or "").strip()
    if not run_id:
        raise ValueError("retraining smoke requires run_id")
    return {
        "artifact_kind": "retraining_smoke_evidence",
        "claim_boundary": "no_alpha_claim",
        "readiness_evidence_for": "retraining_evidence",
        "evidence_tier": "local_smoke",
        "status": "proven",
        "retraining_status": "local_smoke",
        "experiment_id": entry.experiment_id,
        "model_family": entry.model_family,
        "strategy_name": entry.strategy_name,
        "observed_at": observed_at,
        "runner": runner,
        "run_id": run_id,
        "oos_net_metrics": _oos_net_metrics(result),
        "request_digest": _digest_payload(request),
        "result_digest": _digest_payload(result),
    }


def validate_retraining_smoke_evidence(evidence: Mapping[str, Any]) -> None:
    if evidence.get("artifact_kind") != "retraining_smoke_evidence":
        raise ValueError("unknown retraining smoke evidence artifact")
    if evidence.get("claim_boundary") != "no_alpha_claim":
        raise ValueError("retraining smoke evidence must preserve no_alpha_claim")
    if evidence.get("readiness_evidence_for") != "retraining_evidence":
        raise ValueError("retraining smoke evidence has wrong readiness target")
    if evidence.get("evidence_tier") != "local_smoke":
        raise ValueError("retraining smoke evidence must remain local_smoke tier")
    if evidence.get("status") != "proven":
        raise ValueError("retraining smoke evidence must be proven")
    if evidence.get("retraining_status") != "local_smoke":
        raise ValueError("retraining smoke evidence must remain local_smoke")
    metrics = evidence.get("oos_net_metrics")
    if not isinstance(metrics, Mapping) or not metrics:
        raise ValueError("retraining smoke evidence requires out_of_sample net metrics")
    for key in ["experiment_id", "observed_at", "run_id", "request_digest", "result_digest"]:
        if not str(evidence.get(key) or "").strip():
            raise ValueError(f"retraining smoke evidence missing {key}")


def build_automated_drift_monitoring_evidence(
    entry: ExperimentEntry,
    *,
    monitor: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    monitor_request: Mapping[str, Any],
    observed_at: str,
    runner: str = "in_process",
) -> dict[str, Any]:
    """Build local automated drift-monitoring smoke evidence from a monitor callable."""
    if entry.claim_boundary != "no_alpha_claim":
        raise ValueError("automated drift monitoring only accepts no_alpha_claim entries")
    if not observed_at.strip():
        raise ValueError("automated drift monitoring requires observed_at")
    request = _json_native(dict(monitor_request))
    if not isinstance(request, Mapping) or not request:
        raise ValueError("automated drift monitoring requires a non-empty monitor_request")
    result = _json_native(dict(monitor(request)))
    if not isinstance(result, Mapping) or not result:
        raise ValueError("automated drift monitoring requires a non-empty result")
    if result.get("claim_boundary", "no_alpha_claim") != "no_alpha_claim":
        raise ValueError("automated drift monitoring result must preserve no_alpha_claim")
    if result.get("status") not in {"stable", "drift_detected"}:
        raise ValueError("automated drift monitoring status must be stable or drift_detected")
    deltas = result.get("metric_deltas")
    if not isinstance(deltas, Mapping) or not deltas:
        raise ValueError("automated drift monitoring requires metric_deltas")
    return {
        "artifact_kind": "automated_drift_monitoring_evidence",
        "claim_boundary": "no_alpha_claim",
        "readiness_evidence_for": "automated_drift_monitoring_evidence",
        "evidence_tier": "local_smoke",
        "status": "proven",
        "monitoring_status": "local_automated_smoke",
        "drift_status": str(result["status"]),
        "experiment_id": entry.experiment_id,
        "model_family": entry.model_family,
        "strategy_name": entry.strategy_name,
        "observed_at": observed_at,
        "runner": runner,
        "metric_deltas": {str(key): float(value) for key, value in deltas.items()},
        "threshold": float(result.get("threshold", request.get("threshold", 0.0))),
        "request_digest": _digest_payload(request),
        "result_digest": _digest_payload(result),
    }


def validate_automated_drift_monitoring_evidence(evidence: Mapping[str, Any]) -> None:
    if evidence.get("artifact_kind") != "automated_drift_monitoring_evidence":
        raise ValueError("unknown automated drift monitoring evidence artifact")
    if evidence.get("claim_boundary") != "no_alpha_claim":
        raise ValueError("automated drift monitoring evidence must preserve no_alpha_claim")
    if evidence.get("readiness_evidence_for") != "automated_drift_monitoring_evidence":
        raise ValueError("automated drift monitoring evidence has wrong readiness target")
    if evidence.get("evidence_tier") != "local_smoke":
        raise ValueError("automated drift monitoring evidence must remain local_smoke tier")
    if evidence.get("status") != "proven":
        raise ValueError("automated drift monitoring evidence must be proven")
    if evidence.get("monitoring_status") != "local_automated_smoke":
        raise ValueError("automated drift monitoring evidence must remain local_automated_smoke")
    if evidence.get("drift_status") not in {"stable", "drift_detected"}:
        raise ValueError("unknown automated drift monitoring drift status")
    deltas = evidence.get("metric_deltas")
    if not isinstance(deltas, Mapping) or not deltas:
        raise ValueError("automated drift monitoring evidence requires metric_deltas")
    for key in ["experiment_id", "observed_at", "request_digest", "result_digest"]:
        if not str(evidence.get(key) or "").strip():
            raise ValueError(f"automated drift monitoring evidence missing {key}")


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
    if not normalized or _is_local_identity(normalized):
        raise ValueError(f"production evidence requires an external {label}")
    return normalized


def _require_external_proof_id(value: str) -> str:
    proof_id = value.strip()
    if not proof_id:
        raise ValueError("production evidence requires external_proof_id")
    return proof_id


def build_production_serving_evidence(
    entry: ExperimentEntry,
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
    if not observed_at.strip():
        raise ValueError("production serving evidence requires observed_at")
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
    if prediction_payload.get("claim_boundary", "no_alpha_claim") != "no_alpha_claim":
        raise ValueError("production serving prediction must preserve no_alpha_claim")
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
        "observed_at": observed_at,
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
    for key in ["experiment_id", "observed_at", "request_digest", "prediction_digest"]:
        if not str(evidence.get(key) or "").strip():
            raise ValueError(f"production serving evidence missing {key}")


def build_production_retraining_evidence(
    entry: ExperimentEntry,
    *,
    orchestrator: str,
    result: Mapping[str, Any],
    observed_at: str,
    external_proof_id: str,
) -> dict[str, Any]:
    """Build production retraining evidence from an externally orchestrated run result."""
    if entry.claim_boundary != "no_alpha_claim":
        raise ValueError("production retraining evidence only accepts no_alpha_claim entries")
    if not observed_at.strip():
        raise ValueError("production retraining evidence requires observed_at")
    external_orchestrator = _require_external_identity(orchestrator, "orchestrator")
    proof_id = _require_external_proof_id(external_proof_id)
    payload = _json_native(dict(result))
    if not isinstance(payload, Mapping) or not payload:
        raise ValueError("production retraining evidence requires a non-empty result")
    if str(payload.get("status") or "").lower() != "completed":
        raise ValueError("production retraining evidence requires completed status")
    if payload.get("claim_boundary", "no_alpha_claim") != "no_alpha_claim":
        raise ValueError("production retraining result must preserve no_alpha_claim")
    run_id = str(payload.get("run_id") or "").strip()
    artifact_uri = str(payload.get("artifact_uri") or "").strip()
    if not run_id:
        raise ValueError("production retraining evidence requires run_id")
    if not artifact_uri:
        raise ValueError("production retraining evidence requires artifact_uri")
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
        "observed_at": observed_at,
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
    metrics = evidence.get("oos_net_metrics")
    if not isinstance(metrics, Mapping) or not metrics:
        raise ValueError("production retraining evidence requires out_of_sample net metrics")
    for key in ["experiment_id", "observed_at", "run_id", "artifact_uri", "result_digest"]:
        if not str(evidence.get(key) or "").strip():
            raise ValueError(f"production retraining evidence missing {key}")


def build_production_automated_drift_monitoring_evidence(
    entry: ExperimentEntry,
    *,
    monitor: str,
    result: Mapping[str, Any],
    observed_at: str,
    external_proof_id: str,
) -> dict[str, Any]:
    """Build production automated drift-monitoring evidence from an external monitor result."""
    if entry.claim_boundary != "no_alpha_claim":
        raise ValueError("production drift monitoring evidence only accepts no_alpha_claim entries")
    if not observed_at.strip():
        raise ValueError("production drift monitoring evidence requires observed_at")
    external_monitor = _require_external_identity(monitor, "monitor")
    proof_id = _require_external_proof_id(external_proof_id)
    payload = _json_native(dict(result))
    if not isinstance(payload, Mapping) or not payload:
        raise ValueError("production drift monitoring evidence requires a non-empty result")
    if payload.get("claim_boundary", "no_alpha_claim") != "no_alpha_claim":
        raise ValueError("production drift monitoring result must preserve no_alpha_claim")
    if payload.get("status") not in {"stable", "drift_detected"}:
        raise ValueError("production drift monitoring status must be stable or drift_detected")
    deltas = payload.get("metric_deltas")
    if not isinstance(deltas, Mapping) or not deltas:
        raise ValueError("production drift monitoring evidence requires metric_deltas")
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
        "observed_at": observed_at,
        "monitor": external_monitor,
        "external_proof_id": proof_id,
        "metric_deltas": {str(key): float(value) for key, value in deltas.items()},
        "threshold": float(payload.get("threshold", 0.0)),
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
    for key in ["experiment_id", "observed_at", "result_digest"]:
        if not str(evidence.get(key) or "").strip():
            raise ValueError(f"production drift monitoring evidence missing {key}")


def build_drift_report_skeleton(
    entry: ExperimentEntry,
    *,
    reference_window: str,
    current_window: str,
) -> dict[str, Any]:
    if entry.claim_boundary != "no_alpha_claim":
        raise ValueError("drift skeleton only accepts no_alpha_claim entries")
    if not reference_window.strip() or not current_window.strip():
        raise ValueError("drift skeleton requires reference and current windows")
    return {
        "artifact_kind": "drift_report_skeleton",
        "claim_boundary": "no_alpha_claim",
        "experiment_id": entry.experiment_id,
        "model_family": entry.model_family,
        "reference_window": reference_window,
        "current_window": current_window,
        "status": "not_assessed",
        "action": "manual_review_required",
    }


def build_drift_assessment_report(
    entry: ExperimentEntry,
    *,
    reference_metrics: Mapping[str, float],
    current_metrics: Mapping[str, float],
    threshold: float,
    observed_at: str,
) -> dict[str, Any]:
    if entry.claim_boundary != "no_alpha_claim":
        raise ValueError("drift assessment only accepts no_alpha_claim entries")
    if threshold <= 0:
        raise ValueError("drift threshold must be positive")
    if not observed_at.strip():
        raise ValueError("drift assessment requires observed_at")
    keys = sorted(set(reference_metrics) & set(current_metrics))
    if not keys:
        raise ValueError("drift assessment requires overlapping metrics")
    deltas = {
        key: float(current_metrics[key]) - float(reference_metrics[key])
        for key in keys
    }
    status = "drift_detected" if any(abs(delta) > threshold for delta in deltas.values()) else "stable"
    return {
        "artifact_kind": "drift_assessment_report",
        "claim_boundary": "no_alpha_claim",
        "experiment_id": entry.experiment_id,
        "model_family": entry.model_family,
        "monitoring_status": "assessed_not_automated",
        "serving_status": "not_serving",
        "retraining_status": "not_configured",
        "observed_at": observed_at,
        "threshold": float(threshold),
        "status": status,
        "reference_metrics": {str(key): float(value) for key, value in reference_metrics.items()},
        "current_metrics": {str(key): float(value) for key, value in current_metrics.items()},
        "metric_deltas": deltas,
    }


def validate_drift_assessment_report(report: Mapping[str, Any]) -> None:
    if report.get("artifact_kind") != "drift_assessment_report":
        raise ValueError("unknown drift assessment artifact")
    if report.get("claim_boundary") != "no_alpha_claim":
        raise ValueError("drift assessment must preserve no_alpha_claim")
    if report.get("monitoring_status") != "assessed_not_automated":
        raise ValueError("drift assessment must remain assessed_not_automated")
    if report.get("serving_status") != "not_serving":
        raise ValueError("drift assessment must not claim serving")
    if report.get("retraining_status") != "not_configured":
        raise ValueError("drift assessment must not claim retraining")
    if not isinstance(report.get("metric_deltas"), Mapping) or not report["metric_deltas"]:
        raise ValueError("drift assessment requires metric_deltas")
    if report.get("status") not in {"stable", "drift_detected"}:
        raise ValueError("unknown drift assessment status")


def _oos_net_metrics(record: Mapping[str, Any]) -> dict[str, float]:
    for metric in record.get("metrics", []):
        if metric.get("segment") == "out_of_sample" and metric.get("basis") == "net":
            return {str(key): float(value) for key, value in metric.items()
                    if isinstance(value, (int, float)) and key not in {"segment", "basis"}}
    raise ValueError("run record missing out_of_sample net metrics")


def register_result_store_runs(
    registry: ExperimentRegistry,
    store: Any,
    *,
    model_family: str,
    strategy_name: str,
    config: Mapping[str, Any],
    run_ids: Sequence[str],
    tags: Sequence[str] | None = None,
) -> ExperimentEntry:
    if not run_ids:
        raise ValueError("run_ids are required")
    records = [store.get(str(run_id)) for run_id in run_ids]
    for record in records:
        metadata = record.get("strategy_metadata") or {}
        if metadata.get("claim_boundary", "no_alpha_claim") != "no_alpha_claim":
            raise ValueError("result-store bridge only accepts no_alpha_claim runs")
    primary_metrics = _oos_net_metrics(records[0])
    return registry.register(
        model_family,
        strategy_name,
        config,
        run_ids=run_ids,
        metrics=primary_metrics,
        claim_boundary="no_alpha_claim",
        tags=tags,
    )
