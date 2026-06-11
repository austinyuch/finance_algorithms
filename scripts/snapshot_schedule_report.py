#!/usr/bin/env python3
"""Build append-only schedule evidence from daily snapshot reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

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
    args = parser.parse_args(argv)
    report = json.loads(args.report_json.read_text(encoding="utf-8"))
    target = write_schedule_report(build_schedule_report(report), args.out_dir)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
