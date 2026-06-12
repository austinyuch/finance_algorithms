#!/usr/bin/env python3
"""Run and classify broad daily snapshot source-quorum proof attempts."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.snapshot_ops_gate import validate_source_quorum_report

QUORUM_FRED_SERIES = "FEDFUNDS,SP500,PCOPPUSDM"
QUORUM_YAHOO_SYMBOLS = "2330.TW,^TWII"


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def build_snapshot_command(
    *,
    report_json: Path,
    out_root: Path,
    python_executable: str = "python",
) -> list[str]:
    return [
        python_executable,
        "scripts/daily_snapshot.py",
        "--out-root",
        str(out_root),
        "--fred-series",
        QUORUM_FRED_SERIES,
        "--yahoo-symbols",
        QUORUM_YAHOO_SYMBOLS,
        "--report-json",
        str(report_json),
    ]


def build_source_quorum_proof(
    report: Mapping[str, Any],
    *,
    snapshot_exit_code: int,
    command: Sequence[str],
    observed_at: str,
    gate_error: str | None = None,
) -> dict[str, Any]:
    proof: dict[str, Any] = {
        "artifact_kind": "source_quorum_proof",
        "claim_boundary": "source_contract_status_only",
        "available_date": str(report.get("available_date", "")),
        "command": list(command),
        "snapshot_exit_code": int(snapshot_exit_code),
        "observed_at": observed_at,
        "evidence_tier": "live_source_quorum_attempt",
        "status": "not_proven",
        "counts": dict(report.get("counts", {})) if isinstance(report.get("counts"), Mapping) else {},
    }
    try:
        if snapshot_exit_code != 0:
            raise ValueError(f"snapshot command exited {snapshot_exit_code}")
        summary = validate_source_quorum_report(report)
        files = validate_quorum_snapshot_files(report)
    except Exception as exc:
        proof["gate_error"] = gate_error or f"{type(exc).__name__}: {exc}"
        return proof

    proof.update({
        "status": "proven",
        "evidence_tier": "live_source_quorum",
        "groups": summary["groups"],
        "snapshot_files": files,
    })
    return proof


def validate_quorum_snapshot_files(report: Mapping[str, Any]) -> dict[str, str]:
    out_dir = report.get("out_dir")
    if not isinstance(out_dir, str) or not out_dir:
        raise ValueError("source quorum proof requires report out_dir")
    jobs = report.get("jobs")
    if not isinstance(jobs, list):
        raise ValueError("source quorum proof requires report jobs")

    files: dict[str, str] = {}
    for job in jobs:
        if not isinstance(job, Mapping):
            raise ValueError("source quorum proof job must be an object")
        status = str(job.get("status", ""))
        if status not in {"ok", "skip"}:
            continue
        source_id = str(job.get("source_id", ""))
        safe_id = str(job.get("safe_id", ""))
        if not source_id or not safe_id:
            raise ValueError("source quorum proof jobs require source_id and safe_id")
        path = Path(out_dir) / f"{safe_id}.json"
        if not path.exists():
            raise ValueError(f"source quorum proof missing snapshot file for {source_id}: {path}")
        files[source_id] = str(path)
    return files


def write_source_quorum_proof(proof: Mapping[str, Any], proof_json: Path) -> None:
    proof_json.parent.mkdir(parents=True, exist_ok=True)
    proof_json.write_text(json.dumps(dict(proof), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="run and classify broad source-quorum proof")
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--proof-json", type=Path, required=True)
    parser.add_argument("--python", default="python")
    args = parser.parse_args(argv)

    command = build_snapshot_command(
        report_json=args.report_json,
        out_root=args.out_root,
        python_executable=args.python,
    )
    started_at = _utc_now()
    result = subprocess.run(command, cwd=REPO_ROOT, check=False)
    observed_at = _utc_now()

    if args.report_json.exists():
        report = json.loads(args.report_json.read_text(encoding="utf-8"))
        gate_error = None
    else:
        report = {
            "available_date": started_at[:10],
            "counts": {},
        }
        gate_error = "snapshot command did not write report-json"

    proof = build_source_quorum_proof(
        report,
        snapshot_exit_code=result.returncode,
        command=command,
        observed_at=observed_at,
        gate_error=gate_error,
    )
    write_source_quorum_proof(proof, args.proof_json)
    print(json.dumps(proof, sort_keys=True))
    return 0 if proof["status"] == "proven" else 1


if __name__ == "__main__":
    raise SystemExit(main())
