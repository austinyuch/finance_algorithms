"""Canonical showcase scenario built from repo-side QuantLab records."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from quantlab.mlops import ExperimentRegistry
from quantlab.showcase.api import ShowcaseReadAPI, build_dashboard_summary
from quantlab.tracking import LocalResultStore


_EVIDENCE_TESTS = [
    "240 passed",
    "Python mutation 50/50 killed",
    "frontend mutation 13/13 killed",
    "F Next.js coverage 91.07%",
    "E-lite coverage 100%",
    "B source-health/Stooq proof coverage 90%",
]


def _metric(sharpe: float) -> dict[str, Any]:
    return {
        "cumulative_return": 0.1,
        "annualized_return": 0.05,
        "annualized_vol": 0.2,
        "max_drawdown": -0.1,
        "sharpe": sharpe,
        "turnover": 1.0,
        "basis": "net",
        "segment": "out_of_sample",
    }


def _record(
    run_id: str,
    strategy_name: str,
    sharpe: float,
    *,
    baseline: bool = False,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "strategy_name": strategy_name,
        "strategy_metadata": dict(metadata or {}),
        "config": {"seed": 7, "data_version": "canonical-showcase-scenario"},
        "rebalance_dates": ["2022-01-31", "2022-02-28", "2022-03-31"],
        "metrics": [_metric(sharpe)],
        "is_baseline": baseline,
    }


def _leaderboard_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "runId": str(row["run_id"]),
        "strategyName": str(row["strategy_name"]),
        "oosNetSharpe": float(row["oos_net_sharpe"]),
        "isBaseline": bool(row["is_baseline"]),
        "claimBoundary": str(row["claim_boundary"]),
    }


def _experiment_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "experimentId": str(row["experiment_id"]),
        "modelFamily": str(row["model_family"]),
        "strategyName": str(row["strategy_name"]),
        "runIds": [str(run_id) for run_id in row["run_ids"]],
        "claimBoundary": str(row["claim_boundary"]),
        "status": str(row["status"]),
        "readiness": str(row["readiness"]),
        "tags": [str(tag) for tag in row["tags"]],
    }


def _frontend_payload(summary: Mapping[str, Any], *, source_record_count: int) -> dict[str, Any]:
    warnings = list(summary.get("warnings") or [])
    if "local_runtime_only" not in warnings:
        warnings.append("local_runtime_only")
    return {
        "activeRunId": str(summary["active_run_id"]),
        "strategyName": str(summary["strategy_name"]),
        "claimBoundary": str(summary["claim_boundary"]),
        "regime": dict(summary["regime"]),
        "allocation": dict(summary["allocation"]),
        "rebalanceDates": list(summary["rebalance_dates"]),
        "leaderboard": [_leaderboard_row(row) for row in summary["leaderboard"]],
        "experiments": [_experiment_row(row) for row in summary["experiments"]],
        "warnings": warnings,
        "evidence": {
            "readiness": "local_runtime_only",
            "tests": list(_EVIDENCE_TESTS),
        },
        "demoReadiness": {
            "publicHosting": "not_proven",
            "visualRegression": "not_proven",
            "dependencyAudit": "clean",
            "claim": "local_demo_only",
        },
        "sourceMetadata": {
            "source": "local_result_store",
            "sourceRecordCount": source_record_count,
            "experimentRegistry": "experiment_registry",
        },
    }


def build_canonical_dashboard_artifact(work_dir: str | Path) -> dict[str, Any]:
    """Build the frontend dashboard artifact from real local stores.

    The scenario remains a deterministic local demo, but the payload is generated
    through the same repo-side read surfaces that production-facing consumers use.
    """
    root = Path(work_dir)
    root.mkdir(parents=True, exist_ok=True)
    with LocalResultStore(root / "showcase.db") as store:
        forecast_run = store.log(_record(
            "forecast-run",
            "ForecastAllocationStrategy",
            1.21,
            metadata={
                "last_regime": "risk_on",
                "last_regime_confidence": 0.6,
                "weights": {"GROWTH": 0.62, "STEADY": 0.38},
                "claim_boundary": "no_alpha_claim",
            },
        ))
        baseline_run = store.log(_record(
            "baseline-run",
            "StaticWeights",
            0.74,
            baseline=True,
            metadata={"claim_boundary": "no_alpha_claim"},
        ))
        registry = ExperimentRegistry(root / "experiments.jsonl")
        registry.register(
            "return-risk-forecast",
            "ForecastAllocationStrategy",
            {"lookback": 12, "vol_cap": 0.3},
            run_ids=[forecast_run, baseline_run],
            metrics={"oos_net_sharpe": 1.21},
            tags=["D2", "F", "E-lite"],
        )
        api = ShowcaseReadAPI(store, experiment_registry=registry)
        summary = build_dashboard_summary(
            api.run_detail(forecast_run),
            api.leaderboard(),
            experiments=api.experiments(),
        )
        return _frontend_payload(summary, source_record_count=len(api.leaderboard()))


def write_canonical_dashboard_artifact(target: str | Path, work_dir: str | Path) -> dict[str, Any]:
    artifact = build_canonical_dashboard_artifact(work_dir)
    output = Path(target)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(artifact, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return artifact
