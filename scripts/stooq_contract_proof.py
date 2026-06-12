#!/usr/bin/env python3
"""Stooq opt-in source-contract proof wrapper.

This command intentionally does not re-enable Stooq defaults. It runs an
explicit Stooq-only snapshot attempt and emits a conservative proof artifact:
positive live close rows make the source eligible for opt-in review only.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quantlab.data.source_health import build_source_contract_reopen_evidence, decide_stooq_contract


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _csv_arg_symbols(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _safe_source_id(source_id: str) -> str:
    return source_id.replace(":", "_").replace("^", "idx_")


def _parse_positive_close_row(payload: Mapping[str, Any], fallback_symbol: str) -> dict[str, object]:
    raw = str(payload.get("raw") or "")
    rows = list(csv.DictReader(raw.splitlines()))
    if not rows:
        raise ValueError("Stooq snapshot has no CSV data rows")
    latest = rows[-1]
    event_date = str(payload.get("event_date") or latest.get("Date") or "").strip()
    close_raw = str(latest.get("Close") or "").strip()
    close = float(close_raw)
    if not math.isfinite(close) or close <= 0:
        raise ValueError("Stooq snapshot close must be positive")
    return {
        "symbol": fallback_symbol,
        "event_date": event_date,
        "close": close,
    }


def _rows_from_snapshot_files(report: Mapping[str, Any]) -> tuple[list[dict[str, object]], list[str]]:
    out_dir_raw = report.get("out_dir")
    if not isinstance(out_dir_raw, str) or not out_dir_raw:
        return [], ["report missing out_dir"]

    out_dir = Path(out_dir_raw)
    rows: list[dict[str, object]] = []
    reasons: list[str] = []
    for job in report.get("jobs", []):
        if not isinstance(job, Mapping):
            continue
        source_id = str(job.get("source_id") or "")
        if not source_id.startswith("stooq:"):
            continue
        status = str(job.get("status") or "")
        if status not in {"ok", "skip"}:
            reasons.append(f"{source_id} status {status or 'unknown'}")
            continue
        safe_id = str(job.get("safe_id") or _safe_source_id(source_id))
        path = out_dir / f"{safe_id}.json"
        if not path.exists():
            reasons.append(f"missing snapshot file for {source_id}: {path}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            rows.append(_parse_positive_close_row(payload, source_id.split(":", 1)[1]))
        except Exception as exc:
            reasons.append(f"invalid snapshot file for {source_id}: {type(exc).__name__}: {exc}")
    return rows, reasons


def _available_stooq_health(report: Mapping[str, Any]) -> dict[str, object]:
    source_health = report.get("source_health")
    if not isinstance(source_health, dict):
        source_health = {"claim_boundary": "source_contract_status_only"}
    source_health = dict(source_health)
    stooq = source_health.get("stooq")
    if not isinstance(stooq, dict):
        source_health["stooq"] = {"status": "available", "default_enabled": True}
    elif stooq.get("status") in {"unknown", "available"}:
        source_health["stooq"] = {**stooq, "status": "available", "default_enabled": True}
    return source_health


def build_stooq_contract_proof(
    report: Mapping[str, Any],
    *,
    exit_code: int,
    observed_at: str,
    command: Sequence[str],
) -> dict[str, object]:
    rows, reasons = _rows_from_snapshot_files(report)
    source_health = _available_stooq_health(report)
    status = "not_proven"
    evidence: dict[str, object] | None = None
    decision = decide_stooq_contract(source_health)

    if exit_code != 0:
        reasons.insert(0, f"snapshot command exited {exit_code}")
    elif rows:
        evidence = build_source_contract_reopen_evidence("stooq", rows=rows, observed_at=observed_at)
        decision = decide_stooq_contract(source_health, live_close_rows=rows)
        status = "eligible_for_opt_in_review"
    elif not reasons:
        reasons.append("no Stooq live close rows observed")

    return {
        "artifact_kind": "stooq_contract_proof",
        "source": "stooq",
        "status": status,
        "evidence_tier": "live_source_contract" if status == "eligible_for_opt_in_review" else "not_proven",
        "claim_boundary": "source_contract_status_only",
        "decision": decision,
        "default_enabled": False,
        "observed_at": observed_at,
        "exit_code": exit_code,
        "command": list(command),
        "rows": rows if status == "eligible_for_opt_in_review" else [],
        "reasons": reasons,
        "reopen_evidence": evidence,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run explicit Stooq source-contract proof")
    parser.add_argument("--stooq-symbols", required=True, help="comma-separated Stooq symbols to probe")
    parser.add_argument("--out-root", type=Path, default=REPO_ROOT / "data" / "vintage" / "raw")
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--proof-json", type=Path, required=True)
    parser.add_argument("--observed-at", default=_utc_now())
    args = parser.parse_args(argv)

    symbols = _csv_arg_symbols(args.stooq_symbols)
    if not symbols:
        proof = {
            "artifact_kind": "stooq_contract_proof",
            "source": "stooq",
            "status": "not_proven",
            "evidence_tier": "not_proven",
            "claim_boundary": "source_contract_status_only",
            "decision": {
                "decision": "requires_live_close_rows",
                "claim_boundary": "source_contract_status_only",
                "required_evidence": "non_empty_close_rows_before_default_enable",
                "default_enabled": "false",
            },
            "default_enabled": False,
            "observed_at": args.observed_at,
            "exit_code": 2,
            "command": [],
            "rows": [],
            "reasons": ["--stooq-symbols must contain at least one explicit symbol"],
            "reopen_evidence": None,
        }
        _write_json(args.proof_json, proof)
        return 2

    command = [
        "python",
        "scripts/daily_snapshot.py",
        "--out-root",
        str(args.out_root),
        "--fred-series",
        "",
        "--stooq-symbols",
        ",".join(symbols),
        "--yahoo-symbols",
        "",
        "--no-noaa",
        "--report-json",
        str(args.report_json),
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, check=False)
    if args.report_json.exists():
        report = json.loads(args.report_json.read_text(encoding="utf-8"))
    else:
        report = {
            "out_dir": str(args.out_root / dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")),
            "jobs": [],
            "source_health": {
                "claim_boundary": "source_contract_status_only",
                "stooq": {"status": "unknown", "default_enabled": True, "symbols": symbols},
            },
        }
    proof = build_stooq_contract_proof(
        report,
        exit_code=int(result.returncode),
        observed_at=str(args.observed_at),
        command=command,
    )
    _write_json(args.proof_json, proof)
    return 0 if proof["status"] == "eligible_for_opt_in_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
