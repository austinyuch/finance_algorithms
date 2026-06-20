from __future__ import annotations

from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pandas as pd
import pytest


class _CapturedStore:
    paths: list[Path] = []
    closed_paths: list[Path] = []

    def __init__(self, db_path: str | Path) -> None:
        self.path = Path(db_path)
        self.paths.append(self.path)

    def __enter__(self) -> "_CapturedStore":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def leaderboard(self) -> list[dict]:
        return [{"strategy_name": "StaticWeights", "oos_net_sharpe": 0.5}]

    def close(self) -> None:
        self.closed_paths.append(self.path)


def _reset_captured_store() -> None:
    _CapturedStore.paths.clear()
    _CapturedStore.closed_paths.clear()


def test_run_vintage_slice_uses_scoped_temp_store_not_fixed_tmp(monkeypatch, capsys):
    import scripts.run_vintage_slice as vintage

    _reset_captured_store()
    provider = SimpleNamespace(
        _macro=pd.DataFrame([{"series": "FEDFUNDS"}]),
        _prices=pd.DataFrame(
            [
                {"symbol": "SP500", "event_date": pd.Timestamp("2024-01-31")},
                {"symbol": "PCOPPUSDM", "event_date": pd.Timestamp("2024-02-29")},
            ]
        ),
        # public read view (REQ-H4-007): the script no longer reaches into _prices
        symbols=lambda: ["PCOPPUSDM", "SP500"],
        event_span=lambda symbols=None: (pd.Timestamp("2024-01-31"), pd.Timestamp("2024-02-29")),
    )
    monkeypatch.setattr(vintage, "build_provider_from_vintage", lambda *args, **kwargs: provider)
    monkeypatch.setattr(vintage, "LocalResultStore", _CapturedStore)
    monkeypatch.setattr(
        vintage,
        "run_and_log",
        lambda *args, **kwargs: (
            None,
            {"metrics": [{"segment": "full", "cumulative_return": 0.1, "annualized_vol": 0.2,
                          "max_drawdown": -0.05, "sharpe": 0.3}]},
        ),
    )

    assert vintage.main() == 0
    assert _CapturedStore.paths
    assert _CapturedStore.paths[0].name == "vintage_slice.db"
    assert _CapturedStore.paths[0] != Path("/tmp") / "vintage_slice.db"
    assert _CapturedStore.closed_paths == _CapturedStore.paths
    assert not _CapturedStore.paths[0].parent.exists()
    assert "[backtest]" in capsys.readouterr().out


def test_run_tsmc_hedge_slice_cleans_temp_store_directory(monkeypatch, capsys):
    import scripts.run_tsmc_hedge_slice as tsmc

    _reset_captured_store()
    monkeypatch.setattr(tsmc, "LocalResultStore", _CapturedStore)
    monkeypatch.setattr(tsmc, "run_hedge_slice", lambda *args, **kwargs: None)
    monkeypatch.setattr(tsmc, "run_and_log", lambda *args, **kwargs: (None, {}))
    monkeypatch.setattr(tsmc, "load_lstm_strategy", lambda: None)

    assert tsmc.main() == 0
    assert _CapturedStore.paths
    assert _CapturedStore.paths[0].name == "slice.db"
    assert _CapturedStore.closed_paths == _CapturedStore.paths
    assert not _CapturedStore.paths[0].parent.exists()
    assert "StaticWeights" in capsys.readouterr().out


def test_run_vintage_slice_closes_temp_store_when_backtest_fails(monkeypatch):
    import scripts.run_vintage_slice as vintage

    _reset_captured_store()
    provider = SimpleNamespace(
        _macro=pd.DataFrame([{"series": "FEDFUNDS"}]),
        _prices=pd.DataFrame(
            [
                {"symbol": "SP500", "event_date": pd.Timestamp("2024-01-31")},
                {"symbol": "PCOPPUSDM", "event_date": pd.Timestamp("2024-02-29")},
            ]
        ),
        # public read view (REQ-H4-007): the script no longer reaches into _prices
        symbols=lambda: ["PCOPPUSDM", "SP500"],
        event_span=lambda symbols=None: (pd.Timestamp("2024-01-31"), pd.Timestamp("2024-02-29")),
    )

    def raise_backtest_error(*args, **kwargs):
        raise RuntimeError("synthetic backtest failure")

    monkeypatch.setattr(vintage, "build_provider_from_vintage", lambda *args, **kwargs: provider)
    monkeypatch.setattr(vintage, "LocalResultStore", _CapturedStore)
    monkeypatch.setattr(vintage, "run_and_log", raise_backtest_error)

    with pytest.raises(RuntimeError, match="synthetic backtest failure"):
        vintage.main()

    assert _CapturedStore.paths
    assert _CapturedStore.closed_paths == _CapturedStore.paths
    assert not _CapturedStore.paths[0].parent.exists()


def test_run_tsmc_hedge_slice_closes_temp_store_when_hedge_run_fails(monkeypatch):
    import scripts.run_tsmc_hedge_slice as tsmc

    _reset_captured_store()

    def raise_hedge_error(*args, **kwargs):
        raise RuntimeError("synthetic hedge failure")

    monkeypatch.setattr(tsmc, "LocalResultStore", _CapturedStore)
    monkeypatch.setattr(tsmc, "run_hedge_slice", raise_hedge_error)
    monkeypatch.setattr(tsmc, "load_lstm_strategy", lambda: None)

    with pytest.raises(RuntimeError, match="synthetic hedge failure"):
        tsmc.main()

    assert _CapturedStore.paths
    assert _CapturedStore.closed_paths == _CapturedStore.paths
    assert not _CapturedStore.paths[0].parent.exists()


def test_build_showcase_payload_uses_scoped_temp_workspace(monkeypatch, tmp_path):
    import scripts.build_showcase_payload as build

    work_dirs: list[Path] = []

    def write_payload(target: Path, work_dir: Path, *, evidence_root: Path | None = None) -> dict:
        work_dir.mkdir(parents=True, exist_ok=True)
        (work_dir / ".quantlab-test-owned").write_text("1", encoding="utf-8")
        work_dirs.append(work_dir)
        target.write_text("{}", encoding="utf-8")
        return {}

    out = tmp_path / "showcase-payload.json"
    monkeypatch.setattr(build, "write_canonical_dashboard_artifact", write_payload)
    monkeypatch.setattr(sys, "argv", ["build_showcase_payload.py", "--out", str(out)])

    assert build.main() == 0
    assert out.exists()
    assert work_dirs
    assert work_dirs[0].name.startswith("quantlab-showcase-")
    assert work_dirs[0] != Path("/tmp") / "quantlab-showcase"
    leaked = work_dirs[0].exists()
    if leaked and (work_dirs[0] / ".quantlab-test-owned").exists():
        shutil.rmtree(work_dirs[0])
    assert not leaked


def test_build_showcase_payload_cleans_temp_workspace_when_write_fails(monkeypatch, tmp_path):
    import scripts.build_showcase_payload as build

    work_dirs: list[Path] = []

    def fail_write(target: Path, work_dir: Path, *, evidence_root: Path | None = None) -> dict:
        work_dir.mkdir(parents=True, exist_ok=True)
        (work_dir / ".quantlab-test-owned").write_text("1", encoding="utf-8")
        work_dirs.append(work_dir)
        raise RuntimeError("synthetic payload failure")

    monkeypatch.setattr(build, "write_canonical_dashboard_artifact", fail_write)
    monkeypatch.setattr(
        sys,
        "argv",
        ["build_showcase_payload.py", "--out", str(tmp_path / "showcase-payload.json")],
    )

    with pytest.raises(RuntimeError, match="synthetic payload failure"):
        build.main()

    assert work_dirs
    leaked = work_dirs[0].exists()
    if leaked and (work_dirs[0] / ".quantlab-test-owned").exists():
        shutil.rmtree(work_dirs[0])
    assert not leaked
