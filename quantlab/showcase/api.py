"""Read-only showcase facade over A0 result-store records.

The functions in this module intentionally preserve A0's OOS-net leaderboard
authority. They shape data for a dashboard, but do not re-score runs.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence


def _claim_boundary(record: Mapping[str, Any] | None = None) -> str:
    metadata = (record or {}).get("strategy_metadata") or {}
    claim = metadata.get("claim_boundary")
    if claim != "no_alpha_claim":
        raise ValueError("showcase records must explicitly preserve claim_boundary=no_alpha_claim")
    return str(claim)


def _metric_by_segment(record: Mapping[str, Any], segment: str = "out_of_sample",
                       basis: str = "net") -> dict[str, Any] | None:
    for metric in record.get("metrics", []):
        if metric.get("segment") == segment and metric.get("basis") == basis:
            return dict(metric)
    return None


def _leaderboard_row(row: Mapping[str, Any], record: Mapping[str, Any] | None = None) -> dict[str, Any]:
    out = dict(row)
    out["claim_boundary"] = _claim_boundary(record)
    return out


class ShowcaseReadAPI:
    """Read-only facade for dashboard consumers."""

    def __init__(self, store: Any, *, experiment_registry: Any | None = None) -> None:
        self._store = store
        self._experiment_registry = experiment_registry

    def leaderboard(self) -> list[dict[str, Any]]:
        rows = []
        for row in self._store.leaderboard():
            run_id = str(row["run_id"])
            rows.append(_leaderboard_row(row, self._store.get(run_id)))
        return rows

    def run_detail(self, run_id: str) -> dict[str, Any]:
        return dict(self._store.get(run_id))

    def experiments(self) -> list[dict[str, Any]]:
        if self._experiment_registry is None:
            return []
        rows = []
        for entry in self._experiment_registry.list():
            rows.append({
                "experiment_id": entry.experiment_id,
                "model_family": entry.model_family,
                "strategy_name": entry.strategy_name,
                "run_ids": list(entry.run_ids),
                "claim_boundary": entry.claim_boundary,
                "status": entry.status,
                "readiness": entry.readiness,
                "tags": list(entry.tags),
            })
        return sorted(rows, key=lambda row: (row["model_family"], row["strategy_name"],
                                             row["experiment_id"]))


def _regime_summary(record: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    metadata = record.get("strategy_metadata") or {}
    label = metadata.get("last_regime")
    if label is None:
        return {"label": "unknown", "confidence": 0.0}, ["missing_regime_metadata"]
    return {
        "label": str(label),
        "confidence": float(metadata.get("last_regime_confidence") or 0.0),
    }, []


def _allocation(record: Mapping[str, Any]) -> dict[str, float]:
    metadata = record.get("strategy_metadata") or {}
    weights = metadata.get("weights") or metadata.get("last_weights") or {}
    if not isinstance(weights, Mapping):
        return {}
    return {str(k): float(v) for k, v in weights.items()}


def build_dashboard_summary(
    run_record: Mapping[str, Any],
    leaderboard: Sequence[Mapping[str, Any]],
    *,
    experiments: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic dashboard payload without mutating source records."""
    record = deepcopy(dict(run_record))
    regime, warnings = _regime_summary(record)
    metric = _metric_by_segment(record) or {}
    return {
        "active_run_id": str(record.get("run_id", "")),
        "strategy_name": str(record.get("strategy_name", "")),
        "claim_boundary": _claim_boundary(record),
        "regime": regime,
        "allocation": _allocation(record),
        "rebalance_dates": list(record.get("rebalance_dates") or []),
        "oos_net_metrics": metric,
        "leaderboard": [dict(row) for row in leaderboard],
        "experiments": [dict(row) for row in (experiments or [])],
        "warnings": warnings,
    }
