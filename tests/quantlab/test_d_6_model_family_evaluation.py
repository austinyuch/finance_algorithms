"""D-6 model-family evaluation expansion tests."""
from __future__ import annotations

import pytest
from hypothesis import given, strategies as st


def _record(run_id: str, strategy: str, sharpe: float, *, baseline: bool = False):
    return {
        "run_id": run_id,
        "strategy_name": strategy,
        "is_baseline": baseline,
        "metrics": [
            {"segment": "in_sample", "basis": "net", "sharpe": 99.0},
            {"segment": "out_of_sample", "basis": "net", "sharpe": sharpe},
        ],
        "strategy_metadata": {"claim_boundary": "no_alpha_claim"},
    }


def test_model_family_evaluation_ranks_only_oos_net_and_keeps_baseline():
    from quantlab.models import build_model_family_evaluation

    report = build_model_family_evaluation({
        "regime": [_record("regime-run", "RegimeAllocationStrategy", 0.9)],
        "return-risk": [_record("forecast-run", "ForecastAllocationStrategy", 1.2)],
        "robust": [_record("robust-run", "RobustOptimizationStrategy", 0.8)],
        "baseline": [_record("baseline-run", "StaticWeights", 0.7, baseline=True)],
    })

    assert report["claim_boundary"] == "no_alpha_claim"
    assert report["metric_authority"] == "out_of_sample_net_only"
    assert [row["run_id"] for row in report["rows"]] == [
        "forecast-run",
        "regime-run",
        "robust-run",
        "baseline-run",
    ]
    assert report["baseline_run_ids"] == ["baseline-run"]


def test_model_family_evaluation_rejects_alpha_claim_and_missing_baseline():
    from quantlab.models import build_model_family_evaluation

    bad = _record("bad", "BadStrategy", 1.0)
    bad["strategy_metadata"] = {"claim_boundary": "alpha_claim"}

    with pytest.raises(ValueError, match="no_alpha_claim"):
        build_model_family_evaluation({"bad": [bad]})
    with pytest.raises(ValueError, match="baseline"):
        build_model_family_evaluation({"regime": [_record("run", "RegimeAllocationStrategy", 1.0)]})


def test_model_family_evaluation_rejects_missing_oos_net_metric():
    from quantlab.models import build_model_family_evaluation

    record = _record("bad", "BadStrategy", 1.0, baseline=True)
    record["metrics"] = [{"segment": "in_sample", "basis": "net", "sharpe": 99.0}]

    with pytest.raises(ValueError, match="out_of_sample net"):
        build_model_family_evaluation({"bad": [record]})


@given(scores=st.lists(st.floats(min_value=-3, max_value=3, allow_nan=False, allow_infinity=False),
                       min_size=2, max_size=20))
def test_pbt_model_family_evaluation_sorted_descending(scores):
    from quantlab.models import build_model_family_evaluation

    records = [_record(f"run-{i}", f"Strategy{i}", score, baseline=(i == 0))
               for i, score in enumerate(scores)]

    report = build_model_family_evaluation({"family": records})

    ordered = [row["oos_net_sharpe"] for row in report["rows"]]
    assert ordered == sorted(scores, reverse=True)


def test_result_store_family_evaluation_uses_real_run_records(tmp_path):
    from quantlab.models import build_result_store_family_evaluation
    from quantlab.tracking import LocalResultStore

    store = LocalResultStore(tmp_path / "runs.sqlite")
    baseline = store.log(_record("baseline", "StaticWeights", 0.2, baseline=True))
    regime = store.log(_record("regime", "RegimeAllocationStrategy", 0.4))
    forecast = store.log(_record("forecast", "ForecastAllocationStrategy", 0.8))
    robust = store.log(_record("robust", "RobustOptimizationStrategy", 0.6))

    report = build_result_store_family_evaluation(store, {
        "baseline": [baseline],
        "regime": [regime],
        "return-risk": [forecast],
        "robust": [robust],
    })

    assert report["source"] == "local_result_store"
    assert [row["run_id"] for row in report["rows"]] == [forecast, robust, regime, baseline]
    assert report["baseline_run_ids"] == [baseline]


def test_model_family_evaluation_artifact_is_checksumed_and_written(tmp_path):
    from quantlab.models import (
        build_model_family_evaluation,
        build_model_family_evaluation_artifact,
        validate_model_family_evaluation_artifact,
        write_model_family_evaluation_artifact,
    )

    report = build_model_family_evaluation({
        "baseline": [_record("baseline", "StaticWeights", 0.2, baseline=True)],
        "forecast": [_record("forecast", "ForecastAllocationStrategy", 0.8)],
    })
    artifact = build_model_family_evaluation_artifact(
        report,
        artifact_uri="file://artifacts/d-eval.json",
        generated_at="2026-06-11T00:00:00Z",
    )
    target = write_model_family_evaluation_artifact(artifact, tmp_path / "d-eval.json")

    validate_model_family_evaluation_artifact(artifact)
    assert artifact["artifact_kind"] == "model_family_evaluation_artifact"
    assert artifact["row_count"] == 2
    assert artifact["checksum"]
    assert target.read_text(encoding="utf-8").endswith("\n")


@given(scores=st.lists(st.floats(min_value=-2, max_value=2, allow_nan=False, allow_infinity=False),
                       min_size=2, max_size=12))
def test_pbt_model_family_artifact_row_count_matches_report(scores):
    from quantlab.models import build_model_family_evaluation, build_model_family_evaluation_artifact

    report = build_model_family_evaluation({
        "family": [_record(f"run-{idx}", f"Strategy{idx}", score, baseline=(idx == 0))
                   for idx, score in enumerate(scores)]
    })
    artifact = build_model_family_evaluation_artifact(
        report,
        artifact_uri="file://artifacts/d-eval.json",
        generated_at="2026-06-11T00:00:00Z",
    )

    assert artifact["row_count"] == len(report["rows"])
