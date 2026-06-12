#!/usr/bin/env python3
"""Classify GitHub Actions scheduled snapshot proof without overclaiming manual runs."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


def _run_id(run: Mapping[str, Any]) -> int:
    value = run.get("databaseId") or run.get("id") or 0
    return int(value)


def _created_at(run: Mapping[str, Any]) -> str:
    return str(run.get("createdAt") or "")


def _latest(runs: Iterable[Mapping[str, Any]]) -> dict[str, Any] | None:
    ordered = sorted((dict(run) for run in runs), key=lambda run: (_created_at(run), _run_id(run)))
    return ordered[-1] if ordered else None


def build_scheduled_run_observation(runs: list[Mapping[str, Any]], *, workflow: str) -> dict[str, Any]:
    if not workflow.strip():
        raise ValueError("workflow is required")
    schedule_runs = [run for run in runs if run.get("event") == "schedule"]
    manual_successes = [
        run for run in runs
        if run.get("event") == "workflow_dispatch"
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
    ]
    schedule_successes = [
        run for run in schedule_runs
        if run.get("status") == "completed" and run.get("conclusion") == "success"
    ]
    failed_schedule_runs = [
        run for run in schedule_runs
        if run.get("status") == "completed" and run.get("conclusion") != "success"
    ]

    latest_schedule_success = _latest(schedule_successes)
    status = "proven" if latest_schedule_success is not None else "pending"
    return {
        "artifact_kind": "scheduled_run_observation",
        "claim_boundary": "manual_dispatch_is_not_cron",
        "workflow": workflow,
        "status": status,
        "evidence_tier": "live" if status == "proven" else "external_pending",
        "latest_schedule_success": latest_schedule_success,
        "latest_schedule_attempt": _latest(schedule_runs),
        "latest_failed_schedule": _latest(failed_schedule_runs),
        "latest_manual_success": _latest(manual_successes),
        "observed_run_count": len(runs),
        "schedule_run_count": len(schedule_runs),
        "next_action": (
            "cron event=schedule proof observed"
            if status == "proven"
            else "wait for or inspect a completed GitHub Actions event=schedule run"
        ),
    }


def write_scheduled_run_observation(observation: Mapping[str, Any], out_dir: str | Path) -> Path:
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "scheduled-run-observation.json"
    target.write_text(json.dumps(dict(observation), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    return target


def _load_runs_from_gh(workflow: str, limit: int) -> list[Mapping[str, Any]]:
    result = subprocess.run(
        [
            "gh", "run", "list",
            "--workflow", workflow,
            "--limit", str(limit),
            "--json",
            "databaseId,event,status,conclusion,headBranch,createdAt,updatedAt,displayTitle,url",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, list):
        raise ValueError("gh run list did not return a list")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="observe scheduled GitHub Actions proof without overclaiming")
    parser.add_argument("--workflow", default="daily-snapshot.yml")
    parser.add_argument("--runs-json", type=Path, help="pre-fetched gh run list JSON")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)

    if args.runs_json is None:
        runs = _load_runs_from_gh(args.workflow, args.limit)
    else:
        runs = json.loads(args.runs_json.read_text(encoding="utf-8"))
        if not isinstance(runs, list):
            raise ValueError("--runs-json must contain a list")

    observation = build_scheduled_run_observation(runs, workflow=args.workflow)
    target = write_scheduled_run_observation(observation, args.out_dir)
    print(target)
    return 0 if observation["status"] == "proven" else 2


if __name__ == "__main__":
    raise SystemExit(main())
