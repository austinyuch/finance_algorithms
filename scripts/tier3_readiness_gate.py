#!/usr/bin/env python3
"""Build a Tier3 readiness gate artifact from governed production evidence JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from quantlab.mlops import (
    build_tier3_readiness_gate,
    validate_production_automated_drift_monitoring_evidence,
    validate_production_retraining_evidence,
    validate_production_serving_evidence,
    validate_tier3_run_manifest,
)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def build_gate_from_files(
    *,
    manifest_path: Path,
    serving_evidence_path: Path,
    retraining_evidence_path: Path,
    drift_evidence_path: Path,
) -> dict[str, Any]:
    manifest = _read_json(manifest_path)
    serving = _read_json(serving_evidence_path)
    retraining = _read_json(retraining_evidence_path)
    drift = _read_json(drift_evidence_path)

    validate_tier3_run_manifest(manifest)
    validate_production_serving_evidence(serving)
    validate_production_retraining_evidence(retraining)
    validate_production_automated_drift_monitoring_evidence(drift)

    gate = build_tier3_readiness_gate(
        manifest,
        serving_evidence=serving,
        retraining_evidence=retraining,
        automated_drift_monitoring_evidence=drift,
    )
    if gate["readiness"] != "tier3_ready":
        raise ValueError("validated production evidence did not satisfy Tier3 readiness")
    return gate


def _write_or_print(payload: Mapping[str, Any], out: Path | None) -> None:
    text = json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if out is None:
        print(text, end="")
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="build fail-closed E Tier3 readiness proof artifact")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--serving-evidence", type=Path, required=True)
    parser.add_argument("--retraining-evidence", type=Path, required=True)
    parser.add_argument("--drift-evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    try:
        gate = build_gate_from_files(
            manifest_path=args.manifest,
            serving_evidence_path=args.serving_evidence,
            retraining_evidence_path=args.retraining_evidence,
            drift_evidence_path=args.drift_evidence,
        )
        _write_or_print(gate, args.out)
    except Exception as exc:
        print(f"tier3-readiness-gate: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
