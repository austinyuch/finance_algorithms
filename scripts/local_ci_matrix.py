#!/usr/bin/env python3
"""Local-first CI matrix for repo-runnable workflow gates."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class LocalGate:
    name: str
    scope: str
    command: tuple[str, ...]
    workdir: str
    isolation: str
    evidence: str
    remainder: str


def _artifact_path(out_dir: Path, name: str) -> str:
    return str(out_dir / name)


def build_local_ci_matrix(out_dir: Path | str = Path("artifacts")) -> list[LocalGate]:
    """Return the repo-runnable CI gates that replace ordinary hosted steps."""
    artifacts = Path(out_dir)
    snapshot_report = _artifact_path(artifacts, "snapshot-report.json")
    schedule_proof = _artifact_path(artifacts, "snapshot-schedule-run-proof.json")
    snapshot_command = (
        "uv",
        "run",
        "python",
        "scripts/daily_snapshot.py",
        "--dry-run",
        "--report-json",
        snapshot_report,
    )
    return [
        LocalGate(
            name="daily-snapshot:dry-run-report",
            scope="replace the workflow Snapshot dry-run report step locally",
            command=snapshot_command,
            workdir=".",
            isolation="generated-artifact",
            evidence=snapshot_report,
            remainder="hosted-only schedule event semantics and artifact upload transport",
        ),
        LocalGate(
            name="daily-snapshot:schedule-proof",
            scope="replace the workflow schedule report/proof build step locally",
            command=(
                "uv",
                "run",
                "python",
                "scripts/snapshot_schedule_report.py",
                snapshot_report,
                "--out-dir",
                str(artifacts),
                "--proof-json",
                schedule_proof,
                "--workflow",
                "daily-snapshot",
                "--trigger",
                "workflow_dispatch",
                "--command",
                "uv run python scripts/daily_snapshot.py --dry-run --report-json "
                + snapshot_report,
                "--exit-code",
                "0",
                "--started-at",
                "<utc-started-at>",
                "--finished-at",
                "<utc-finished-at>",
            ),
            workdir=".",
            isolation="generated-artifact",
            evidence=schedule_proof,
            remainder="hosted-only schedule event semantics and artifact upload transport",
        ),
    ]


def matrix_payload(out_dir: Path | str = Path("artifacts")) -> dict[str, object]:
    return {
        "policy": "local-first-ci",
        "hosted_only": [
            "schedule event semantics",
            "artifact upload transport",
        ],
        "gates": [asdict(gate) for gate in build_local_ci_matrix(out_dir)],
    }


def _resolved_command(gate: LocalGate, *, started_at: str | None = None, finished_at: str | None = None) -> list[str]:
    command = list(gate.command)
    if gate.name == "daily-snapshot:schedule-proof":
        assert started_at is not None
        assert finished_at is not None
        command = [
            started_at if part == "<utc-started-at>" else finished_at if part == "<utc-finished-at>" else part
            for part in command
        ]
    return command


def _run_gate(gate: LocalGate, *, started_at: str | None = None, finished_at: str | None = None) -> int:
    command = _resolved_command(gate, started_at=started_at, finished_at=finished_at)
    completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
    return int(completed.returncode)


def run_matrix(out_dir: Path) -> dict[str, object]:
    gates = build_local_ci_matrix(out_dir)
    results: list[dict[str, object]] = []
    for gate in gates:
        started_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        resolved_command = _resolved_command(gate, started_at=started_at, finished_at=started_at)
        exit_code = _run_gate(gate, started_at=started_at, finished_at=started_at)
        finished_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if gate.name == "daily-snapshot:schedule-proof" and exit_code != 0:
            # Re-run is intentionally not attempted; local-first CI should stop at the first unexplained failure.
            pass
        results.append(
            {
                **asdict(gate),
                "command": resolved_command,
                "exit_code": exit_code,
                "started_at": started_at,
                "finished_at": finished_at,
            }
        )
        if exit_code != 0:
            break
    status = "passed" if results and all(result["exit_code"] == 0 for result in results) else "failed"
    payload: dict[str, object] = {
        "policy": "local-first-ci",
        "status": status,
        "results": results,
        "hosted_only": [
            "schedule event semantics",
            "artifact upload transport",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "local-ci-matrix-report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="list or run repo-local CI equivalents for hosted workflows")
    parser.add_argument("--out-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--list-json", action="store_true", help="print the local CI matrix without executing it")
    parser.add_argument("--run", choices=["daily-snapshot"], help="execute repo-runnable generated-artifact gates")
    args = parser.parse_args(argv)

    if args.list_json:
        print(json.dumps(matrix_payload(args.out_dir), indent=2, sort_keys=True))
        return 0
    if args.run == "daily-snapshot":
        payload = run_matrix(args.out_dir)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["status"] == "passed" else 1
    parser.error("choose --list-json or --run daily-snapshot")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
