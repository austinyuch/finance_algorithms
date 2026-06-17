"""CLI tests — scripts/run_dl_experiment.py (spec: h-deep-learning-research-lab).

Covers REQ-H-EXPERIMENT-001: parameterized experiment → computed artifact + MLOps
lineage (exit 0); insufficient data fails closed (exit 2, nothing registered);
idempotent experiment_id on identical parameters.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

from quantlab.data.provider import InMemoryPITDataProvider

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_dl_experiment.py"


def _load():
    spec = importlib.util.spec_from_file_location("run_dl_experiment", MODULE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _provider(symbols, n_months=96) -> InMemoryPITDataProvider:
    rng = np.random.default_rng(11)
    dates = pd.date_range("2016-01-31", periods=n_months, freq="ME")
    prows = []
    for si, sym in enumerate(symbols):
        c = 100.0 + si * 5.0
        drift = 0.010 if si == 0 else 0.004
        for d in dates:
            c *= float(1 + rng.normal(drift, 0.03))
            prows.append({"symbol": sym, "event_date": d, "available_date": d,
                          "close": round(c, 4)})
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("2014-01-01"),
                              "delist_date": pd.NaT} for s in symbols])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(pd.DataFrame(prows), listings, macro)


def _params(**over):
    p = dict(symbols=["GROWTH", "STEADY"], hidden_units=4, lookback=6, epochs=20,
             seed=0, rebalance="monthly", backend="reference", commission_bps=5)
    p.update(over)
    return p


def test_cli_computed_run_writes_artifact_and_registers(tmp_path):
    mod = _load()
    out = tmp_path / "dl-exp.json"
    viz = tmp_path / "dl-exp.svg"
    registry = tmp_path / "experiments.jsonl"

    result = mod.run_experiment(
        _provider(["GROWTH", "STEADY"]),
        out_path=out, viz_path=viz, registry_path=registry, **_params(),
    )

    assert result["status"] == "computed"
    assert out.exists() and viz.exists() and registry.exists()
    artifact = json.loads(out.read_text())
    assert artifact["claim_boundary"] == "no_alpha_claim"
    assert artifact["performance_report"]["metric_authority"] == "out_of_sample_net_only"
    assert {r["strategy_name"] for r in artifact["leaderboard"]} == {
        "DeepForecastAllocationStrategy", "StaticWeights"}
    # MLOps lineage recorded
    entries = [json.loads(line) for line in registry.read_text().splitlines() if line.strip()]
    assert len(entries) == 1
    assert entries[0]["model_family"] == "NumpyMLPForecaster"
    assert entries[0]["claim_boundary"] == "no_alpha_claim"
    assert entries[0]["experiment_id"] == result["experiment_id"]
    assert entries[0]["run_ids"]
    # self-contained viz
    svg = viz.read_text()
    assert svg.lstrip().startswith("<svg")
    assert "https://" not in svg and "<script" not in svg


def test_cli_insufficient_data_fails_closed(tmp_path):
    mod = _load()
    out = tmp_path / "dl-exp.json"
    registry = tmp_path / "experiments.jsonl"

    # single asset → cannot form a >=2-asset co-temporal comparison
    result = mod.run_experiment(
        _provider(["GROWTH"]), out_path=out, viz_path=tmp_path / "x.svg",
        registry_path=registry, **_params(symbols=["GROWTH"]),
    )

    assert result["status"] == "insufficient_data"
    assert mod.exit_code_for(result) == 2
    # fail-closed: nothing registered
    assert not registry.exists() or registry.read_text().strip() == ""


def test_cli_thin_history_fails_closed(tmp_path):
    mod = _load()
    registry = tmp_path / "experiments.jsonl"

    result = mod.run_experiment(
        _provider(["GROWTH", "STEADY"], n_months=10),
        out_path=tmp_path / "o.json", viz_path=tmp_path / "x.svg",
        registry_path=registry, **_params(),
    )

    assert result["status"] == "insufficient_data"
    assert mod.exit_code_for(result) == 2


def test_cli_idempotent_experiment_id(tmp_path):
    mod = _load()
    registry = tmp_path / "experiments.jsonl"
    kw = dict(viz_path=tmp_path / "v.svg", registry_path=registry, **_params())

    r1 = mod.run_experiment(_provider(["GROWTH", "STEADY"]), out_path=tmp_path / "a.json", **kw)
    r2 = mod.run_experiment(_provider(["GROWTH", "STEADY"]), out_path=tmp_path / "b.json", **kw)

    assert r1["experiment_id"] == r2["experiment_id"]
    entries = [json.loads(line) for line in registry.read_text().splitlines() if line.strip()]
    assert len(entries) == 1  # deterministic id → registry dedups


def test_cli_main_help_smoke(capsys):
    mod = _load()
    code = mod.main(["--help"])
    out = capsys.readouterr().out
    assert code == 0
    assert "hidden-units" in out or "hidden_units" in out
