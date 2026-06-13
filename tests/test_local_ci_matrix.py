from __future__ import annotations

import json

from scripts.local_ci_matrix import run_matrix


def test_local_ci_matrix_run_writes_report_and_replaces_timestamps(tmp_path, monkeypatch):
    import scripts.local_ci_matrix as local_ci_matrix

    calls: list[tuple[str, ...]] = []

    class Completed:
        returncode = 0

    def fake_run(command, **kwargs):
        calls.append(tuple(command))
        return Completed()

    monkeypatch.setattr(local_ci_matrix.subprocess, "run", fake_run)

    report = run_matrix(tmp_path)

    assert report["status"] == "passed"
    assert [result["exit_code"] for result in report["results"]] == [0, 0]
    assert len(calls) == 2
    assert calls[0] == (
        "uv",
        "run",
        "python",
        "scripts/daily_snapshot.py",
        "--dry-run",
        "--report-json",
        str(tmp_path / "snapshot-report.json"),
    )
    assert "<utc-started-at>" not in calls[1]
    assert "<utc-finished-at>" not in calls[1]
    assert "--proof-json" in calls[1]
    assert str(tmp_path / "snapshot-schedule-run-proof.json") in calls[1]

    written = json.loads((tmp_path / "local-ci-matrix-report.json").read_text(encoding="utf-8"))
    assert written["status"] == "passed"
    assert written["hosted_only"] == ["schedule event semantics", "artifact upload transport"]
    assert "<utc-started-at>" not in written["results"][1]["command"]
    assert "<utc-finished-at>" not in written["results"][1]["command"]
