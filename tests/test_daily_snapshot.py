"""Unit tests for scripts/daily_snapshot.py.

原則:**完全不打網路**。所有 HTTP 以 monkeypatch 假造,確保測試 deterministic、
快速、可重現(與本專案 point-in-time / reproducibility 方法論一致)。

保護的核心邏輯:
  - bitemporal stamping(available_date / is_approximate=False)
  - append-only / immutable 寫檔(已存在則跳過,絕不覆寫)
  - dry-run 不寫檔
  - FRED / Stooq CSV 的 event_date 解析
  - graceful degradation(逐源失敗不中斷)
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "daily_snapshot.py"


def _load():
    spec = importlib.util.spec_from_file_location("daily_snapshot", MODULE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ds = _load()


class FakeResp:
    def __init__(self, text: str, status: int = 200):
        self.text = text
        self._status = status

    def raise_for_status(self) -> None:
        if self._status >= 400:
            raise ds.requests.HTTPError(f"{self._status} error")


# --- _record:bitemporal 欄位 -------------------------------------------------

def test_record_has_bitemporal_fields():
    rec = ds._record("fred:CPIAUCSL", "2026-06-09", "raw-text", event_date="2026-05-01")
    assert rec["source"] == "fred:CPIAUCSL"
    assert rec["available_date"] == "2026-06-09"   # 自建 snapshot = 真實可得日
    assert rec["is_approximate"] is False          # 非估算
    assert rec["raw"] == "raw-text"
    assert rec["event_date"] == "2026-05-01"
    assert "captured_at" in rec


# --- _write:append-only / immutable -----------------------------------------

def test_write_creates_file(tmp_path: Path):
    status = ds._write(tmp_path, "src_a", {"k": "v"}, dry=False)
    assert status.startswith("OK")
    assert json.loads((tmp_path / "src_a.json").read_text(encoding="utf-8")) == {"k": "v"}


def test_write_is_append_only_and_immutable(tmp_path: Path):
    ds._write(tmp_path, "src_a", {"first": 1}, dry=False)
    status = ds._write(tmp_path, "src_a", {"second": 2}, dry=False)   # 第二次同源同日
    assert status.startswith("SKIP")
    # 內容必須保持第一次寫入,絕不被覆寫
    assert json.loads((tmp_path / "src_a.json").read_text(encoding="utf-8")) == {"first": 1}


def test_write_dry_run_does_not_write(tmp_path: Path):
    status = ds._write(tmp_path, "src_a", {"k": "v"}, dry=True)
    assert status.startswith("DRY")
    assert not (tmp_path / "src_a.json").exists()


# --- fetch_*:CSV 解析(mock 網路) ------------------------------------------

def test_fetch_fred_parses_event_date(monkeypatch):
    csv = "observation_date,CPIAUCSL\n2026-04-01,310.0\n2026-05-01,311.2\n"
    monkeypatch.setattr(ds.requests, "get", lambda *a, **k: FakeResp(csv))
    rec = ds.fetch_fred("CPIAUCSL", "2026-06-09")
    assert rec["source"] == "fred:CPIAUCSL"
    assert rec["available_date"] == "2026-06-09"
    assert rec["event_date"] == "2026-05-01"    # CSV 最後一列 observation date
    assert rec["is_approximate"] is False


def test_fetch_stooq_parses_event_date(monkeypatch):
    csv = "Symbol,Date,Time,Open,High,Low,Close,Volume\nSPY.US,2026-06-09,22:00:00,1,2,0.5,1.5,1000\n"
    monkeypatch.setattr(ds.requests, "get", lambda *a, **k: FakeResp(csv))
    rec = ds.fetch_stooq("spy.us", "2026-06-09")
    assert rec["source"] == "stooq:spy.us"
    assert rec["event_date"] == "2026-06-09"     # 第二列的 Date 欄
    assert rec["is_approximate"] is False


def test_fetch_yahoo_chart_parses_event_date(monkeypatch):
    payload = json.dumps({
        "chart": {"result": [{
            "timestamp": [1780963200, 1781049600],
            "indicators": {"quote": [{"close": [1000.0, 1010.5]}]},
        }], "error": None}
    })
    monkeypatch.setattr(ds.requests, "get", lambda *a, **k: FakeResp(payload))
    rec = ds.fetch_yahoo_chart("2330.TW", "2026-06-11")
    assert rec["source"] == "yahoo:2330.TW"
    assert rec["event_date"] == "2026-06-10"
    assert rec["is_approximate"] is False


@given(
    ts=st.lists(st.integers(min_value=1_600_000_000, max_value=1_900_000_000), min_size=1, max_size=8),
    close=st.lists(st.one_of(st.none(), st.floats(min_value=1.0, max_value=10_000.0,
                                                  allow_nan=False, allow_infinity=False)),
                   min_size=1, max_size=8),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_yahoo_latest_event_date_matches_last_valid_close(monkeypatch, ts, close):
    n = min(len(ts), len(close))
    ts = ts[:n]
    close = close[:n]
    if not any(v is not None for v in close):
        close[-1] = 123.0
    payload = json.dumps({
        "chart": {"result": [{
            "timestamp": ts,
            "indicators": {"quote": [{"close": close}]},
        }], "error": None}
    })
    monkeypatch.setattr(ds.requests, "get", lambda *a, **k: FakeResp(payload))

    rec = ds.fetch_yahoo_chart("SPY", "2026-06-11")
    valid = [(t, c) for t, c in zip(ts, close) if c is not None]
    expected = ds.dt.datetime.fromtimestamp(valid[-1][0], ds.dt.timezone.utc).strftime("%Y-%m-%d")
    assert rec["event_date"] == expected


def test_fetch_noaa_wraps_text(monkeypatch):
    monkeypatch.setattr(ds.requests, "get", lambda *a, **k: FakeResp("SEAS YR ...oni..."))
    rec = ds.fetch_noaa_oni("2026-06-09")
    assert rec["source"] == "noaa:oni"
    assert "oni" in rec["raw"]


def test_fetch_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(ds.requests, "get", lambda *a, **k: FakeResp("not found", status=404))
    with pytest.raises(ds.requests.HTTPError):
        ds.fetch_fred("BAD", "2026-06-09")


# --- main:graceful degradation(一源失敗不中斷,且仍寫出成功源) ----------

def test_main_degrades_gracefully(monkeypatch, tmp_path, capsys):
    # 把輸出根目錄導到 tmp,避免污染 repo
    monkeypatch.setattr(ds, "OUT_ROOT", tmp_path)
    # 縮減到 2 個 FRED 源,其中一個會炸
    monkeypatch.setattr(ds, "FRED_SERIES", ["GOOD", "BAD"])
    monkeypatch.setattr(ds, "STOOQ_SYMBOLS", [])
    monkeypatch.setattr(ds, "YAHOO_SYMBOLS", [])
    monkeypatch.setattr(ds, "NOAA_ONI_URL", "http://example/none")

    def fake_get(url, *a, **k):
        if "GOOD" in url:
            return FakeResp("observation_date,GOOD\n2026-05-01,1.0\n")
        if "BAD" in url:
            return FakeResp("err", status=500)
        return FakeResp("SEAS YR oni")   # noaa

    monkeypatch.setattr(ds.requests, "get", fake_get)

    monkeypatch.setattr(ds.sys, "argv", ["daily_snapshot.py"])
    rc = ds.main()
    # GOOD + noaa 成功,BAD 失敗 → 回傳碼非 0,但成功源仍寫出
    out_dir = tmp_path / ds._today()
    written = {p.name for p in out_dir.glob("*.json")}
    assert any("GOOD" in n for n in written)        # 成功源已寫出
    assert not any("BAD" in n for n in written)     # 失敗源未寫出
    assert rc == 1                                  # 有失敗 → 非 0


def test_main_writes_machine_readable_report_for_dry_run(monkeypatch, tmp_path):
    monkeypatch.setattr(ds, "OUT_ROOT", tmp_path / "vintage")
    monkeypatch.setattr(ds, "FRED_SERIES", ["FEDFUNDS"])
    monkeypatch.setattr(ds, "STOOQ_SYMBOLS", [])
    monkeypatch.setattr(ds, "YAHOO_SYMBOLS", ["2330.TW"])
    report_path = tmp_path / "snapshot-report.json"

    monkeypatch.setattr(ds.sys, "argv", [
        "daily_snapshot.py",
        "--dry-run",
        "--report-json",
        str(report_path),
    ])

    rc = ds.main()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert rc == 0
    assert report["available_date"] == ds._today()
    assert report["dry_run"] is True
    assert report["counts"] == {"ok": 0, "skip": 0, "fail": 0, "dry": 3}
    assert report["source_health"]["claim_boundary"] == "source_contract_status_only"
    assert report["source_health"]["stooq"]["status"] == "blocked"
    assert report["source_health"]["stooq"]["default_enabled"] is False
    assert report["source_health"]["yahoo"]["status"] == "available"


def test_main_scoped_live_write_uses_out_root_and_scoped_source_health(monkeypatch, tmp_path):
    out_root = tmp_path / "vintage"
    report_path = tmp_path / "snapshot-report.json"

    def fake_get(url, *a, **k):
        assert "FEDFUNDS" in url
        return FakeResp("observation_date,FEDFUNDS\n2026-05-01,4.33\n")

    monkeypatch.setattr(ds.requests, "get", fake_get)
    monkeypatch.setattr(ds.sys, "argv", [
        "daily_snapshot.py",
        "--out-root",
        str(out_root),
        "--fred-series",
        "FEDFUNDS",
        "--yahoo-symbols",
        "",
        "--no-noaa",
        "--report-json",
        str(report_path),
    ])

    rc = ds.main()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    out_dir = out_root / ds._today()
    written = out_dir / "fred_FEDFUNDS.json"

    assert rc == 0
    assert written.exists()
    assert report["dry_run"] is False
    assert report["out_dir"] == str(out_dir)
    assert report["counts"] == {"ok": 1, "skip": 0, "fail": 0, "dry": 0}
    assert report["jobs"] == [{"source_id": "fred:FEDFUNDS", "safe_id": "fred_FEDFUNDS", "status": "ok"}]
    assert report["source_health"]["fred"]["symbols"] == ["FEDFUNDS"]
    assert "yahoo" not in report["source_health"]
    assert "noaa" not in report["source_health"]
    assert report["source_health"]["stooq"]["status"] == "blocked"


def test_main_scoped_live_write_is_append_only_on_second_run(monkeypatch, tmp_path):
    out_root = tmp_path / "vintage"

    def fake_get(url, *a, **k):
        return FakeResp("observation_date,FEDFUNDS\n2026-05-01,4.33\n")

    monkeypatch.setattr(ds.requests, "get", fake_get)
    argv = [
        "daily_snapshot.py",
        "--out-root",
        str(out_root),
        "--fred-series",
        "FEDFUNDS",
        "--yahoo-symbols",
        "",
        "--no-noaa",
    ]

    monkeypatch.setattr(ds.sys, "argv", argv)
    assert ds.main() == 0
    first = (out_root / ds._today() / "fred_FEDFUNDS.json").read_text(encoding="utf-8")

    monkeypatch.setattr(ds.sys, "argv", argv)
    assert ds.main() == 0
    second = (out_root / ds._today() / "fred_FEDFUNDS.json").read_text(encoding="utf-8")

    assert second == first


def test_main_report_records_failed_sources_without_corrupting_successes(monkeypatch, tmp_path):
    monkeypatch.setattr(ds, "OUT_ROOT", tmp_path / "vintage")
    monkeypatch.setattr(ds, "FRED_SERIES", ["GOOD", "BAD"])
    monkeypatch.setattr(ds, "STOOQ_SYMBOLS", [])
    monkeypatch.setattr(ds, "YAHOO_SYMBOLS", [])
    report_path = tmp_path / "snapshot-report.json"

    def fake_get(url, *a, **k):
        if "GOOD" in url:
            return FakeResp("observation_date,GOOD\n2026-05-01,1.0\n")
        if "BAD" in url:
            return FakeResp("err", status=500)
        return FakeResp("SEAS YR oni")

    monkeypatch.setattr(ds.requests, "get", fake_get)
    monkeypatch.setattr(ds.sys, "argv", [
        "daily_snapshot.py",
        "--report-json",
        str(report_path),
    ])

    rc = ds.main()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert rc == 1
    assert report["counts"]["ok"] == 2
    assert report["counts"]["fail"] == 1
    failed = [item for item in report["jobs"] if item["status"] == "fail"]
    assert failed == [{
        "source_id": "fred:BAD",
        "safe_id": "fred_BAD",
        "status": "fail",
        "error_type": "HTTPError",
        "error": "500 error",
    }]


def test_snapshot_includes_yahoo_tsmc_and_twse_sources():
    assert {"2330.TW", "^TWII"} <= set(ds.YAHOO_SYMBOLS)


def test_stooq_defaults_disabled_after_source_contract_block():
    assert ds.STOOQ_SYMBOLS == []


def test_csv_env_symbols_trims_and_skips_empty_values(monkeypatch):
    monkeypatch.setenv("QUANTLAB_STOOQ_SYMBOLS", " spy.us, ,2330.tw, ^twse ")

    assert ds._csv_env_symbols("QUANTLAB_STOOQ_SYMBOLS", []) == ["spy.us", "2330.tw", "^twse"]


def test_snapshot_ops_gate_accepts_partial_live_report_when_allowed():
    from scripts.snapshot_ops_gate import validate_snapshot_report

    report = {
        "available_date": "2026-06-11",
        "dry_run": False,
        "counts": {"ok": 2, "skip": 1, "fail": 1, "dry": 0},
        "jobs": [
            {"source_id": "fred:GOOD", "status": "ok"},
            {"source_id": "fred:OLD", "status": "skip"},
            {"source_id": "fred:BAD", "status": "fail"},
            {"source_id": "yahoo:2330.TW", "status": "ok"},
        ],
        "source_health": {
            "claim_boundary": "source_contract_status_only",
            "stooq": {"status": "blocked", "default_enabled": False},
        },
    }

    summary = validate_snapshot_report(report, allow_failures=True)

    assert summary["status"] == "partial"
    assert summary["claim_boundary"] == "source_contract_status_only"


def test_source_quorum_gate_requires_broad_default_live_coverage():
    from scripts.snapshot_ops_gate import validate_source_quorum_report

    report = _broad_source_quorum_report()

    summary = validate_source_quorum_report(report)

    assert summary["status"] == "broad_source_quorum"
    assert summary["evidence_tier"] == "live_source_quorum"
    assert summary["claim_boundary"] == "source_contract_status_only"
    assert summary["groups"] == {
        "fred_macro": ["fred:FEDFUNDS"],
        "fred_price_proxy": ["fred:SP500", "fred:PCOPPUSDM"],
        "yahoo_equity": ["yahoo:2330.TW"],
        "yahoo_market": ["yahoo:^TWII"],
        "noaa_macro": ["noaa:oni"],
    }


def _broad_source_quorum_report() -> dict[str, object]:
    return {
        "available_date": "2026-06-12",
        "dry_run": False,
        "counts": {"ok": 6, "skip": 0, "fail": 0, "dry": 0},
        "jobs": [
            {"source_id": "fred:FEDFUNDS", "status": "ok"},
            {"source_id": "fred:SP500", "status": "ok"},
            {"source_id": "fred:PCOPPUSDM", "status": "ok"},
            {"source_id": "yahoo:2330.TW", "status": "ok"},
            {"source_id": "yahoo:^TWII", "status": "ok"},
            {"source_id": "noaa:oni", "status": "ok"},
        ],
        "source_health": {
            "claim_boundary": "source_contract_status_only",
            "stooq": {"status": "blocked", "default_enabled": False},
        },
    }


def _broad_source_quorum_report_with_files(tmp_path: Path) -> dict[str, object]:
    report = _broad_source_quorum_report()
    out_dir = tmp_path / "vintage" / "2026-06-12"
    out_dir.mkdir(parents=True)
    jobs = report["jobs"]
    assert isinstance(jobs, list)
    for job in jobs:
        safe_id = str(job["source_id"]).replace(":", "_").replace("^", "idx_")
        job["safe_id"] = safe_id
        (out_dir / f"{safe_id}.json").write_text(json.dumps({"source": job["source_id"]}), encoding="utf-8")
    report["out_dir"] = str(out_dir)
    return report


def test_source_quorum_gate_cli_smoke(tmp_path, capsys):
    from scripts.snapshot_ops_gate import main

    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_broad_source_quorum_report()), encoding="utf-8")

    rc = main([str(report_path), "--require-source-quorum"])
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["status"] == "broad_source_quorum"
    assert out["evidence_tier"] == "live_source_quorum"


@given(group=st.sampled_from(["fred_macro", "fred_price_proxy", "yahoo_equity", "yahoo_market", "noaa_macro"]))
def test_pbt_source_quorum_gate_fails_when_any_group_is_missing(group):
    from scripts.snapshot_ops_gate import DEFAULT_SOURCE_QUORUM, validate_source_quorum_report

    report = _broad_source_quorum_report()
    required = set(DEFAULT_SOURCE_QUORUM[group])
    jobs = report["jobs"]
    assert isinstance(jobs, list)
    report["jobs"] = [job for job in jobs if job["source_id"] not in required]
    report["counts"] = {"ok": len(report["jobs"]), "skip": 0, "fail": 0, "dry": 0}

    with pytest.raises(ValueError, match=f"missing broad source quorum for {group}"):
        validate_source_quorum_report(report)


def test_source_quorum_gate_rejects_scoped_smoke_as_broad_readiness():
    from scripts.snapshot_ops_gate import validate_source_quorum_report

    report = {
        "available_date": "2026-06-12",
        "dry_run": False,
        "counts": {"ok": 1, "skip": 0, "fail": 0, "dry": 0},
        "jobs": [{"source_id": "fred:FEDFUNDS", "status": "ok"}],
        "source_health": {
            "claim_boundary": "source_contract_status_only",
            "stooq": {"status": "blocked", "default_enabled": False},
        },
    }

    with pytest.raises(ValueError, match="missing broad source quorum"):
        validate_source_quorum_report(report)


def test_source_quorum_gate_rejects_dry_or_failed_critical_sources():
    from scripts.snapshot_ops_gate import validate_source_quorum_report

    report = {
        "available_date": "2026-06-12",
        "dry_run": False,
        "counts": {"ok": 5, "skip": 0, "fail": 1, "dry": 0},
        "jobs": [
            {"source_id": "fred:FEDFUNDS", "status": "ok"},
            {"source_id": "fred:SP500", "status": "ok"},
            {"source_id": "fred:PCOPPUSDM", "status": "ok"},
            {"source_id": "yahoo:2330.TW", "status": "ok"},
            {"source_id": "yahoo:^TWII", "status": "fail"},
            {"source_id": "noaa:oni", "status": "ok"},
        ],
        "source_health": {
            "claim_boundary": "source_contract_status_only",
            "stooq": {"status": "blocked", "default_enabled": False},
        },
    }
    dry = {
        **report,
        "dry_run": True,
        "counts": {"ok": 0, "skip": 0, "fail": 0, "dry": 6},
        "jobs": [{**job, "status": "dry"} for job in report["jobs"]],
    }
    replayed_dry_rows = {
        **dry,
        "dry_run": False,
    }

    with pytest.raises(ValueError, match="failed sources"):
        validate_source_quorum_report(report)
    with pytest.raises(ValueError, match="non-dry-run"):
        validate_source_quorum_report(dry)
    with pytest.raises(ValueError, match="missing broad source quorum"):
        validate_source_quorum_report(replayed_dry_rows)


def test_source_quorum_proof_marks_valid_live_quorum_as_proven(tmp_path):
    from scripts.source_quorum_proof import build_snapshot_command, build_source_quorum_proof, write_source_quorum_proof

    command = build_snapshot_command(
        report_json=tmp_path / "report.json",
        out_root=tmp_path / "vintage",
        python_executable="python",
    )
    proof = build_source_quorum_proof(
        _broad_source_quorum_report_with_files(tmp_path),
        snapshot_exit_code=0,
        command=command,
        observed_at="2026-06-12T00:00:00Z",
    )
    target = tmp_path / "source-quorum-proof.json"
    write_source_quorum_proof(proof, target)

    assert proof["artifact_kind"] == "source_quorum_proof"
    assert proof["status"] == "proven"
    assert proof["evidence_tier"] == "live_source_quorum"
    assert proof["claim_boundary"] == "source_contract_status_only"
    assert proof["groups"]["fred_macro"] == ["fred:FEDFUNDS"]
    assert proof["snapshot_files"]["fred:FEDFUNDS"].endswith("fred_FEDFUNDS.json")
    assert json.loads(target.read_text(encoding="utf-8"))["status"] == "proven"


def test_source_quorum_proof_rejects_scoped_or_failed_attempts(tmp_path):
    from scripts.source_quorum_proof import build_source_quorum_proof

    scoped = {
        "available_date": "2026-06-12",
        "dry_run": False,
        "counts": {"ok": 1, "skip": 0, "fail": 0, "dry": 0},
        "jobs": [{"source_id": "fred:FEDFUNDS", "status": "ok"}],
        "source_health": {
            "claim_boundary": "source_contract_status_only",
            "stooq": {"status": "blocked", "default_enabled": False},
        },
    }
    failed = _broad_source_quorum_report()

    scoped_proof = build_source_quorum_proof(
        scoped,
        snapshot_exit_code=0,
        command=["daily_snapshot"],
        observed_at="2026-06-12T00:00:00Z",
    )
    failed_proof = build_source_quorum_proof(
        failed,
        snapshot_exit_code=1,
        command=["daily_snapshot"],
        observed_at="2026-06-12T00:00:00Z",
    )

    assert scoped_proof["status"] == "not_proven"
    assert "missing broad source quorum" in scoped_proof["gate_error"]
    assert failed_proof["status"] == "not_proven"
    assert failed_proof["gate_error"] == "ValueError: snapshot command exited 1"


def test_source_quorum_proof_rejects_replayed_report_without_snapshot_files(tmp_path):
    from scripts.source_quorum_proof import build_source_quorum_proof

    report = _broad_source_quorum_report_with_files(tmp_path)
    for path in (tmp_path / "vintage" / "2026-06-12").glob("*.json"):
        path.unlink()

    proof = build_source_quorum_proof(
        report,
        snapshot_exit_code=0,
        command=["daily_snapshot"],
        observed_at="2026-06-12T00:00:00Z",
    )

    assert proof["status"] == "not_proven"
    assert "missing snapshot file" in proof["gate_error"]


def test_source_quorum_proof_cli_runs_quorum_scope_without_network(monkeypatch, tmp_path, capsys):
    from scripts import source_quorum_proof

    report_path = tmp_path / "snapshot-report.json"
    proof_path = tmp_path / "source-quorum-proof.json"

    class FakeCompleted:
        returncode = 0

    def fake_run(command, **kwargs):
        assert "--fred-series" in command
        assert source_quorum_proof.QUORUM_FRED_SERIES in command
        assert "--yahoo-symbols" in command
        assert source_quorum_proof.QUORUM_YAHOO_SYMBOLS in command
        report_path.write_text(json.dumps(_broad_source_quorum_report_with_files(tmp_path)), encoding="utf-8")
        return FakeCompleted()

    monkeypatch.setattr(source_quorum_proof.subprocess, "run", fake_run)
    rc = source_quorum_proof.main([
        "--out-root",
        str(tmp_path / "vintage"),
        "--report-json",
        str(report_path),
        "--proof-json",
        str(proof_path),
        "--python",
        "python",
    ])
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["status"] == "proven"
    assert json.loads(proof_path.read_text(encoding="utf-8"))["status"] == "proven"


def test_schedule_report_records_retention_and_latest_pointer(tmp_path):
    from scripts.snapshot_schedule_report import build_schedule_report, write_schedule_report

    report = {
        "available_date": "2026-06-11",
        "dry_run": False,
        "counts": {"ok": 2, "skip": 1, "fail": 0, "dry": 0},
        "jobs": [
            {"source_id": "fred:GOOD", "status": "ok"},
            {"source_id": "fred:OLD", "status": "skip"},
            {"source_id": "yahoo:2330.TW", "status": "ok"},
        ],
        "source_health": {
            "claim_boundary": "source_contract_status_only",
            "stooq": {"status": "blocked", "default_enabled": False},
        },
    }

    schedule = build_schedule_report(report, frequency="daily")
    target = write_schedule_report(schedule, tmp_path)

    assert schedule["status"] == "clean"
    assert schedule["frequency"] == "daily"
    assert schedule["retention"] == "append_only"
    assert (tmp_path / "latest-schedule-report.json").read_text(encoding="utf-8") == target.read_text(encoding="utf-8")


def test_schedule_run_proof_records_smoke_tier_and_degraded_exit():
    from scripts.snapshot_schedule_report import build_schedule_report, build_schedule_run_proof

    report = {
        "available_date": "2026-06-11",
        "dry_run": True,
        "counts": {"ok": 0, "skip": 0, "fail": 0, "dry": 2},
        "jobs": [
            {"source_id": "fred:GOOD", "status": "dry"},
            {"source_id": "yahoo:2330.TW", "status": "dry"},
        ],
        "source_health": {
            "claim_boundary": "source_contract_status_only",
            "stooq": {"status": "blocked", "default_enabled": False},
        },
    }
    schedule = build_schedule_report(report)

    proof = build_schedule_run_proof(
        schedule,
        workflow="daily-snapshot",
        trigger="workflow_dispatch",
        command="uv run python scripts/daily_snapshot.py --dry-run --report-json report.json",
        exit_code=0,
        started_at="2026-06-11T00:00:00Z",
        finished_at="2026-06-11T00:01:00Z",
    )
    degraded = build_schedule_run_proof(
        schedule,
        workflow="daily-snapshot",
        trigger="schedule",
        command="uv run python scripts/daily_snapshot.py --report-json report.json",
        exit_code=1,
        started_at="2026-06-11T00:00:00Z",
        finished_at="2026-06-11T00:01:00Z",
    )

    assert proof["artifact_kind"] == "snapshot_schedule_run_proof"
    assert proof["status"] == "clean"
    assert proof["evidence_tier"] == "smoke"
    assert proof["retention"] == "append_only"
    assert degraded["status"] == "degraded"
    assert degraded["evidence_tier"] == "live"


def test_daily_snapshot_workflow_records_report_and_schedule_contract():
    workflow = Path(".github/workflows/daily-snapshot.yml").read_text(encoding="utf-8")

    assert "cron:" in workflow
    assert "scripts/daily_snapshot.py --dry-run --report-json" in workflow
    assert "scripts/snapshot_schedule_report.py" in workflow
    assert "github.run_started_at" not in workflow
    assert "date -u +%Y-%m-%dT%H:%M:%SZ" in workflow


def test_scheduled_run_observer_keeps_manual_dispatch_as_pending(tmp_path):
    from scripts.scheduled_run_observer import build_scheduled_run_observation, write_scheduled_run_observation

    runs = [
        {
            "databaseId": 27387041974,
            "event": "workflow_dispatch",
            "status": "completed",
            "conclusion": "success",
            "headBranch": "spec/b-live-scheduled-snapshot-proof",
            "createdAt": "2026-06-12T00:47:01Z",
            "updatedAt": "2026-06-12T00:47:39Z",
            "url": "https://github.com/austinyuch/finance_algorithms/actions/runs/27387041974",
        },
    ]

    observation = build_scheduled_run_observation(runs, workflow="daily-snapshot")
    target = write_scheduled_run_observation(observation, tmp_path)

    assert observation["artifact_kind"] == "scheduled_run_observation"
    assert observation["status"] == "pending"
    assert observation["claim_boundary"] == "manual_dispatch_is_not_cron"
    assert observation["latest_manual_success"]["databaseId"] == 27387041974
    assert observation["latest_schedule_success"] is None
    assert "event=schedule" in observation["next_action"]
    assert target.name == "scheduled-run-observation.json"


def test_scheduled_run_observer_promotes_only_successful_schedule_run():
    from scripts.scheduled_run_observer import build_scheduled_run_observation

    runs = [
        {
            "databaseId": 10,
            "event": "schedule",
            "status": "completed",
            "conclusion": "failure",
            "headBranch": "main",
            "createdAt": "2026-06-12T02:17:00Z",
            "updatedAt": "2026-06-12T02:18:00Z",
            "url": "https://example.invalid/fail",
        },
        {
            "databaseId": 11,
            "event": "schedule",
            "status": "completed",
            "conclusion": "success",
            "headBranch": "main",
            "createdAt": "2026-06-13T02:17:00Z",
            "updatedAt": "2026-06-13T02:18:00Z",
            "url": "https://example.invalid/success",
        },
    ]

    observation = build_scheduled_run_observation(runs, workflow="daily-snapshot")

    assert observation["status"] == "proven"
    assert observation["evidence_tier"] == "live"
    assert observation["latest_schedule_success"]["databaseId"] == 11
    assert observation["latest_schedule_attempt"]["databaseId"] == 11
    assert observation["latest_failed_schedule"]["databaseId"] == 10


def test_snapshot_ops_gate_rejects_overclaimed_or_inconsistent_report():
    from scripts.snapshot_ops_gate import validate_snapshot_report

    report = {
        "available_date": "2026-06-11",
        "dry_run": False,
        "counts": {"ok": 1, "skip": 0, "fail": 0, "dry": 0},
        "jobs": [{"source_id": "stooq:spy.us", "status": "ok"}],
        "source_health": {
            "claim_boundary": "source_contract_ready",
            "stooq": {"status": "available", "default_enabled": True},
        },
    }

    with pytest.raises(ValueError, match="source_contract_status_only"):
        validate_snapshot_report(report)


def test_stooq_source_contract_decision_requires_live_proof():
    from quantlab.data.source_health import build_source_contract_reopen_evidence, decide_stooq_contract

    blocked = {
        "claim_boundary": "source_contract_status_only",
        "stooq": {"status": "blocked", "default_enabled": False},
    }
    available = {
        "claim_boundary": "source_contract_status_only",
        "stooq": {"status": "available", "default_enabled": True},
    }
    evidence = build_source_contract_reopen_evidence(
        "stooq",
        rows=[{"symbol": "spy.us", "event_date": "2026-06-11", "close": 123.45}],
        observed_at="2026-06-11T00:00:00Z",
    )

    assert decide_stooq_contract(blocked)["decision"] == "keep_default_disabled"
    assert decide_stooq_contract(available)["decision"] == "requires_live_close_rows"
    opt_in = decide_stooq_contract(available, live_close_rows=evidence["rows"])
    assert opt_in["decision"] == "eligible_for_opt_in_review"
    assert opt_in["default_enabled"] == "false"


@given(close=st.one_of(st.none(), st.floats(max_value=0, allow_nan=False, allow_infinity=False)))
def test_pbt_stooq_reopen_evidence_rejects_missing_positive_close(close):
    from quantlab.data.source_health import build_source_contract_reopen_evidence

    with pytest.raises(ValueError, match="close"):
        build_source_contract_reopen_evidence(
            "stooq",
            rows=[{"symbol": "spy.us", "event_date": "2026-06-11", "close": close}],
            observed_at="2026-06-11T00:00:00Z",
        )


@given(
    ok=st.integers(min_value=0, max_value=10),
    skip=st.integers(min_value=0, max_value=10),
    fail=st.integers(min_value=0, max_value=10),
    dry=st.integers(min_value=0, max_value=10),
)
def test_pbt_snapshot_ops_gate_counts_must_match_job_outcomes(ok, skip, fail, dry):
    from scripts.snapshot_ops_gate import validate_snapshot_report

    total = ok + skip + fail + dry
    jobs = [{"source_id": f"src:{i}", "status": "ok"} for i in range(total)]
    report = {
        "available_date": "2026-06-11",
        "dry_run": False,
        "counts": {"ok": ok, "skip": skip, "fail": fail, "dry": dry},
        "jobs": jobs,
        "source_health": {
            "claim_boundary": "source_contract_status_only",
            "stooq": {"status": "blocked", "default_enabled": False},
        },
    }

    if total == 0:
        with pytest.raises(ValueError, match="job outcomes"):
            validate_snapshot_report({**report, "jobs": []}, allow_failures=True)
    elif ok + skip + dry == 0:
        with pytest.raises(ValueError, match="no successful"):
            validate_snapshot_report(report, allow_failures=True)
    else:
        summary = validate_snapshot_report(report, allow_failures=True)
        assert summary["counts"] == report["counts"]
