"""CLI tests for production Tier3 readiness proof gate."""
from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path

from quantlab.mlops import (
    ExperimentRegistry,
    build_production_automated_drift_monitoring_evidence,
    build_production_retraining_evidence,
    build_production_serving_evidence,
    build_serving_smoke_evidence,
    build_tier3_run_manifest,
)

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "tier3_readiness_gate.py"


def _load():
    spec = importlib.util.spec_from_file_location("tier3_readiness_gate", MODULE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def _digest(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _production_payloads(tmp_path: Path) -> tuple[dict, dict, dict, dict]:
    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    entry = registry.register("return-risk", "ForecastAllocationStrategy", {"lookback": 12})
    manifest = build_tier3_run_manifest(
        registry.snapshot_artifact(),
        artifact_uri="s3://quant-prod/manifests/return-risk-demo.json",
    )
    serving = build_production_serving_evidence(
        entry,
        endpoint="https://quant.example.com/models/return-risk",
        health={"status": "ok", "model_loaded": True},
        sample_request={"features": {"momentum": 0.6}},
        prediction={"claim_boundary": "no_alpha_claim", "weights": {"A": 0.6, "B": 0.4}},
        observed_at="2026-06-12T06:00:00Z",
        external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
    )
    retraining = build_production_retraining_evidence(
        entry,
        orchestrator="github-actions://finance_algorithms/retrain",
        result={
            "status": "completed",
            "run_id": "train-prod-123",
            "artifact_uri": "s3://quant-prod/models/return-risk/train-prod-123.json",
            "claim_boundary": "no_alpha_claim",
            "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.2}],
        },
        observed_at="2026-06-12T06:10:00Z",
        external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
    )
    drift = build_production_automated_drift_monitoring_evidence(
        entry,
        monitor="https://quant.example.com/monitors/return-risk",
        result={
            "status": "stable",
            "claim_boundary": "no_alpha_claim",
            "metric_deltas": {"oos_net_sharpe": 0.02},
            "threshold": 0.05,
        },
        observed_at="2026-06-12T06:20:00Z",
        external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
    )
    return manifest, serving, retraining, drift


def test_tier3_readiness_gate_cli_writes_ready_artifact(tmp_path):
    mod = _load()
    manifest, serving, retraining, drift = _production_payloads(tmp_path)
    out = tmp_path / "gate.json"

    rc = mod.main([
        "--manifest", str(_write_json(tmp_path / "manifest.json", manifest)),
        "--serving-evidence", str(_write_json(tmp_path / "serving.json", serving)),
        "--retraining-evidence", str(_write_json(tmp_path / "retraining.json", retraining)),
        "--drift-evidence", str(_write_json(tmp_path / "drift.json", drift)),
        "--out", str(out),
    ])
    artifact = json.loads(out.read_text(encoding="utf-8"))

    assert rc == 0
    assert artifact["artifact_kind"] == "tier3_readiness_gate"
    assert artifact["claim_boundary"] == "no_alpha_claim"
    assert artifact["readiness"] == "tier3_ready"
    assert artifact["missing_evidence"] == []
    assert artifact["serving_evidence"]["artifact_kind"] == "production_serving_evidence"
    assert artifact["manifest_digest"] == _digest(manifest)
    assert artifact["evidence_digests"] == {
        "serving_evidence": _digest(serving),
        "retraining_evidence": _digest(retraining),
        "automated_drift_monitoring_evidence": _digest(drift),
    }


def test_tier3_readiness_gate_cli_rejects_local_smoke_evidence(tmp_path):
    mod = _load()
    manifest, _serving, retraining, drift = _production_payloads(tmp_path)
    entry = ExperimentRegistry(tmp_path / "local.jsonl").register("family", "Strategy", {"x": 1})
    local_serving = build_serving_smoke_evidence(
        entry,
        health_check=lambda: {"status": "ok"},
        predict=lambda request: {"claim_boundary": "no_alpha_claim", "ok": True},
        sample_request={"x": 1},
        observed_at="2026-06-12T06:00:00Z",
    )
    out = tmp_path / "gate.json"

    rc = mod.main([
        "--manifest", str(_write_json(tmp_path / "manifest.json", manifest)),
        "--serving-evidence", str(_write_json(tmp_path / "serving.json", local_serving)),
        "--retraining-evidence", str(_write_json(tmp_path / "retraining.json", retraining)),
        "--drift-evidence", str(_write_json(tmp_path / "drift.json", drift)),
        "--out", str(out),
    ])

    assert rc == 1
    assert not out.exists()


def test_tier3_readiness_gate_cli_rejects_spoofed_production_map(tmp_path, capsys):
    mod = _load()
    manifest, _serving, retraining, drift = _production_payloads(tmp_path)
    spoofed_serving = {
        "artifact_kind": "hand_written_map",
        "claim_boundary": "no_alpha_claim",
        "status": "proven",
        "readiness_evidence_for": "serving_evidence",
        "evidence_tier": "production",
    }
    out = tmp_path / "gate.json"

    rc = mod.main([
        "--manifest", str(_write_json(tmp_path / "manifest.json", manifest)),
        "--serving-evidence", str(_write_json(tmp_path / "serving.json", spoofed_serving)),
        "--retraining-evidence", str(_write_json(tmp_path / "retraining.json", retraining)),
        "--drift-evidence", str(_write_json(tmp_path / "drift.json", drift)),
        "--out", str(out),
    ])

    assert rc == 1
    assert not out.exists()
    assert "unknown production serving evidence artifact" in capsys.readouterr().err


def test_tier3_readiness_gate_cli_rejects_mismatched_experiment_binding(tmp_path, capsys):
    mod = _load()
    manifest, serving, _retraining, drift = _production_payloads(tmp_path)
    other_entry = ExperimentRegistry(tmp_path / "other.jsonl").register(
        "robust-portfolio",
        "RobustOptimizationStrategy",
        {"vol_cap": 0.2},
    )
    retraining = build_production_retraining_evidence(
        other_entry,
        orchestrator="github-actions://finance_algorithms/retrain",
        result={
            "status": "completed",
            "run_id": "train-prod-456",
            "artifact_uri": "s3://quant-prod/models/robust-portfolio/train-prod-456.json",
            "claim_boundary": "no_alpha_claim",
            "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.1}],
        },
        observed_at="2026-06-12T06:10:00Z",
        external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/456#retraining",
    )
    out = tmp_path / "gate.json"

    rc = mod.main([
        "--manifest", str(_write_json(tmp_path / "manifest.json", manifest)),
        "--serving-evidence", str(_write_json(tmp_path / "serving.json", serving)),
        "--retraining-evidence", str(_write_json(tmp_path / "retraining.json", retraining)),
        "--drift-evidence", str(_write_json(tmp_path / "drift.json", drift)),
        "--out", str(out),
    ])

    assert rc == 1
    assert not out.exists()
    assert "validated production evidence did not satisfy Tier3 readiness" in capsys.readouterr().err


def test_tier3_readiness_gate_cli_invalid_json_is_chaos_safe(tmp_path):
    mod = _load()
    manifest, _serving, retraining, drift = _production_payloads(tmp_path)
    bad_serving = tmp_path / "serving.json"
    bad_serving.write_text("{not valid json", encoding="utf-8")
    out = tmp_path / "gate.json"

    rc = mod.main([
        "--manifest", str(_write_json(tmp_path / "manifest.json", manifest)),
        "--serving-evidence", str(bad_serving),
        "--retraining-evidence", str(_write_json(tmp_path / "retraining.json", retraining)),
        "--drift-evidence", str(_write_json(tmp_path / "drift.json", drift)),
        "--out", str(out),
    ])

    assert rc == 1
    assert not out.exists()
