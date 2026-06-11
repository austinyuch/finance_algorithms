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
