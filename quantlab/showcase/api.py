"""Read-only showcase facade over A0 result-store records.

The functions in this module intentionally preserve A0's OOS-net leaderboard
authority. They shape data for a dashboard, but do not re-score runs.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence


def _claim_boundary(record: Mapping[str, Any] | None = None) -> str:
    metadata = (record or {}).get("strategy_metadata") or {}
    return str(metadata.get("claim_boundary") or "no_alpha_claim")


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

    def __init__(self, store: Any) -> None:
        self._store = store

    def leaderboard(self) -> list[dict[str, Any]]:
        rows = []
        for row in self._store.leaderboard():
            run_id = str(row["run_id"])
            rows.append(_leaderboard_row(row, self._store.get(run_id)))
        return rows

    def run_detail(self, run_id: str) -> dict[str, Any]:
        return dict(self._store.get(run_id))


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


def build_dashboard_summary(run_record: Mapping[str, Any],
                            leaderboard: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
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
        "warnings": warnings,
    }
