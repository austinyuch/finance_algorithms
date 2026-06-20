"""Chaos hardening for scripts/daily_snapshot.py (CR-B-CHAOS-001).

完全不打網路。覆蓋既有單源失敗測試未涵蓋的極端情境:
  - 多源同時逾時/失敗的 cascade(degrade gracefully,仍寫出倖存源)
  - 寫檔原子性(中途失敗不留下截斷的 immutable 檔)
  - 200 但格式錯誤的 payload 不會讓整個 run 崩潰
Trace: REQ-B-SNAP, FMEA-B-CHAOS-01/02.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "daily_snapshot.py"


def _load():
    spec = importlib.util.spec_from_file_location("daily_snapshot_chaos", MODULE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ds = _load()


class _Resp:
    def __init__(self, text: str, status: int = 200):
        self.text = text
        self._status = status

    def raise_for_status(self) -> None:
        if self._status >= 400:
            raise ds.requests.HTTPError(f"{self._status} error")


def _fred_url(series: str) -> str:
    return "https://" + f"fred.stlouisfed.org/graph/fredgraph.csv?id={series}"


# --- CHAOS-1: multi-source timeout cascade still writes survivors and reports each failure ---

def test_main_multi_source_timeout_cascade_degrades_and_reports(monkeypatch, tmp_path):
    monkeypatch.setattr(ds, "OUT_ROOT", tmp_path)
    monkeypatch.setattr(ds, "FRED_SERIES", ["GOOD1", "TIMEOUT1", "TIMEOUT2", "GOOD2"])
    monkeypatch.setattr(ds, "STOOQ_SYMBOLS", [])
    monkeypatch.setattr(ds, "YAHOO_SYMBOLS", [])

    def fake_get(url, *a, **k):
        if "TIMEOUT" in url:
            raise ds.requests.exceptions.Timeout("read timed out")
        if "GOOD" in url:
            return _Resp("observation_date,V\n2026-05-01,1.0\n")
        return _Resp("SEAS YR oni")  # NOAA

    monkeypatch.setattr(ds.requests, "get", fake_get)
    report_path = tmp_path / "report.json"
    monkeypatch.setattr(ds.sys, "argv", ["daily_snapshot.py", "--report-json", str(report_path)])

    rc = ds.main()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    # Two FRED sources time out simultaneously; the run must not abort.
    assert rc == 1
    assert report["counts"]["fail"] == 2
    assert report["counts"]["ok"] >= 2  # GOOD1, GOOD2, noaa all written
    # Survivors are written; failures are not.
    written = {p.name for p in (tmp_path / ds._today()).glob("*.json")}
    assert any("GOOD1" in n for n in written) and any("GOOD2" in n for n in written)
    assert not any("TIMEOUT" in n for n in written)
    # Every failed job records a structured error_type (not a silent drop).
    failed = [j for j in report["jobs"] if j["status"] == "fail"]
    assert len(failed) == 2
    assert all(j["error_type"] == "Timeout" for j in failed)


# --- CHAOS-2: write is atomic — a mid-write failure leaves no truncated/immutable file ---

def test_write_is_atomic_no_partial_or_temp_on_failure(monkeypatch, tmp_path):
    def boom(src, dst):
        raise OSError("simulated crash during os.replace")

    monkeypatch.setattr(ds.os, "replace", boom)
    with pytest.raises(OSError):
        ds._write(tmp_path, "fred_X", {"k": "v"}, dry=False)

    # No final record (would otherwise be SKIP'd forever as immutable) and no temp leftover.
    assert not (tmp_path / "fred_X.json").exists()
    assert list(tmp_path.glob(".*tmp*")) == []


def test_write_atomic_success_still_writes_valid_json(tmp_path):
    status = ds._write(tmp_path, "fred_X", {"k": "v"}, dry=False)
    assert status.startswith("OK")
    assert json.loads((tmp_path / "fred_X.json").read_text(encoding="utf-8")) == {"k": "v"}
    assert list(tmp_path.glob(".*tmp*")) == []  # temp cleaned up


# --- CHAOS-3: a 200-but-malformed payload is captured, not crashed on ---

def test_fetch_fred_malformed_body_does_not_crash(monkeypatch):
    # HTML error page served with HTTP 200 (some endpoints do this) — must not raise.
    monkeypatch.setattr(ds.requests, "get", lambda *a, **k: _Resp("<html>error</html>"))
    rec = ds.fetch_fred("X", "2026-06-19")
    assert rec["source"] == "fred:X"
    assert rec["event_date"] is None  # single non-CSV line → no parsable observation date


def test_fetch_yahoo_malformed_json_raises_and_is_caught_by_main(monkeypatch, tmp_path):
    # Malformed JSON must fail that one source (caught by main), not corrupt the run.
    monkeypatch.setattr(ds, "FRED_SERIES", [])
    monkeypatch.setattr(ds, "STOOQ_SYMBOLS", [])
    monkeypatch.setattr(ds, "YAHOO_SYMBOLS", ["SPY"])
    monkeypatch.setattr(ds, "OUT_ROOT", tmp_path)

    def fake_get(url, *a, **k):
        if "yahoo" in url or "chart" in url:
            return _Resp("{not valid json")
        return _Resp("SEAS YR oni")

    monkeypatch.setattr(ds.requests, "get", fake_get)
    report_path = tmp_path / "report.json"
    monkeypatch.setattr(ds.sys, "argv", ["daily_snapshot.py", "--report-json", str(report_path)])

    rc = ds.main()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    yahoo = [j for j in report["jobs"] if j["source_id"] == "yahoo:SPY"][0]
    assert yahoo["status"] == "fail"
    assert rc == 1
