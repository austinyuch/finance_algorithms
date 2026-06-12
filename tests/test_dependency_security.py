"""Dependency-surface guards for default UAT/runtime installs."""
from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_default_project_dependencies_exclude_torch() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = pyproject["project"]["dependencies"]

    assert not any(dep.lower().startswith("torch") for dep in deps)


def test_tsmc_hedge_slice_runs_without_lstm_when_torch_lane_absent(monkeypatch, capsys) -> None:
    import scripts.run_tsmc_hedge_slice as runner

    monkeypatch.setattr(runner, "load_lstm_strategy", lambda: None)

    assert runner.main() == 0
    captured = capsys.readouterr()

    assert "LSTMStrategy" not in captured.out
    assert "PyTorch lane not installed" in captured.err
