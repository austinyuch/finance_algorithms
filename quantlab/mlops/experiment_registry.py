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
