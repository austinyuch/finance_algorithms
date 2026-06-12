"""Conservative model-family evaluation summaries for D.

The evaluator consumes completed result records. It ranks only out-of-sample net
metrics and preserves the project-level no-alpha claim boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class ModelFamilyScore:
    run_id: str
    model_family: str
    strategy_name: str
    oos_net_sharpe: float
    is_baseline: bool
    claim_boundary: str = "no_alpha_claim"


def _oos_net_sharpe(record: Mapping[str, Any]) -> float:
    for metric in record.get("metrics", []):
        if metric.get("segment") == "out_of_sample" and metric.get("basis") == "net":
            return float(metric["sharpe"])
    raise ValueError("model evaluation requires out_of_sample net Sharpe")


def _claim_boundary(record: Mapping[str, Any]) -> str:
    metadata = record.get("strategy_metadata") or {}
    claim = metadata.get("claim_boundary")
    if claim != "no_alpha_claim":
        raise ValueError("model evaluation only accepts explicit no_alpha_claim records")
    return str(claim)


def score_model_family(record: Mapping[str, Any], *, model_family: str) -> ModelFamilyScore:
    if _claim_boundary(record) != "no_alpha_claim":
        raise ValueError("model evaluation only accepts no_alpha_claim records")
    family = model_family.strip()
    if not family:
        raise ValueError("model_family is required")
    return ModelFamilyScore(
        run_id=str(record.get("run_id") or ""),
        model_family=family,
        strategy_name=str(record.get("strategy_name") or ""),
        oos_net_sharpe=_oos_net_sharpe(record),
        is_baseline=bool(record.get("is_baseline")),
    )


def build_model_family_evaluation(
    records_by_family: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    scores: list[ModelFamilyScore] = []
    for family, records in records_by_family.items():
        scores.extend(score_model_family(record, model_family=family) for record in records)
    if not scores:
        raise ValueError("model evaluation requires at least one run record")
    rows = sorted(scores, key=lambda score: score.oos_net_sharpe, reverse=True)
    if not any(row.is_baseline for row in rows):
        raise ValueError("model evaluation requires a visible baseline row")
    return {
        "claim_boundary": "no_alpha_claim",
        "metric_authority": "out_of_sample_net_only",
        "rows": [row.__dict__ for row in rows],
        "families": sorted({row.model_family for row in rows}),
        "baseline_run_ids": [row.run_id for row in rows if row.is_baseline],
    }


def build_result_store_family_evaluation(
    store: Any,
    run_ids_by_family: Mapping[str, Sequence[str]],
) -> dict[str, Any]:
    records_by_family = {
        family: [store.get(str(run_id)) for run_id in run_ids]
        for family, run_ids in run_ids_by_family.items()
    }
    report = build_model_family_evaluation(records_by_family)
    return {**report, "source": "local_result_store"}


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_model_family_evaluation_artifact(
    report: Mapping[str, Any],
    *,
    artifact_uri: str,
    generated_at: str,
) -> dict[str, Any]:
    rows = report.get("rows")
    if report.get("claim_boundary") != "no_alpha_claim":
        raise ValueError("evaluation artifact must preserve no_alpha_claim")
    if report.get("metric_authority") != "out_of_sample_net_only":
        raise ValueError("evaluation artifact requires out_of_sample_net_only authority")
    if not isinstance(rows, list) or not rows:
        raise ValueError("evaluation artifact requires rows")
    clean_uri = artifact_uri.strip()
    clean_generated_at = generated_at.strip()
    if not clean_uri or not clean_generated_at:
        raise ValueError("evaluation artifact requires artifact_uri and generated_at")
    payload = {
        "artifact_uri": clean_uri,
        "generated_at": clean_generated_at,
        "report": report,
    }
    checksum = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return {
        "artifact_kind": "model_family_evaluation_artifact",
        "claim_boundary": "no_alpha_claim",
        "metric_authority": "out_of_sample_net_only",
        "source": str(report.get("source", "in_memory_evaluation")),
        "artifact_uri": clean_uri,
        "generated_at": clean_generated_at,
        "row_count": len(rows),
        "report": dict(report),
        "checksum": checksum,
    }


def validate_model_family_evaluation_artifact(artifact: Mapping[str, Any]) -> None:
    if artifact.get("artifact_kind") != "model_family_evaluation_artifact":
        raise ValueError("unknown model family evaluation artifact")
    if artifact.get("claim_boundary") != "no_alpha_claim":
        raise ValueError("evaluation artifact must preserve no_alpha_claim")
    if artifact.get("metric_authority") != "out_of_sample_net_only":
        raise ValueError("evaluation artifact requires out_of_sample_net_only authority")
    report = artifact.get("report")
    if not isinstance(report, Mapping):
        raise ValueError("evaluation artifact requires report")
    rows = report.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("evaluation artifact requires rows")
    if artifact.get("row_count") != len(rows):
        raise ValueError("evaluation artifact row_count mismatch")
    payload = {
        "artifact_uri": artifact.get("artifact_uri"),
        "generated_at": artifact.get("generated_at"),
        "report": report,
    }
    expected = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    if artifact.get("checksum") != expected:
        raise ValueError("evaluation artifact checksum mismatch")


def write_model_family_evaluation_artifact(artifact: Mapping[str, Any], path: str | Path) -> Path:
    validate_model_family_evaluation_artifact(artifact)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dict(artifact), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    return target
