#!/usr/bin/env python3
"""Validate machine-readable daily snapshot reports for ops handoff.

This gate is intentionally report-only. It does not turn partial live-source
failure into production readiness; it verifies the run is explicit about source
outcomes, Stooq policy, and the source-contract claim boundary.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


def _counts(report: Mapping[str, Any]) -> Mapping[str, Any]:
    counts = report.get("counts")
    if not isinstance(counts, Mapping):
        raise ValueError("snapshot report missing counts")
    for key in ("ok", "skip", "fail", "dry"):
        value = counts.get(key)
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"snapshot report count {key} must be a non-negative integer")
    return counts


def validate_snapshot_report(
    report: Mapping[str, Any],
    *,
    allow_failures: bool = False,
    require_live_jobs: bool = True,
) -> dict[str, Any]:
    counts = _counts(report)
    jobs = report.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("snapshot report must include job outcomes")
    if require_live_jobs and bool(report.get("dry_run")):
        raise ValueError("live snapshot ops gate requires a non-dry-run report")

    source_health = report.get("source_health")
    if not isinstance(source_health, Mapping):
        raise ValueError("snapshot report missing source_health")
    if source_health.get("claim_boundary") != "source_contract_status_only":
        raise ValueError("source health must remain source_contract_status_only")
    stooq = source_health.get("stooq")
    if not isinstance(stooq, Mapping) or stooq.get("status") != "blocked" or stooq.get("default_enabled") is not False:
        raise ValueError("Stooq must remain blocked/default-disabled unless source contract changes")

    total = int(counts["ok"]) + int(counts["skip"]) + int(counts["fail"]) + int(counts["dry"])
    if total != len(jobs):
        raise ValueError("snapshot report counts do not match job outcomes")
    if int(counts["fail"]) > 0 and not allow_failures:
        raise ValueError("snapshot report contains failed sources")
    if int(counts["ok"]) + int(counts["skip"]) + int(counts["dry"]) == 0:
        raise ValueError("snapshot report has no successful, skipped, or dry-run work")

    return {
        "claim_boundary": "source_contract_status_only",
        "available_date": str(report.get("available_date", "")),
        "dry_run": bool(report.get("dry_run")),
        "counts": dict(counts),
        "status": "partial" if int(counts["fail"]) else "clean",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="validate daily snapshot report JSON")
    parser.add_argument("report_json", type=Path)
    parser.add_argument("--allow-failures", action="store_true")
    parser.add_argument("--allow-dry-run", action="store_true")
    args = parser.parse_args(argv)

    report = json.loads(args.report_json.read_text(encoding="utf-8"))
    summary = validate_snapshot_report(
        report,
        allow_failures=args.allow_failures,
        require_live_jobs=not args.allow_dry_run,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"snapshot-ops-gate: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
