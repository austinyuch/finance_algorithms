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
    ready = build_tier3_readiness_gate(
        manifest,
        serving_evidence={"status": "proven", "url": "http://127.0.0.1:9000/health"},
        retraining_evidence={"status": "proven", "run_id": "train-1"},
        automated_drift_monitoring_evidence={"status": "proven", "monitor_id": "drift-1"},
    )

    assert partial["readiness"] == "not_ready"
    assert partial["missing_evidence"] == ["automated_drift_monitoring_evidence"]
    assert ready["readiness"] == "tier3_ready"
    assert ready["missing_evidence"] == []
    assert ready["required_evidence"] == [
        "serving_evidence",
        "retraining_evidence",
        "automated_drift_monitoring_evidence",
    ]


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
    assert evidence["readiness_evidence_for"] == "serving_evidence"
    assert gate["readiness"] == "not_ready"
    assert gate["missing_evidence"] == [
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
    assert evidence["readiness_evidence_for"] == "retraining_evidence"
    assert evidence["oos_net_metrics"] == {"sharpe": 1.1, "max_drawdown": -0.07}
    assert gate["readiness"] == "not_ready"
    assert gate["missing_evidence"] == ["automated_drift_monitoring_evidence"]


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
        build_drift_assessment_report,
        build_drift_report_skeleton,
        build_retraining_smoke_evidence,
        build_serving_smoke_evidence,
        build_tier3_run_manifest,
        register_result_store_runs,
        validate_drift_assessment_report,
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
        {"artifact_kind": "serving_smoke_evidence", "claim_boundary": "no_alpha_claim", "readiness_evidence_for": "serving_evidence", "status": "planned"},
        {
            "artifact_kind": "serving_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "status": "proven",
            "serving_status": "production",
        },
        {
            "artifact_kind": "serving_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
            "status": "proven",
            "serving_status": "local_smoke",
            "health": {"status": "degraded"},
        },
        {
            "artifact_kind": "serving_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "serving_evidence",
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
        {"artifact_kind": "retraining_smoke_evidence", "claim_boundary": "no_alpha_claim", "readiness_evidence_for": "retraining_evidence", "status": "planned"},
        {
            "artifact_kind": "retraining_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
            "status": "proven",
            "retraining_status": "production",
        },
        {
            "artifact_kind": "retraining_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
            "status": "proven",
            "retraining_status": "local_smoke",
            "oos_net_metrics": {},
        },
        {
            "artifact_kind": "retraining_smoke_evidence",
            "claim_boundary": "no_alpha_claim",
            "readiness_evidence_for": "retraining_evidence",
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

    store = LocalResultStore(tmp_path / "runs.sqlite")
    alpha_run = store.log({
        "strategy_name": "AlphaStrategy",
        "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.0}],
        "strategy_metadata": {"claim_boundary": "alpha_claim"},
    })
    with pytest.raises(ValueError, match="run_ids"):
        register_result_store_runs(registry, store, model_family="family", strategy_name="Strategy", config={}, run_ids=[])
    with pytest.raises(ValueError, match="no_alpha_claim"):
        register_result_store_runs(registry, store, model_family="family", strategy_name="Strategy", config={}, run_ids=[alpha_run])


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

    assert report["status"] == ("drift_detected" if abs(delta) > threshold else "stable")


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
