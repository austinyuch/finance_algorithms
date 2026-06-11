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
from typing import Any, Mapping, Sequence


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
