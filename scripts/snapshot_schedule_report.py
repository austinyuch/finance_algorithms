#!/usr/bin/env python3
"""Build append-only schedule evidence from daily snapshot reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.snapshot_ops_gate import validate_snapshot_report


def build_schedule_report(report: Mapping[str, Any], *, frequency: str = "daily") -> dict[str, Any]:
    if frequency != "daily":
        raise ValueError("only daily snapshot scheduling is supported")
    summary = validate_snapshot_report(report, allow_failures=True, require_live_jobs=False)
    return {
        "artifact_kind": "snapshot_schedule_report",
        "claim_boundary": "source_contract_status_only",
        "available_date": summary["available_date"],
        "frequency": frequency,
        "status": summary["status"],
        "counts": summary["counts"],
        "retention": "append_only",
        "latest_pointer": "latest-schedule-report.json",
    }


def build_schedule_run_proof(
    schedule: Mapping[str, Any],
    *,
    workflow: str,
    trigger: str,
    command: str,
    exit_code: int,
    started_at: str,
    finished_at: str,
) -> dict[str, Any]:
    if schedule.get("artifact_kind") != "snapshot_schedule_report":
        raise ValueError("schedule proof requires a snapshot_schedule_report")
    if schedule.get("claim_boundary") != "source_contract_status_only":
        raise ValueError("schedule proof must preserve source_contract_status_only")
    if schedule.get("retention") != "append_only":
        raise ValueError("schedule proof requires append_only retention")
    if not workflow.strip() or not trigger.strip() or not command.strip():
        raise ValueError("schedule proof requires workflow, trigger, and command")
    if not started_at.strip() or not finished_at.strip():
        raise ValueError("schedule proof requires start and finish timestamps")
    evidence_tier = "smoke" if "--dry-run" in command or trigger == "workflow_dispatch" else "live"
    status = "degraded" if exit_code != 0 else str(schedule.get("status") or "unknown")
    return {
        "artifact_kind": "snapshot_schedule_run_proof",
        "claim_boundary": "source_contract_status_only",
        "available_date": schedule["available_date"],
        "workflow": workflow,
        "trigger": trigger,
        "command": command,
        "exit_code": int(exit_code),
        "started_at": started_at,
        "finished_at": finished_at,
        "status": status,
        "evidence_tier": evidence_tier,
        "retention": "append_only",
        "schedule_status": schedule["status"],
        "counts": schedule["counts"],
    }


def write_schedule_report(schedule: Mapping[str, Any], out_dir: str | Path) -> Path:
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    available_date = str(schedule.get("available_date") or "unknown")
    target = target_dir / f"snapshot-schedule-{available_date}.json"
    text = json.dumps(dict(schedule), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    target.write_text(text, encoding="utf-8")
    (target_dir / "latest-schedule-report.json").write_text(text, encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="build snapshot schedule evidence")
    parser.add_argument("report_json", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--proof-json", type=Path)
    parser.add_argument("--workflow", default="manual")
    parser.add_argument("--trigger", default="workflow_dispatch")
    parser.add_argument("--command", default="manual schedule report build")
    parser.add_argument("--exit-code", type=int, default=0)
    parser.add_argument("--started-at", default="unknown")
    parser.add_argument("--finished-at", default="unknown")
    args = parser.parse_args(argv)
    report = json.loads(args.report_json.read_text(encoding="utf-8"))
    schedule = build_schedule_report(report)
    target = write_schedule_report(schedule, args.out_dir)
    if args.proof_json is not None:
        proof = build_schedule_run_proof(
            schedule,
            workflow=args.workflow,
            trigger=args.trigger,
            command=args.command,
            exit_code=args.exit_code,
            started_at=args.started_at,
            finished_at=args.finished_at,
        )
        args.proof_json.parent.mkdir(parents=True, exist_ok=True)
        args.proof_json.write_text(json.dumps(proof, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                   encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
