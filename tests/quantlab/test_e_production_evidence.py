"""E production evidence boundary tests."""
from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st


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


def test_tier3_gate_rejects_production_evidence_for_different_experiment(tmp_path):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_production_automated_drift_monitoring_evidence,
        build_production_retraining_evidence,
        build_production_serving_evidence,
        build_tier3_readiness_gate,
        build_tier3_run_manifest,
    )

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    manifest_entry = registry.register("return-risk", "ForecastAllocationStrategy", {"lookback": 12})
    manifest = build_tier3_run_manifest(
        registry.snapshot_artifact(),
        artifact_uri="s3://quant-prod/manifests/return-risk-demo.json",
    )
    other_entry = registry.register("robust-portfolio", "RobustOptimizationStrategy", {"vol_cap": 0.2})

    serving = build_production_serving_evidence(
        manifest_entry,
        endpoint="https://quant.example.com/models/return-risk",
        health={"status": "ok", "model_loaded": True},
        sample_request={"features": {"momentum": 0.6}},
        prediction={"claim_boundary": "no_alpha_claim", "weights": {"A": 0.6, "B": 0.4}},
        observed_at="2026-06-12T05:00:00Z",
        external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
    )
    retraining = build_production_retraining_evidence(
        other_entry,
        orchestrator="github-actions://finance_algorithms/retrain",
        result={
            "status": "completed",
            "run_id": "train-prod-123",
            "artifact_uri": "s3://quant-prod/models/robust-portfolio/train-prod-123.json",
            "claim_boundary": "no_alpha_claim",
            "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.2}],
        },
        observed_at="2026-06-12T05:10:00Z",
        external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
    )
    drift = build_production_automated_drift_monitoring_evidence(
        manifest_entry,
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
        serving_evidence=serving,
        retraining_evidence=retraining,
        automated_drift_monitoring_evidence=drift,
    )

    assert other_entry.experiment_id not in manifest["experiment_ids"]
    assert gate["readiness"] == "not_ready"
    assert gate["missing_evidence"] == ["experiment_binding"]


@given(artifact_uri=st.sampled_from([
    "file://artifacts/demo.json",
    "memory://artifacts/demo.json",
    "artifact-prod-123",
    "http://localhost/artifacts/demo.json",
    "http://quant.example.com/artifacts/demo.json",
    "ftp://quant.example.com/artifacts/demo.json",
    "ssh://quant.example.com/artifacts/demo.json",
    "github-actions://finance_algorithms/artifacts/demo.json",
]))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_production_evidence_triplet_requires_external_manifest_artifact(tmp_path, artifact_uri):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_production_automated_drift_monitoring_evidence,
        build_production_retraining_evidence,
        build_production_serving_evidence,
        build_tier3_readiness_gate,
        build_tier3_run_manifest,
    )

    registry = ExperimentRegistry(tmp_path / "experiments.jsonl")
    entry = registry.register("return-risk", "ForecastAllocationStrategy", {"lookback": 12})
    local_manifest = build_tier3_run_manifest(
        registry.snapshot_artifact(),
        artifact_uri=artifact_uri,
    )
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

    gate = build_tier3_readiness_gate(
        local_manifest,
        serving_evidence=serving,
        retraining_evidence=retraining,
        automated_drift_monitoring_evidence=drift,
    )

    assert gate["readiness"] == "not_ready"
    assert gate["missing_evidence"] == ["production_manifest_artifact"]


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


@given(
    proof_id=st.sampled_from([
        "file:///tmp/serving-proof.json",
        "s3://quant-prod/proofs/serving.json",
        "github-actions://finance_algorithms/actions/runs/123",
        "http://ci.example.com/actions/runs/123",
        "https:ci.example.com/actions/runs/123",
    ])
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_production_external_proof_id_requires_https_url(tmp_path, proof_id):
    from quantlab.mlops import ExperimentRegistry, build_production_serving_evidence

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
            external_proof_id=proof_id,
        )


@given(observed_at=st.sampled_from([
    "",
    "today",
    "2026-06-12",
    "2026-06-12T05:00:00",
    "2026-06-12T05:00:00+08:00",
    "Fri, 12 Jun 2026 05:00:00 GMT",
]))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_production_evidence_requires_utc_observed_at(tmp_path, observed_at):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_production_automated_drift_monitoring_evidence,
        build_production_retraining_evidence,
        build_production_serving_evidence,
    )

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register(
        "return-risk",
        "ForecastAllocationStrategy",
        {"lookback": 12},
    )

    with pytest.raises(ValueError, match="observed_at"):
        build_production_serving_evidence(
            entry,
            endpoint="https://quant.example.com/models/return-risk",
            health={"status": "ok"},
            sample_request={"features": {"momentum": 0.6}},
            prediction={"claim_boundary": "no_alpha_claim", "weights": {"A": 0.6}},
            observed_at=observed_at,
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#serving",
        )

    with pytest.raises(ValueError, match="observed_at"):
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
            observed_at=observed_at,
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
        )

    with pytest.raises(ValueError, match="observed_at"):
        build_production_automated_drift_monitoring_evidence(
            entry,
            monitor="https://quant.example.com/monitors/return-risk",
            result={
                "status": "stable",
                "claim_boundary": "no_alpha_claim",
                "metric_deltas": {"oos_net_sharpe": 0.02},
                "threshold": 0.05,
            },
            observed_at=observed_at,
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
        )


@given(identity=st.sampled_from([
    "prod-runner",
    "ci-prod-123",
    "monitor-prod",
    "external-job",
    "http://ci.example.com/retrain",
    "ftp://ci.example.com/retrain",
    "ssh://ci.example.com/retrain",
]))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_production_external_identities_require_uri_authority(tmp_path, identity):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_production_automated_drift_monitoring_evidence,
        build_production_retraining_evidence,
    )

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register(
        "return-risk",
        "ForecastAllocationStrategy",
        {"lookback": 12},
    )

    with pytest.raises(ValueError, match="external orchestrator"):
        build_production_retraining_evidence(
            entry,
            orchestrator=identity,
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

    with pytest.raises(ValueError, match="external monitor"):
        build_production_automated_drift_monitoring_evidence(
            entry,
            monitor=identity,
            result={
                "status": "stable",
                "claim_boundary": "no_alpha_claim",
                "metric_deltas": {"oos_net_sharpe": 0.02},
                "threshold": 0.05,
            },
            observed_at="2026-06-12T05:20:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
        )


@given(artifact_uri=st.sampled_from([
    "file://artifacts/train-prod-123.json",
    "memory://models/train-prod-123.json",
    "train-prod-123",
    "http://localhost/models/train-prod-123.json",
    "http://quant.example.com/models/train-prod-123.json",
    "ftp://quant.example.com/models/train-prod-123.json",
    "ssh://quant.example.com/models/train-prod-123.json",
    "github-actions://finance_algorithms/models/train-prod-123.json",
]))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_production_retraining_artifact_uri_requires_external_authority(tmp_path, artifact_uri):
    from quantlab.mlops import ExperimentRegistry, build_production_retraining_evidence

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register(
        "return-risk",
        "ForecastAllocationStrategy",
        {"lookback": 12},
    )

    with pytest.raises(ValueError, match="artifact_uri"):
        build_production_retraining_evidence(
            entry,
            orchestrator="github-actions://finance_algorithms/retrain",
            result={
                "status": "completed",
                "run_id": "train-prod-123",
                "artifact_uri": artifact_uri,
                "claim_boundary": "no_alpha_claim",
                "metrics": [{"segment": "out_of_sample", "basis": "net", "sharpe": 1.2}],
            },
            observed_at="2026-06-12T05:10:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#retraining",
        )


@given(threshold=st.one_of(
    st.none(),
    st.floats(max_value=0, allow_nan=False, allow_infinity=False),
))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_production_drift_monitoring_requires_positive_threshold(tmp_path, threshold):
    from quantlab.mlops import (
        ExperimentRegistry,
        build_production_automated_drift_monitoring_evidence,
        validate_production_automated_drift_monitoring_evidence,
    )

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register(
        "return-risk",
        "ForecastAllocationStrategy",
        {"lookback": 12},
    )
    result = {
        "status": "stable",
        "claim_boundary": "no_alpha_claim",
        "metric_deltas": {"oos_net_sharpe": 0.02},
    }
    if threshold is not None:
        result["threshold"] = threshold

    with pytest.raises(ValueError, match="threshold"):
        build_production_automated_drift_monitoring_evidence(
            entry,
            monitor="https://quant.example.com/monitors/return-risk",
            result=result,
            observed_at="2026-06-12T05:20:00Z",
            external_proof_id="https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
        )

    evidence = {
        "artifact_kind": "production_automated_drift_monitoring_evidence",
        "claim_boundary": "no_alpha_claim",
        "readiness_evidence_for": "automated_drift_monitoring_evidence",
        "evidence_tier": "production",
        "status": "proven",
        "monitoring_status": "production_automated_monitoring",
        "drift_status": "stable",
        "monitor": "https://quant.example.com/monitors/return-risk",
        "external_proof_id": "https://github.com/austinyuch/finance_algorithms/actions/runs/123#drift",
        "metric_deltas": {"oos_net_sharpe": 0.02},
        "experiment_id": entry.experiment_id,
        "observed_at": "2026-06-12T05:20:00Z",
        "result_digest": "digest",
    }
    if threshold is not None:
        evidence["threshold"] = threshold

    with pytest.raises(ValueError, match="threshold"):
        validate_production_automated_drift_monitoring_evidence(evidence)


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


def test_production_evidence_validators_reject_handwritten_short_digests(tmp_path):
    from quantlab.mlops import (
        ExperimentRegistry,
        validate_production_automated_drift_monitoring_evidence,
        validate_production_retraining_evidence,
        validate_production_serving_evidence,
    )

    entry = ExperimentRegistry(tmp_path / "experiments.jsonl").register(
        "return-risk",
        "ForecastAllocationStrategy",
        {"lookback": 12},
    )
    common = {
        "claim_boundary": "no_alpha_claim",
        "evidence_tier": "production",
        "status": "proven",
        "experiment_id": entry.experiment_id,
        "observed_at": "2026-06-12T05:00:00Z",
        "external_proof_id": "https://github.com/austinyuch/finance_algorithms/actions/runs/123#proof",
    }

    with pytest.raises(ValueError, match="request_digest"):
        validate_production_serving_evidence({
            **common,
            "artifact_kind": "production_serving_evidence",
            "readiness_evidence_for": "serving_evidence",
            "serving_status": "production_serving",
            "endpoint": "https://quant.example.com/models/return-risk",
            "health": {"status": "ok"},
            "request_digest": "abc",
            "prediction_digest": "d" * 64,
        })
    with pytest.raises(ValueError, match="result_digest"):
        validate_production_retraining_evidence({
            **common,
            "artifact_kind": "production_retraining_evidence",
            "readiness_evidence_for": "retraining_evidence",
            "retraining_status": "production_retraining",
            "orchestrator": "github-actions://finance_algorithms/retrain",
            "run_id": "train-prod-123",
            "artifact_uri": "s3://quant-prod/models/return-risk/train-prod-123.json",
            "oos_net_metrics": {"sharpe": 1.2},
            "result_digest": "digest",
        })
    with pytest.raises(ValueError, match="result_digest"):
        validate_production_automated_drift_monitoring_evidence({
            **common,
            "artifact_kind": "production_automated_drift_monitoring_evidence",
            "readiness_evidence_for": "automated_drift_monitoring_evidence",
            "monitoring_status": "production_automated_monitoring",
            "drift_status": "stable",
            "monitor": "https://quant.example.com/monitors/return-risk",
            "metric_deltas": {"oos_net_sharpe": 0.02},
            "threshold": 0.05,
            "result_digest": "abc",
        })


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

