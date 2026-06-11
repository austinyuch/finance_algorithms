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
