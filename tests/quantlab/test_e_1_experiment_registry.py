"""E-lite experiment registry tests.

RED: added before quantlab.mlops.experiment_registry exists.
"""
from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st


def test_experiment_registry_persists_model_lineage_and_run_config(tmp_path):
    from quantlab.mlops import ExperimentRegistry

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    entry = registry.register(
        model_family="return-risk-forecast",
        strategy_name="ForecastAllocationStrategy",
        config={"lookback": 12, "vol_cap": 0.30},
        run_ids=["forecast-run", "baseline-run"],
        metrics={"oos_net_sharpe": 1.21},
        claim_boundary="no_alpha_claim",
        tags=["D2", "F"],
    )

    loaded = ExperimentRegistry(tmp_path / "experiments.jsonl").get(entry.experiment_id)

    assert loaded is not None
    assert loaded.model_family == "return-risk-forecast"
    assert loaded.config == {"lookback": 12, "vol_cap": 0.30}
    assert loaded.run_ids == ["forecast-run", "baseline-run"]
    assert loaded.claim_boundary == "no_alpha_claim"
    assert loaded.status == "research_only"


def test_experiment_registry_dedupes_same_config_and_preserves_no_alpha_claim(tmp_path):
    from quantlab.mlops import ExperimentRegistry

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    first = registry.register("robust-portfolio", "RobustOptimizationStrategy", {"vol_cap": 0.2})
    second = registry.register("robust-portfolio", "RobustOptimizationStrategy", {"vol_cap": 0.2})

    assert first.experiment_id == second.experiment_id
    assert len(registry.list()) == 1
    assert registry.list()[0].claim_boundary == "no_alpha_claim"


@given(
    model_family=st.text(min_size=1, max_size=24).filter(lambda s: s.strip() != ""),
    strategy_name=st.text(min_size=1, max_size=24).filter(lambda s: s.strip() != ""),
    vol_cap=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_experiment_registry_roundtrip_preserves_config(tmp_path, model_family, strategy_name, vol_cap):
    from quantlab.mlops import ExperimentRegistry

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    entry = registry.register(model_family, strategy_name, {"vol_cap": vol_cap})
    loaded = ExperimentRegistry(tmp_path / "experiments.jsonl").get(entry.experiment_id)

    assert loaded is not None
    assert loaded.config == {"vol_cap": vol_cap}
    assert loaded.claim_boundary == "no_alpha_claim"
    assert loaded.readiness == "registry_only"


def test_experiment_registry_rejects_alpha_claim(tmp_path):
    from quantlab.mlops import ExperimentRegistry

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")

    with pytest.raises(ValueError, match="no_alpha_claim"):
        registry.register("bad", "BadStrategy", {}, claim_boundary="alpha_claim")


def test_experiment_registry_writes_checksum_snapshot_and_detects_tampering(tmp_path):
    from dataclasses import asdict

    from quantlab.mlops import ExperimentRegistry, load_registry_snapshot, validate_registry_snapshot

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    entry = registry.register("return-risk-forecast", "ForecastAllocationStrategy", {"lookback": 12})

    artifact = registry.write_snapshot(tmp_path / "snapshot.json")
    loaded = load_registry_snapshot(tmp_path / "snapshot.json")

    assert loaded == [entry]
    assert artifact["claim_boundary"] == "no_alpha_claim"
    assert artifact["readiness"] == "registry_only"

    tampered = {**artifact, "entries": [{**asdict(entry), "claim_boundary": "alpha_claim"}]}
    with pytest.raises(ValueError, match="no_alpha_claim"):
        validate_registry_snapshot(tampered)


def test_register_result_store_runs_uses_real_oos_net_metrics(tmp_path):
    from quantlab.mlops import ExperimentRegistry, register_result_store_runs
    from quantlab.tracking import LocalResultStore

    store = LocalResultStore(tmp_path / "runs.sqlite")
    run_id = store.log({
        "strategy_name": "ForecastAllocationStrategy",
        "metrics": [
            {"segment": "in_sample", "basis": "net", "sharpe": 99.0},
            {"segment": "out_of_sample", "basis": "net", "sharpe": 1.23, "max_drawdown": -0.08},
        ],
        "strategy_metadata": {"claim_boundary": "no_alpha_claim"},
    })
    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")

    entry = register_result_store_runs(
        registry,
        store,
        model_family="return-risk-forecast",
        strategy_name="ForecastAllocationStrategy",
        config={"lookback": 12},
        run_ids=[run_id],
        tags=["real-run"],
    )

    assert entry.run_ids == [run_id]
    assert entry.metrics == {"sharpe": 1.23, "max_drawdown": -0.08}
    assert entry.tags == ["real-run"]
    assert entry.claim_boundary == "no_alpha_claim"


def test_register_result_store_runs_rejects_missing_oos_net_metrics(tmp_path):
    from quantlab.mlops import ExperimentRegistry, register_result_store_runs
    from quantlab.tracking import LocalResultStore

    store = LocalResultStore(tmp_path / "runs.sqlite")
    run_id = store.log({
        "strategy_name": "BadStrategy",
        "metrics": [{"segment": "in_sample", "basis": "net", "sharpe": 99.0}],
        "strategy_metadata": {"claim_boundary": "no_alpha_claim"},
    })

    with pytest.raises(ValueError, match="out_of_sample net metrics"):
        register_result_store_runs(
            ExperimentRegistry(tmp_path / "experiments.jsonl"),
            store,
            model_family="bad",
            strategy_name="BadStrategy",
            config={},
            run_ids=[run_id],
        )


def test_tier3_manifest_and_drift_skeleton_remain_non_serving(tmp_path):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_drift_report_skeleton,
        build_tier3_run_manifest,
        validate_tier3_run_manifest,
    )

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    entry = registry.register(
        "robust-portfolio",
        "RobustOptimizationStrategy",
        {"vol_cap": 0.2},
        run_ids=["robust-run"],
        metrics={"sharpe": 0.9},
    )
    snapshot = registry.snapshot_artifact()

    manifest = build_tier3_run_manifest(snapshot, artifact_uri="file://artifacts/robust-run.json")
    validate_tier3_run_manifest(manifest)
    drift = build_drift_report_skeleton(entry, reference_window="2022Q1", current_window="2022Q2")

    assert manifest["readiness"] == "artifact_manifest_only"
    assert manifest["serving_status"] == "not_serving"
    assert manifest["claim_boundary"] == "no_alpha_claim"
    assert manifest["experiment_ids"] == [entry.experiment_id]
    assert drift["status"] == "not_assessed"
    assert drift["action"] == "manual_review_required"


def test_tier3_readiness_gate_fails_closed_for_artifact_only_manifest(tmp_path):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_tier3_readiness_gate,
        build_tier3_run_manifest,
    )

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    registry.register("robust-portfolio", "RobustOptimizationStrategy", {"vol_cap": 0.2})
    manifest = build_tier3_run_manifest(registry.snapshot_artifact(), artifact_uri="file://artifacts/demo.json")

    gate = build_tier3_readiness_gate(manifest)

    assert gate["artifact_kind"] == "tier3_readiness_gate"
    assert gate["readiness"] == "not_ready"
    assert gate["missing_evidence"] == [
        "serving_evidence",
        "retraining_evidence",
        "automated_drift_monitoring_evidence",
    ]
    assert gate["claim_boundary"] == "no_alpha_claim"


def test_tier3_readiness_gate_requires_all_live_evidence(tmp_path):
    from quantlab.mlops import ExperimentRegistry, build_tier3_readiness_gate, build_tier3_run_manifest

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    registry.register("return-risk", "ForecastAllocationStrategy", {"lookback": 12})
    manifest = build_tier3_run_manifest(registry.snapshot_artifact(), artifact_uri="file://artifacts/demo.json")

    partial = build_tier3_readiness_gate(
        manifest,
        serving_evidence={"status": "proven", "url": "http://127.0.0.1:9000/health"},
        retraining_evidence={"status": "proven", "run_id": "train-1"},
    )
    arbitrary_maps = build_tier3_readiness_gate(
        manifest,
        serving_evidence={"status": "proven", "url": "http://127.0.0.1:9000/health"},
        retraining_evidence={"status": "proven", "run_id": "train-1"},
        automated_drift_monitoring_evidence={"status": "proven", "monitor_id": "drift-1"},
    )
    production_looking_maps = build_tier3_readiness_gate(
        manifest,
        serving_evidence={
            "status": "proven",
            "readiness_evidence_for": "serving_evidence",
            "evidence_tier": "production",
        },
        retraining_evidence={
            "status": "proven",
            "readiness_evidence_for": "retraining_evidence",
            "evidence_tier": "production",
        },
        automated_drift_monitoring_evidence={
            "status": "proven",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "production",
        },
    )

    assert partial["readiness"] == "not_ready"
    assert partial["missing_evidence"] == [
        "serving_evidence",
        "retraining_evidence",
        "automated_drift_monitoring_evidence",
    ]
    assert arbitrary_maps["readiness"] == "not_ready"
    assert arbitrary_maps["missing_evidence"] == [
        "serving_evidence",
        "retraining_evidence",
        "automated_drift_monitoring_evidence",
    ]
    assert production_looking_maps["readiness"] == "not_ready"
    assert production_looking_maps["missing_evidence"] == [
        "serving_evidence",
        "retraining_evidence",
        "automated_drift_monitoring_evidence",
    ]
    assert production_looking_maps["required_evidence"] == [
        "serving_evidence",
        "retraining_evidence",
        "automated_drift_monitoring_evidence",
    ]
    assert production_looking_maps["manifest_digest"]
    assert production_looking_maps["evidence_digests"] == {
        "serving_evidence": production_looking_maps["serving_evidence_digest"],
        "retraining_evidence": production_looking_maps["retraining_evidence_digest"],
        "automated_drift_monitoring_evidence": production_looking_maps[
            "automated_drift_monitoring_evidence_digest"
        ],
    }
    assert len(set(production_looking_maps["evidence_digests"].values())) == 3


def test_serving_smoke_evidence_proves_only_serving_slice(tmp_path):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_serving_smoke_evidence,
        build_tier3_readiness_gate,
        build_tier3_run_manifest,
        validate_serving_smoke_evidence,
    )

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    entry = registry.register("return-risk", "ForecastAllocationStrategy", {"lookback": 12})
    manifest = build_tier3_run_manifest(registry.snapshot_artifact(), artifact_uri="file://artifacts/demo.json")

    evidence = build_serving_smoke_evidence(
        entry,
        health_check=lambda: {"status": "ok", "model_loaded": True},
        predict=lambda request: {
            "claim_boundary": "no_alpha_claim",
            "weights": {"A": float(request["features"]["momentum"]), "B": 0.4},
        },
        sample_request={"features": {"momentum": 0.6}},
        observed_at="2026-06-12T02:30:00Z",
    )
    gate = build_tier3_readiness_gate(manifest, serving_evidence=evidence)

    validate_serving_smoke_evidence(evidence)
    assert evidence["status"] == "proven"
    assert evidence["serving_status"] == "local_smoke"
    assert evidence["evidence_tier"] == "local_smoke"
    assert evidence["readiness_evidence_for"] == "serving_evidence"
    assert gate["readiness"] == "not_ready"
    assert gate["missing_evidence"] == [
        "serving_evidence",
        "retraining_evidence",
        "automated_drift_monitoring_evidence",
    ]


def test_serving_smoke_evidence_rejects_unhealthy_or_alpha_claim(tmp_path):
    from quantlab.mlops import ExperimentRegistry, build_serving_smoke_evidence

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register("family", "Strategy", {"x": 1})

    with pytest.raises(ValueError, match="healthy"):
        build_serving_smoke_evidence(
            entry,
            health_check=lambda: {"status": "degraded"},
            predict=lambda request: {"claim_boundary": "no_alpha_claim", "ok": True},
            sample_request={"features": {"x": 1}},
            observed_at="2026-06-12T02:30:00Z",
        )

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_serving_smoke_evidence(
            entry,
            health_check=lambda: {"status": "ok"},
            predict=lambda request: {"claim_boundary": "alpha_claim", "ok": True},
            sample_request={"features": {"x": 1}},
            observed_at="2026-06-12T02:30:00Z",
        )

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_serving_smoke_evidence(
            entry,
            health_check=lambda: {"status": "ok"},
            predict=lambda request: {"ok": True},
            sample_request={"features": {"x": 1}},
            observed_at="2026-06-12T02:30:00Z",
        )


def test_retraining_smoke_evidence_proves_only_retraining_slice(tmp_path):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_retraining_smoke_evidence,
        build_serving_smoke_evidence,
        build_tier3_readiness_gate,
        build_tier3_run_manifest,
        validate_retraining_smoke_evidence,
    )

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    entry = registry.register("return-risk", "ForecastAllocationStrategy", {"lookback": 12})
    manifest = build_tier3_run_manifest(registry.snapshot_artifact(), artifact_uri="file://artifacts/demo.json")
    serving = build_serving_smoke_evidence(
        entry,
        health_check=lambda: {"status": "ok", "model_loaded": True},
        predict=lambda request: {"claim_boundary": "no_alpha_claim", "weights": {"A": 0.6, "B": 0.4}},
        sample_request={"features": {"momentum": 0.6}},
        observed_at="2026-06-12T02:30:00Z",
    )

    evidence = build_retraining_smoke_evidence(
        entry,
        retrain=lambda request: {
            "status": "completed",
            "run_id": "train-1",
            "claim_boundary": "no_alpha_claim",
            "metrics": [
                {"segment": "in_sample", "basis": "net", "sharpe": 99.0},
                {"segment": "out_of_sample", "basis": "net", "sharpe": 1.1, "max_drawdown": -0.07},
            ],
        },
        training_request={"lookback": 12, "seed": 7},
        observed_at="2026-06-12T03:00:00Z",
    )
    gate = build_tier3_readiness_gate(manifest, serving_evidence=serving, retraining_evidence=evidence)

    validate_retraining_smoke_evidence(evidence)
    assert evidence["status"] == "proven"
    assert evidence["retraining_status"] == "local_smoke"
    assert evidence["evidence_tier"] == "local_smoke"
    assert evidence["readiness_evidence_for"] == "retraining_evidence"
    assert evidence["oos_net_metrics"] == {"sharpe": 1.1, "max_drawdown": -0.07}
    assert gate["readiness"] == "not_ready"
    assert gate["missing_evidence"] == [
        "serving_evidence",
        "retraining_evidence",
        "automated_drift_monitoring_evidence",
    ]


def test_automated_drift_monitoring_local_evidence_does_not_make_tier3_ready(tmp_path):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_automated_drift_monitoring_evidence,
        build_retraining_smoke_evidence,
        build_serving_smoke_evidence,
        build_tier3_readiness_gate,
        build_tier3_run_manifest,
        validate_automated_drift_monitoring_evidence,
    )

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    entry = registry.register("return-risk", "ForecastAllocationStrategy", {"lookback": 12})
    manifest = build_tier3_run_manifest(registry.snapshot_artifact(), artifact_uri="file://artifacts/demo.json")
    serving = build_serving_smoke_evidence(
        entry,
        health_check=lambda: {"status": "ok"},
        predict=lambda request: {"claim_boundary": "no_alpha_claim", "weights": {"A": 0.6, "B": 0.4}},
        sample_request={"features": {"momentum": 0.6}},
        observed_at="2026-06-12T02:30:00Z",
    )
    retraining = build_retraining_smoke_evidence(
        entry,
        retrain=lambda request: {
            "status": "completed",
            "run_id": "train-1",
            "claim_boundary": "no_alpha_claim",
            "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.1}],
        },
        training_request={"lookback": 12},
        observed_at="2026-06-12T03:00:00Z",
    )
    drift = build_automated_drift_monitoring_evidence(
        entry,
        monitor=lambda request: {
            "status": "stable",
            "claim_boundary": "no_alpha_claim",
            "metric_deltas": {"oos_net_sharpe": 0.02},
            "threshold": request["threshold"],
        },
        monitor_request={"threshold": 0.05, "window": "2026-06-12"},
        observed_at="2026-06-12T04:00:00Z",
    )
    gate = build_tier3_readiness_gate(
        manifest,
        serving_evidence=serving,
        retraining_evidence=retraining,
        automated_drift_monitoring_evidence=drift,
    )

    validate_automated_drift_monitoring_evidence(drift)
    assert drift["status"] == "proven"
    assert drift["monitoring_status"] == "local_automated_smoke"
    assert drift["evidence_tier"] == "local_smoke"
    assert drift["readiness_evidence_for"] == "automated_drift_monitoring_evidence"
    assert gate["readiness"] == "not_ready"
    assert gate["missing_evidence"] == [
        "serving_evidence",
        "retraining_evidence",
        "automated_drift_monitoring_evidence",
    ]


def test_automated_drift_monitoring_rejects_overclaim_or_bad_status(tmp_path):
    from quantlab.mlops import ExperimentRegistry, build_automated_drift_monitoring_evidence

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register("family", "Strategy", {"x": 1})

    with pytest.raises(ValueError, match="stable or drift_detected"):
        build_automated_drift_monitoring_evidence(
            entry,
            monitor=lambda request: {"status": "unknown", "claim_boundary": "no_alpha_claim", "metric_deltas": {"x": 0.1}},
            monitor_request={"threshold": 0.05},
            observed_at="2026-06-12T04:00:00Z",
        )

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_automated_drift_monitoring_evidence(
            entry,
            monitor=lambda request: {"status": "stable", "claim_boundary": "alpha_claim", "metric_deltas": {"x": 0.1}},
            monitor_request={"threshold": 0.05},
            observed_at="2026-06-12T04:00:00Z",
        )

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_automated_drift_monitoring_evidence(
            entry,
            monitor=lambda request: {"status": "stable", "metric_deltas": {"x": 0.1}},
            monitor_request={"threshold": 0.05},
            observed_at="2026-06-12T04:00:00Z",
        )

    with pytest.raises(ValueError, match="metric_deltas"):
        build_automated_drift_monitoring_evidence(
            entry,
            monitor=lambda request: {"status": "stable", "claim_boundary": "no_alpha_claim", "metric_deltas": {}},
            monitor_request={"threshold": 0.05},
            observed_at="2026-06-12T04:00:00Z",
        )


def test_production_evidence_triplet_satisfies_tier3_gate(tmp_path):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_production_automated_drift_monitoring_evidence,
        build_production_retraining_evidence,
        build_production_serving_evidence,
        build_tier3_readiness_gate,
        build_tier3_run_manifest,
        validate_production_automated_drift_monitoring_evidence,
        validate_production_retraining_evidence,
        validate_production_serving_evidence,
    )

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    entry = registry.register("return-risk", "ForecastAllocationStrategy", {"lookback": 12})
    manifest = build_tier3_run_manifest(registry.snapshot_artifact(), artifact_uri="file://artifacts/demo.json")
    serving = build_production_serving_evidence(
        entry,
        endpoint="https://quant.example.com/models/return-risk",
        health={"status": "ok", "model_loaded": True},
        sample_request={"features": {"momentum": 0.6}},
        prediction={"claim_boundary": "no_alpha_claim", "weights": {"A": 0.6, "B": 0.4}},
        observed_at="2026-06-12T05:00:00Z",
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
        observed_at="2026-06-12T05:10:00Z",
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
        observed_at="2026-06-12T05:20:00Z",
        external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
    )

    validate_production_serving_evidence(serving)
    validate_production_retraining_evidence(retraining)
    validate_production_automated_drift_monitoring_evidence(drift)
    gate = build_tier3_readiness_gate(
        manifest,
        serving_evidence=serving,
        retraining_evidence=retraining,
        automated_drift_monitoring_evidence=drift,
    )

    assert serving["evidence_tier"] == "production"
    assert retraining["evidence_tier"] == "production"
    assert drift["evidence_tier"] == "production"
    assert gate["readiness"] == "tier3_ready"
    assert gate["missing_evidence"] == []
    assert gate["manifest_digest"]
    assert gate["evidence_digests"] == {
        "serving_evidence": gate["serving_evidence_digest"],
        "retraining_evidence": gate["retraining_evidence_digest"],
        "automated_drift_monitoring_evidence": gate["automated_drift_monitoring_evidence_digest"],
    }


def test_production_evidence_requires_traceable_external_proof_uri(tmp_path):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_production_automated_drift_monitoring_evidence,
        build_production_retraining_evidence,
        build_production_serving_evidence,
        validate_production_serving_evidence,
    )

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register(
        "return-risk",
        "ForecastAllocationStrategy",
        {"lookback": 12},
    )

    with pytest.raises(ValueError, match="external_proof_id"):
        build_production_serving_evidence(
            entry,
            endpoint="https://quant.example.com/models/return-risk",
            health={"status": "ok"},
            sample_request={"features": {"momentum": 0.6}},
            prediction={"claim_boundary": "no_alpha_claim", "weights": {"A": 0.6}},
            observed_at="2026-06-12T05:00:00Z",
            external_proof_id="serving-run-123",
        )
    with pytest.raises(ValueError, match="external_proof_id"):
        build_production_retraining_evidence(
            entry,
            orchestrator="github-actions://finance_algorithms/retrain",
            result={
                "status": "completed",
                "run_id": "train-prod-123",
                "artifact_uri": "s3://quant-prod/models/return-risk/train-prod-123.json",
                "claim_boundary": "no_alpha_claim",
                "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.2}],
            },
            observed_at="2026-06-12T05:10:00Z",
            external_proof_id="retrain-run-123",
        )
    with pytest.raises(ValueError, match="external_proof_id"):
        build_production_automated_drift_monitoring_evidence(
            entry,
            monitor="https://quant.example.com/monitors/return-risk",
            result={
                "status": "stable",
                "claim_boundary": "no_alpha_claim",
                "metric_deltas": {"oos_net_sharpe": 0.02},
            },
            observed_at="2026-06-12T05:20:00Z",
            external_proof_id="drift-run-123",
        )

    with pytest.raises(ValueError, match="external_proof_id"):
        validate_production_serving_evidence({
            "artifact_kind": "production_serving_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "serving_status": "production_serving",
            "endpoint": "https://quant.example.com/model",
            "external_proof_id": "serving-run-123",
            "health": {"status": "ok"},
            "experiment_id": entry.experiment_id,
            "observed_at": "2026-06-12T05:00:00Z",
            "request_digest": "abc",
            "prediction_digest": "def",
        })


def test_tier3_gate_rejects_spoofed_production_serving_map(tmp_path):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_production_automated_drift_monitoring_evidence,
        build_production_retraining_evidence,
        build_tier3_readiness_gate,
        build_tier3_run_manifest,
    )

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    entry = registry.register("return-risk", "ForecastAllocationStrategy", {"lookback": 12})
    manifest = build_tier3_run_manifest(registry.snapshot_artifact(), artifact_uri="file://artifacts/demo.json")
    spoofed_serving = {
        "artifact_kind": "hand_written_map",
        "claim_boundary": "no_alpha_claim",
        "status": "proven",
        "readiness_evidence_for": "serving_evidence",
        "evidence_tier": "production",
    }
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
        observed_at="2026-06-12T05:10:00Z",
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
        observed_at="2026-06-12T05:20:00Z",
        external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
    )

    gate = build_tier3_readiness_gate(
        manifest,
        serving_evidence=spoofed_serving,
        retraining_evidence=retraining,
        automated_drift_monitoring_evidence=drift,
    )

    assert gate["readiness"] == "not_ready"
    assert gate["missing_evidence"] == ["serving_evidence"]


def test_production_evidence_rejects_local_or_overclaimed_inputs(tmp_path):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_production_automated_drift_monitoring_evidence,
        build_production_retraining_evidence,
        build_production_serving_evidence,
    )

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register("family", "Strategy", {"x": 1})

    with pytest.raises(ValueError, match="production HTTPS"):
        build_production_serving_evidence(
            entry,
            endpoint="http://127.0.0.1:9000/model",
            health={"status": "ok"},
            sample_request={"x": 1},
            prediction={"claim_boundary": "no_alpha_claim", "ok": True},
            observed_at="2026-06-12T05:00:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
        )

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_production_serving_evidence(
            entry,
            endpoint="https://quant.example.com/model",
            health={"status": "ok"},
            sample_request={"x": 1},
            prediction={"claim_boundary": "alpha_claim", "ok": True},
            observed_at="2026-06-12T05:00:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
        )

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_production_serving_evidence(
            entry,
            endpoint="https://quant.example.com/model",
            health={"status": "ok"},
            sample_request={"x": 1},
            prediction={"ok": True},
            observed_at="2026-06-12T05:00:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
        )

    with pytest.raises(ValueError, match="external orchestrator"):
        build_production_retraining_evidence(
            entry,
            orchestrator="in_process",
            result={
                "status": "completed",
                "run_id": "train-prod-123",
                "artifact_uri": "s3://quant-prod/models/train-prod-123.json",
                "claim_boundary": "no_alpha_claim",
                "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.0}],
            },
            observed_at="2026-06-12T05:10:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
        )

    with pytest.raises(ValueError, match="completed"):
        build_production_retraining_evidence(
            entry,
            orchestrator="github-actions://finance_algorithms/retrain",
            result={
                "status": "failed",
                "run_id": "train-prod-123",
                "artifact_uri": "s3://quant-prod/models/train-prod-123.json",
                "claim_boundary": "no_alpha_claim",
                "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.0}],
            },
            observed_at="2026-06-12T05:10:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
        )

    with pytest.raises(ValueError, match="external monitor"):
        build_production_automated_drift_monitoring_evidence(
            entry,
            monitor="local_smoke",
            result={
                "status": "stable",
                "claim_boundary": "no_alpha_claim",
                "metric_deltas": {"x": 0.1},
            },
            observed_at="2026-06-12T05:20:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
        )

    with pytest.raises(ValueError, match="stable or drift_detected"):
        build_production_automated_drift_monitoring_evidence(
            entry,
            monitor="https://quant.example.com/monitors/return-risk",
            result={
                "status": "unknown",
                "claim_boundary": "no_alpha_claim",
                "metric_deltas": {"x": 0.1},
            },
            observed_at="2026-06-12T05:20:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
        )


@given(
    host=st.sampled_from(["localhost", "127.0.0.1", "0.0.0.0"]),
    scheme=st.sampled_from(["http", "https"]),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_production_serving_rejects_local_endpoint_identities(tmp_path, host, scheme):
    from quantlab.mlops import ExperimentRegistry, build_production_serving_evidence

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register("family", "Strategy", {"x": 1})

    with pytest.raises(ValueError, match="production HTTPS"):
        build_production_serving_evidence(
            entry,
            endpoint=f"{scheme}://{host}:9000/model",
            health={"status": "ok"},
            sample_request={"x": 1},
            prediction={"claim_boundary": "no_alpha_claim", "ok": True},
            observed_at="2026-06-12T05:00:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
        )


def test_retraining_smoke_evidence_rejects_failed_alpha_or_missing_oos(tmp_path):
    from quantlab.mlops import ExperimentRegistry, build_retraining_smoke_evidence

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register("family", "Strategy", {"x": 1})

    with pytest.raises(ValueError, match="completed"):
        build_retraining_smoke_evidence(
            entry,
            retrain=lambda request: {"status": "failed", "run_id": "train-1", "claim_boundary": "no_alpha_claim"},
            training_request={"lookback": 12},
            observed_at="2026-06-12T03:00:00Z",
        )

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_retraining_smoke_evidence(
            entry,
            retrain=lambda request: {"status": "completed", "run_id": "train-1", "claim_boundary": "alpha_claim"},
            training_request={"lookback": 12},
            observed_at="2026-06-12T03:00:00Z",
        )

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_retraining_smoke_evidence(
            entry,
            retrain=lambda request: {"status": "completed", "run_id": "train-1"},
            training_request={"lookback": 12},
            observed_at="2026-06-12T03:00:00Z",
        )

    with pytest.raises(ValueError, match="out_of_sample net metrics"):
        build_retraining_smoke_evidence(
            entry,
            retrain=lambda request: {
                "status": "completed",
                "run_id": "train-1",
                "claim_boundary": "no_alpha_claim",
                "metrics": [{"segment": "in_sample", "basis": "net", "sharpe": 99.0}],
            },
            training_request={"lookback": 12},
            observed_at="2026-06-12T03:00:00Z",
        )


def test_experiment_registry_defensive_validation_branches(tmp_path):
    from dataclasses import replace

    from quantlab.mlops import (
        ExperimentRegistry,
        build_automated_drift_monitoring_evidence,
        build_drift_assessment_report,
        build_drift_report_skeleton,
        build_production_automated_drift_monitoring_evidence,
        build_production_retraining_evidence,
        build_production_serving_evidence,
        build_retraining_smoke_evidence,
        build_serving_smoke_evidence,
        build_tier3_run_manifest,
        register_result_store_runs,
        validate_automated_drift_monitoring_evidence,
        validate_drift_assessment_report,
        validate_production_automated_drift_monitoring_evidence,
        validate_production_retraining_evidence,
        validate_production_serving_evidence,
        validate_registry_snapshot,
        validate_retraining_smoke_evidence,
        validate_serving_smoke_evidence,
        validate_tier3_run_manifest,
    )
    from quantlab.tracking import LocalResultStore

    registry_path = tmp_path / "experiments.jsonl"
    registry_path.write_text("\n", encoding="utf-8")
    registry = ExperimentRegistry(registry_path)
    assert registry.list() == []

    with pytest.raises(ValueError, match="model_family"):
        registry.register("", "Strategy", {"x": 1})

    entry = registry.register("family", "Strategy", {"x": 1})
    alpha_entry = replace(entry, claim_boundary="alpha_claim")
    snapshot = registry.snapshot_artifact()

    for artifact in [
        {"artifact_kind": "bad", "claim_boundary": "no_alpha_claim", "readiness": "registry_only", "entries": []},
        {"artifact_kind": "experiment_registry_snapshot", "claim_boundary": "alpha_claim", "readiness": "registry_only", "entries": []},
        {"artifact_kind": "experiment_registry_snapshot", "claim_boundary": "no_alpha_claim", "readiness": "tier3_ready", "entries": []},
        {"artifact_kind": "experiment_registry_snapshot", "claim_boundary": "no_alpha_claim", "readiness": "registry_only", "entries": {}},
        {"artifact_kind": "experiment_registry_snapshot", "claim_boundary": "no_alpha_claim", "readiness": "registry_only", "entries": [], "checksum": "bad"},
    ]:
        with pytest.raises(ValueError):
            validate_registry_snapshot(artifact)

    with pytest.raises(ValueError, match="artifact_uri"):
        build_tier3_run_manifest(snapshot, artifact_uri=" ")

    for manifest in [
        {"artifact_kind": "bad"},
        {"artifact_kind": "tier3_run_manifest", "claim_boundary": "alpha_claim"},
        {"artifact_kind": "tier3_run_manifest", "claim_boundary": "no_alpha_claim", "readiness": "tier3_ready"},
        {
            "artifact_kind": "tier3_run_manifest",
            "claim_boundary": "no_alpha_claim",
            "readiness": "artifact_manifest_only",
            "serving_status": "serving",
        },
        {
            "artifact_kind": "tier3_run_manifest",
            "claim_boundary": "no_alpha_claim",
            "readiness": "artifact_manifest_only",
            "serving_status": "not_serving",
            "experiment_ids": "not-list",
        },
    ]:
        with pytest.raises(ValueError):
            validate_tier3_run_manifest(manifest)

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_serving_smoke_evidence(
            alpha_entry,
            health_check=lambda: {"status": "ok"},
            predict=lambda request: {"claim_boundary": "no_alpha_claim", "ok": True},
            sample_request={"x": 1},
            observed_at="2026-06-12T02:30:00Z",
        )
    with pytest.raises(ValueError, match="observed_at"):
        build_serving_smoke_evidence(entry, health_check=lambda: {"status": "ok"}, predict=lambda request: {"ok": True}, sample_request={"x": 1}, observed_at=" ")
    with pytest.raises(ValueError, match="sample_request"):
        build_serving_smoke_evidence(entry, health_check=lambda: {"status": "ok"}, predict=lambda request: {"ok": True}, sample_request={}, observed_at="2026-06-12T02:30:00Z")
    with pytest.raises(ValueError, match="prediction"):
        build_serving_smoke_evidence(entry, health_check=lambda: {"status": "ok"}, predict=lambda request: {}, sample_request={"x": 1}, observed_at="2026-06-12T02:30:00Z")

    for evidence in [
        {"artifact_kind": "bad"},
        {"artifact_kind": "serving_smoke_evidence", "claim_boundary": "alpha_claim"},
        {"artifact_kind": "serving_smoke_evidence", "claim_boundary": "no_alpha_claim", "readiness_evidence_for": "wrong"},
        {
            "artifact_kind": "serving_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "evidence_tier": "production",
        },
        {
            "artifact_kind": "serving_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "evidence_tier": "local_smoke",
            "status": "planned",
        },
        {
            "artifact_kind": "serving_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "evidence_tier": "local_smoke",
            "status": "proven",
            "serving_status": "production",
        },
        {
            "artifact_kind": "serving_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "evidence_tier": "local_smoke",
            "status": "proven",
            "serving_status": "local_smoke",
            "health": {"status": "degraded"},
        },
        {
            "artifact_kind": "serving_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "evidence_tier": "local_smoke",
            "status": "proven",
            "serving_status": "local_smoke",
            "health": {"status": "ok"},
        },
    ]:
        with pytest.raises(ValueError):
            validate_serving_smoke_evidence(evidence)

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_retraining_smoke_evidence(alpha_entry, retrain=lambda request: {"status": "completed"}, training_request={"x": 1}, observed_at="2026-06-12T03:00:00Z")
    with pytest.raises(ValueError, match="observed_at"):
        build_retraining_smoke_evidence(entry, retrain=lambda request: {"status": "completed"}, training_request={"x": 1}, observed_at=" ")
    with pytest.raises(ValueError, match="training_request"):
        build_retraining_smoke_evidence(entry, retrain=lambda request: {"status": "completed"}, training_request={}, observed_at="2026-06-12T03:00:00Z")
    with pytest.raises(ValueError, match="result"):
        build_retraining_smoke_evidence(entry, retrain=lambda request: {}, training_request={"x": 1}, observed_at="2026-06-12T03:00:00Z")
    with pytest.raises(ValueError, match="run_id"):
        build_retraining_smoke_evidence(
            entry,
            retrain=lambda request: {
                "status": "completed",
                "claim_boundary": "no_alpha_claim",
                "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.0}],
            },
            training_request={"x": 1},
            observed_at="2026-06-12T03:00:00Z",
        )

    for evidence in [
        {"artifact_kind": "bad"},
        {"artifact_kind": "retraining_smoke_evidence", "claim_boundary": "alpha_claim"},
        {"artifact_kind": "retraining_smoke_evidence", "claim_boundary": "no_alpha_claim", "readiness_evidence_for": "wrong"},
        {
            "artifact_kind": "retraining_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
            "evidence_tier": "production",
        },
        {
            "artifact_kind": "retraining_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
            "evidence_tier": "local_smoke",
            "status": "planned",
        },
        {
            "artifact_kind": "retraining_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
            "evidence_tier": "local_smoke",
            "status": "proven",
            "retraining_status": "production",
        },
        {
            "artifact_kind": "retraining_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
            "evidence_tier": "local_smoke",
            "status": "proven",
            "retraining_status": "local_smoke",
            "oos_net_metrics": {},
        },
        {
            "artifact_kind": "retraining_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
            "evidence_tier": "local_smoke",
            "status": "proven",
            "retraining_status": "local_smoke",
            "oos_net_metrics": {"sharpe": 1.0},
        },
    ]:
        with pytest.raises(ValueError):
            validate_retraining_smoke_evidence(evidence)

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_drift_report_skeleton(alpha_entry, reference_window="2022Q1", current_window="2022Q2")
    with pytest.raises(ValueError, match="reference"):
        build_drift_report_skeleton(entry, reference_window=" ", current_window="2022Q2")
    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_drift_assessment_report(alpha_entry, reference_metrics={"x": 1}, current_metrics={"x": 1}, threshold=0.1, observed_at="2026-06-12T00:00:00Z")
    with pytest.raises(ValueError, match="positive"):
        build_drift_assessment_report(entry, reference_metrics={"x": 1}, current_metrics={"x": 1}, threshold=0, observed_at="2026-06-12T00:00:00Z")
    with pytest.raises(ValueError, match="observed_at"):
        build_drift_assessment_report(entry, reference_metrics={"x": 1}, current_metrics={"x": 1}, threshold=0.1, observed_at=" ")
    with pytest.raises(ValueError, match="overlapping"):
        build_drift_assessment_report(entry, reference_metrics={"x": 1}, current_metrics={"y": 1}, threshold=0.1, observed_at="2026-06-12T00:00:00Z")

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_automated_drift_monitoring_evidence(alpha_entry, monitor=lambda request: {"status": "stable"}, monitor_request={"x": 1}, observed_at="2026-06-12T04:00:00Z")
    with pytest.raises(ValueError, match="observed_at"):
        build_automated_drift_monitoring_evidence(entry, monitor=lambda request: {"status": "stable"}, monitor_request={"x": 1}, observed_at=" ")
    with pytest.raises(ValueError, match="monitor_request"):
        build_automated_drift_monitoring_evidence(entry, monitor=lambda request: {"status": "stable"}, monitor_request={}, observed_at="2026-06-12T04:00:00Z")
    with pytest.raises(ValueError, match="result"):
        build_automated_drift_monitoring_evidence(entry, monitor=lambda request: {}, monitor_request={"x": 1}, observed_at="2026-06-12T04:00:00Z")

    for report in [
        {"artifact_kind": "bad"},
        {"artifact_kind": "drift_assessment_report", "claim_boundary": "no_alpha_claim", "monitoring_status": "automated"},
        {"artifact_kind": "drift_assessment_report", "claim_boundary": "no_alpha_claim", "monitoring_status": "assessed_not_automated", "serving_status": "serving"},
        {
            "artifact_kind": "drift_assessment_report",
            "claim_boundary": "no_alpha_claim",
            "monitoring_status": "assessed_not_automated",
            "serving_status": "not_serving",
            "retraining_status": "configured",
        },
        {
            "artifact_kind": "drift_assessment_report",
            "claim_boundary": "no_alpha_claim",
            "monitoring_status": "assessed_not_automated",
            "serving_status": "not_serving",
            "retraining_status": "not_configured",
            "metric_deltas": {},
        },
        {
            "artifact_kind": "drift_assessment_report",
            "claim_boundary": "no_alpha_claim",
            "monitoring_status": "assessed_not_automated",
            "serving_status": "not_serving",
            "retraining_status": "not_configured",
            "metric_deltas": {"x": 0.1},
            "status": "unknown",
        },
    ]:
        with pytest.raises(ValueError):
            validate_drift_assessment_report(report)

    for evidence in [
        {"artifact_kind": "bad"},
        {"artifact_kind": "automated_drift_monitoring_evidence", "claim_boundary": "alpha_claim"},
        {
            "artifact_kind": "automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "wrong",
        },
        {
            "artifact_kind": "automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "production",
        },
        {
            "artifact_kind": "automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "local_smoke",
            "status": "planned",
        },
        {
            "artifact_kind": "automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "local_smoke",
            "status": "proven",
            "monitoring_status": "production",
        },
        {
            "artifact_kind": "automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "local_smoke",
            "status": "proven",
            "monitoring_status": "local_automated_smoke",
            "drift_status": "unknown",
        },
        {
            "artifact_kind": "automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "local_smoke",
            "status": "proven",
            "monitoring_status": "local_automated_smoke",
            "drift_status": "stable",
            "metric_deltas": {},
        },
        {
            "artifact_kind": "automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "local_smoke",
            "status": "proven",
            "monitoring_status": "local_automated_smoke",
            "drift_status": "stable",
            "metric_deltas": {"x": 0.1},
        },
    ]:
        with pytest.raises(ValueError):
            validate_automated_drift_monitoring_evidence(evidence)

    with pytest.raises(ValueError, match="external_proof_id"):
        build_production_serving_evidence(
            entry,
            endpoint="https://quant.example.com/model",
            health={"status": "ok"},
            sample_request={"x": 1},
            prediction={"claim_boundary": "no_alpha_claim", "ok": True},
            observed_at="2026-06-12T05:00:00Z",
            external_proof_id=" ",
        )
    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_production_serving_evidence(
            alpha_entry,
            endpoint="https://quant.example.com/model",
            health={"status": "ok"},
            sample_request={"x": 1},
            prediction={"claim_boundary": "no_alpha_claim", "ok": True},
            observed_at="2026-06-12T05:00:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
        )
    with pytest.raises(ValueError, match="observed_at"):
        build_production_serving_evidence(
            entry,
            endpoint="https://quant.example.com/model",
            health={"status": "ok"},
            sample_request={"x": 1},
            prediction={"claim_boundary": "no_alpha_claim", "ok": True},
            observed_at=" ",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
        )
    with pytest.raises(ValueError, match="sample_request"):
        build_production_serving_evidence(
            entry,
            endpoint="https://quant.example.com/model",
            health={"status": "ok"},
            sample_request={},
            prediction={"claim_boundary": "no_alpha_claim", "ok": True},
            observed_at="2026-06-12T05:00:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
        )
    with pytest.raises(ValueError, match="healthy"):
        build_production_serving_evidence(
            entry,
            endpoint="https://quant.example.com/model",
            health={"status": "degraded"},
            sample_request={"x": 1},
            prediction={"claim_boundary": "no_alpha_claim", "ok": True},
            observed_at="2026-06-12T05:00:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
        )
    with pytest.raises(ValueError, match="prediction"):
        build_production_serving_evidence(
            entry,
            endpoint="https://quant.example.com/model",
            health={"status": "ok"},
            sample_request={"x": 1},
            prediction={},
            observed_at="2026-06-12T05:00:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
        )
    for evidence in [
        {"artifact_kind": "bad"},
        {"artifact_kind": "production_serving_evidence", "claim_boundary": "alpha_claim"},
        {"artifact_kind": "production_serving_evidence", "claim_boundary": "no_alpha_claim", "readiness_evidence_for": "wrong"},
        {
            "artifact_kind": "production_serving_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "evidence_tier": "local_smoke",
        },
        {
            "artifact_kind": "production_serving_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "evidence_tier": "production",
            "status": "planned",
        },
        {
            "artifact_kind": "production_serving_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "serving_status": "local_smoke",
        },
        {
            "artifact_kind": "production_serving_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "serving_status": "production_serving",
            "endpoint": "http://127.0.0.1:9000/model",
        },
        {
            "artifact_kind": "production_serving_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "serving_status": "production_serving",
            "endpoint": "https://quant.example.com/model",
            "external_proof_id": "https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
            "health": {"status": "degraded"},
        },
        {
            "artifact_kind": "production_serving_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "serving_status": "production_serving",
            "endpoint": "https://quant.example.com/model",
            "external_proof_id": "https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
            "health": {"status": "ok"},
        },
    ]:
        with pytest.raises(ValueError):
            validate_production_serving_evidence(evidence)

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_production_retraining_evidence(
            alpha_entry,
            orchestrator="github-actions://finance_algorithms/retrain",
            result={"status": "completed"},
            observed_at="2026-06-12T05:10:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
        )
    with pytest.raises(ValueError, match="observed_at"):
        build_production_retraining_evidence(
            entry,
            orchestrator="github-actions://finance_algorithms/retrain",
            result={"status": "completed"},
            observed_at=" ",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
        )
    with pytest.raises(ValueError, match="result"):
        build_production_retraining_evidence(
            entry,
            orchestrator="github-actions://finance_algorithms/retrain",
            result={},
            observed_at="2026-06-12T05:10:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
        )
    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_production_retraining_evidence(
            entry,
            orchestrator="github-actions://finance_algorithms/retrain",
            result={
                "status": "completed",
                "run_id": "train-prod-123",
                "artifact_uri": "s3://quant-prod/models/train-prod-123.json",
                "claim_boundary": "alpha_claim",
                "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.0}],
            },
            observed_at="2026-06-12T05:10:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
        )
    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_production_retraining_evidence(
            entry,
            orchestrator="github-actions://finance_algorithms/retrain",
            result={
                "status": "completed",
                "run_id": "train-prod-123",
                "artifact_uri": "s3://quant-prod/models/train-prod-123.json",
                "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.0}],
            },
            observed_at="2026-06-12T05:10:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
        )
    with pytest.raises(ValueError, match="run_id"):
        build_production_retraining_evidence(
            entry,
            orchestrator="github-actions://finance_algorithms/retrain",
            result={
                "status": "completed",
                "artifact_uri": "s3://quant-prod/models/train-prod-123.json",
                "claim_boundary": "no_alpha_claim",
                "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.0}],
            },
            observed_at="2026-06-12T05:10:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
        )
    with pytest.raises(ValueError, match="artifact_uri"):
        build_production_retraining_evidence(
            entry,
            orchestrator="github-actions://finance_algorithms/retrain",
            result={
                "status": "completed",
                "run_id": "train-prod-123",
                "artifact_uri": " ",
                "claim_boundary": "no_alpha_claim",
                "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.0}],
            },
            observed_at="2026-06-12T05:10:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
        )
    with pytest.raises(ValueError, match="out_of_sample net metrics"):
        build_production_retraining_evidence(
            entry,
            orchestrator="github-actions://finance_algorithms/retrain",
            result={
                "status": "completed",
                "run_id": "train-prod-123",
                "artifact_uri": "s3://quant-prod/models/train-prod-123.json",
                "claim_boundary": "no_alpha_claim",
                "metrics": [{"segment": "in_sample", "basis": "net", "sharpe": 99.0}],
            },
            observed_at="2026-06-12T05:10:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
        )
    for evidence in [
        {"artifact_kind": "bad"},
        {"artifact_kind": "production_retraining_evidence", "claim_boundary": "alpha_claim"},
        {"artifact_kind": "production_retraining_evidence", "claim_boundary": "no_alpha_claim", "readiness_evidence_for": "wrong"},
        {
            "artifact_kind": "production_retraining_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
            "evidence_tier": "local_smoke",
        },
        {
            "artifact_kind": "production_retraining_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
            "evidence_tier": "production",
            "status": "planned",
        },
        {
            "artifact_kind": "production_retraining_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "retraining_status": "local_smoke",
        },
        {
            "artifact_kind": "production_retraining_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "retraining_status": "production_retraining",
            "orchestrator": "in_process",
        },
        {
            "artifact_kind": "production_retraining_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "retraining_status": "production_retraining",
            "orchestrator": "github-actions://finance_algorithms/retrain",
            "external_proof_id": "https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
            "oos_net_metrics": {},
        },
        {
            "artifact_kind": "production_retraining_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "retraining_status": "production_retraining",
            "orchestrator": "github-actions://finance_algorithms/retrain",
            "external_proof_id": "https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
            "oos_net_metrics": {"sharpe": 1.0},
        },
    ]:
        with pytest.raises(ValueError):
            validate_production_retraining_evidence(evidence)

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_production_automated_drift_monitoring_evidence(
            alpha_entry,
            monitor="https://quant.example.com/monitors/return-risk",
            result={"status": "stable"},
            observed_at="2026-06-12T05:20:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
        )
    with pytest.raises(ValueError, match="observed_at"):
        build_production_automated_drift_monitoring_evidence(
            entry,
            monitor="https://quant.example.com/monitors/return-risk",
            result={"status": "stable"},
            observed_at=" ",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
        )
    with pytest.raises(ValueError, match="result"):
        build_production_automated_drift_monitoring_evidence(
            entry,
            monitor="https://quant.example.com/monitors/return-risk",
            result={},
            observed_at="2026-06-12T05:20:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
        )
    with pytest.raises(ValueError, match="metric_deltas"):
        build_production_automated_drift_monitoring_evidence(
            entry,
            monitor="https://quant.example.com/monitors/return-risk",
            result={"status": "stable", "claim_boundary": "no_alpha_claim", "metric_deltas": {}},
            observed_at="2026-06-12T05:20:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
        )
    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_production_automated_drift_monitoring_evidence(
            entry,
            monitor="https://quant.example.com/monitors/return-risk",
            result={"status": "stable", "claim_boundary": "alpha_claim", "metric_deltas": {"x": 0.1}},
            observed_at="2026-06-12T05:20:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
        )
    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_production_automated_drift_monitoring_evidence(
            entry,
            monitor="https://quant.example.com/monitors/return-risk",
            result={"status": "stable", "metric_deltas": {"x": 0.1}},
            observed_at="2026-06-12T05:20:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
        )
    for evidence in [
        {"artifact_kind": "bad"},
        {"artifact_kind": "production_automated_drift_monitoring_evidence", "claim_boundary": "alpha_claim"},
        {
            "artifact_kind": "production_automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "wrong",
        },
        {
            "artifact_kind": "production_automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "local_smoke",
        },
        {
            "artifact_kind": "production_automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "production",
            "status": "planned",
        },
        {
            "artifact_kind": "production_automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "monitoring_status": "local_automated_smoke",
        },
        {
            "artifact_kind": "production_automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "monitoring_status": "production_automated_monitoring",
            "drift_status": "unknown",
        },
        {
            "artifact_kind": "production_automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "monitoring_status": "production_automated_monitoring",
            "drift_status": "stable",
            "monitor": "local_smoke",
        },
        {
            "artifact_kind": "production_automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "monitoring_status": "production_automated_monitoring",
            "drift_status": "stable",
            "monitor": "https://quant.example.com/monitors/return-risk",
            "external_proof_id": "https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
            "metric_deltas": {},
        },
        {
            "artifact_kind": "production_automated_drift_monitoring_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "evidence_tier": "production",
            "status": "proven",
            "monitoring_status": "production_automated_monitoring",
            "drift_status": "stable",
            "monitor": "https://quant.example.com/monitors/return-risk",
            "external_proof_id": "https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
            "metric_deltas": {"x": 0.1},
        },
    ]:
        with pytest.raises(ValueError):
            validate_production_automated_drift_monitoring_evidence(evidence)

    store = LocalResultStore(tmp_path / "runs.sqlite")
    alpha_run = store.log({
        "strategy_name": "AlphaStrategy",
        "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.0}],
        "strategy_metadata": {"claim_boundary": "alpha_claim"},
    })
    missing_claim_run = store.log({
        "strategy_name": "MissingClaimStrategy",
        "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.0}],
        "strategy_metadata": {},
    })
    with pytest.raises(ValueError, match="run_ids"):
        register_result_store_runs(registry, store, model_family="family", strategy_name="Strategy", config={}, run_ids=[])
    with pytest.raises(ValueError, match="no_alpha_claim"):
        register_result_store_runs(registry, store, model_family="family", strategy_name="Strategy", config={}, run_ids=[alpha_run])
    with pytest.raises(ValueError, match="no_alpha_claim"):
        register_result_store_runs(registry, store, model_family="family", strategy_name="Strategy", config={}, run_ids=[missing_claim_run])


def test_drift_assessment_report_detects_metric_drift_without_serving_claim(tmp_path):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_drift_assessment_report,
        validate_drift_assessment_report,
    )

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    entry = registry.register("return-risk", "ForecastAllocationStrategy", {"lookback": 12})

    stable = build_drift_assessment_report(
        entry,
        reference_metrics={"oos_net_sharpe": 1.0},
        current_metrics={"oos_net_sharpe": 1.04},
        threshold=0.05,
        observed_at="2026-06-11T00:00:00Z",
    )
    drifted = build_drift_assessment_report(
        entry,
        reference_metrics={"oos_net_sharpe": 1.0},
        current_metrics={"oos_net_sharpe": 0.7},
        threshold=0.05,
        observed_at="2026-06-11T00:00:00Z",
    )

    validate_drift_assessment_report(stable)
    assert stable["monitoring_status"] == "assessed_not_automated"
    assert stable["serving_status"] == "not_serving"
    assert stable["status"] == "stable"
    assert drifted["status"] == "drift_detected"
    assert drifted["claim_boundary"] == "no_alpha_claim"


def test_drift_assessment_rejects_overclaim():
    from quantlab.mlops import validate_drift_assessment_report

    with pytest.raises(ValueError, match="no_alpha_claim"):
        validate_drift_assessment_report({
            "artifact_kind": "drift_assessment_report",
            "claim_boundary": "alpha_claim",
            "monitoring_status": "assessed_not_automated",
            "serving_status": "not_serving",
            "metric_deltas": {},
        })


@given(
    reference=st.floats(min_value=-5, max_value=5, allow_nan=False, allow_infinity=False),
    delta=st.floats(min_value=-1, max_value=1, allow_nan=False, allow_infinity=False),
    threshold=st.floats(min_value=0.001, max_value=1, allow_nan=False, allow_infinity=False),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_drift_status_matches_absolute_threshold(tmp_path, reference, delta, threshold):
    from quantlab.mlops import ExperimentRegistry, build_drift_assessment_report

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register("family", "Strategy", {"x": 1})
    report = build_drift_assessment_report(
        entry,
        reference_metrics={"oos_net_sharpe": reference},
        current_metrics={"oos_net_sharpe": reference + delta},
        threshold=threshold,
        observed_at="2026-06-11T00:00:00Z",
    )

    reported_delta = report["metric_deltas"]["oos_net_sharpe"]
    assert report["status"] == ("drift_detected" if abs(reported_delta) > threshold else "stable")


@given(
    delta=st.floats(min_value=-1, max_value=1, allow_nan=False, allow_infinity=False),
    threshold=st.floats(min_value=0.001, max_value=1, allow_nan=False, allow_infinity=False),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_automated_drift_monitoring_digest_and_status_are_deterministic(tmp_path, delta, threshold):
    from quantlab.mlops import ExperimentRegistry, build_automated_drift_monitoring_evidence

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register("family", "Strategy", {"x": 1})

    def monitor(request):
        return {
            "status": "drift_detected" if abs(delta) > request["threshold"] else "stable",
            "claim_boundary": "no_alpha_claim",
            "metric_deltas": {"oos_net_sharpe": float(delta)},
            "threshold": float(request["threshold"]),
        }

    first = build_automated_drift_monitoring_evidence(
        entry,
        monitor=monitor,
        monitor_request={"threshold": threshold},
        observed_at="2026-06-12T04:00:00Z",
    )
    second = build_automated_drift_monitoring_evidence(
        entry,
        monitor=monitor,
        monitor_request={"threshold": threshold},
        observed_at="2026-06-12T04:00:00Z",
    )

    assert first["request_digest"] == second["request_digest"]
    assert first["result_digest"] == second["result_digest"]
    assert first["drift_status"] == ("drift_detected" if abs(delta) > threshold else "stable")
    assert first["claim_boundary"] == "no_alpha_claim"


@given(count=st.integers(min_value=1, max_value=8))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_tier3_manifest_preserves_experiment_count(tmp_path, count):
    from quantlab.mlops import ExperimentRegistry, build_tier3_run_manifest

    registry_path = tmp_path / f"experiments-{count}.jsonl"
    registry_path.unlink(missing_ok=True)
    registry = ExperimentRegistry(registry_path)
    for idx in range(count):
        registry.register("family", f"Strategy{idx}", {"idx": idx})

    manifest = build_tier3_run_manifest(registry.snapshot_artifact(), artifact_uri="file://artifacts/demo.json")

    assert manifest["entry_count"] == count
    assert len(manifest["experiment_ids"]) == count


@given(momentum=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_serving_smoke_digest_is_deterministic(tmp_path, momentum):
    from quantlab.mlops import ExperimentRegistry, build_serving_smoke_evidence

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register("family", "Strategy", {"x": 1})

    def predict(request):
        return {
            "claim_boundary": "no_alpha_claim",
            "weights": {"A": float(request["features"]["momentum"]), "B": 1.0 - float(request["features"]["momentum"])},
        }

    first = build_serving_smoke_evidence(
        entry,
        health_check=lambda: {"status": "ok"},
        predict=predict,
        sample_request={"features": {"momentum": momentum}},
        observed_at="2026-06-12T02:30:00Z",
    )
    second = build_serving_smoke_evidence(
        entry,
        health_check=lambda: {"status": "ok"},
        predict=predict,
        sample_request={"features": {"momentum": momentum}},
        observed_at="2026-06-12T02:30:00Z",
    )

    assert first["request_digest"] == second["request_digest"]
    assert first["prediction_digest"] == second["prediction_digest"]
    assert first["claim_boundary"] == "no_alpha_claim"


@given(
    lookback=st.integers(min_value=2, max_value=252),
    sharpe=st.floats(min_value=-3, max_value=3, allow_nan=False, allow_infinity=False),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_retraining_smoke_digest_is_deterministic(tmp_path, lookback, sharpe):
    from quantlab.mlops import ExperimentRegistry, build_retraining_smoke_evidence

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register("family", "Strategy", {"x": 1})

    def retrain(request):
        return {
            "status": "completed",
            "run_id": f"train-{request['lookback']}",
            "claim_boundary": "no_alpha_claim",
            "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": float(sharpe)}],
        }

    first = build_retraining_smoke_evidence(
        entry,
        retrain=retrain,
        training_request={"lookback": lookback},
        observed_at="2026-06-12T03:00:00Z",
    )
    second = build_retraining_smoke_evidence(
        entry,
        retrain=retrain,
        training_request={"lookback": lookback},
        observed_at="2026-06-12T03:00:00Z",
    )

    assert first["request_digest"] == second["request_digest"]
    assert first["result_digest"] == second["result_digest"]
    assert first["claim_boundary"] == "no_alpha_claim"
