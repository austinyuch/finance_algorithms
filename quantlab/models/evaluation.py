"""Conservative model-family evaluation summaries for D.

The evaluator consumes completed result records. It ranks only out-of-sample net
metrics and preserves the project-level no-alpha claim boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
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
    return str(metadata.get("claim_boundary") or "no_alpha_claim")


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
