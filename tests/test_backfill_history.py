"""Tests — scripts/backfill_history.py (CR-B21 historical backfill).

Covers REQ-B21-001/002: approximate marking, event_date extraction, idempotent
skip (immutability), per-source degradation, retry, and that backfilled records
load through the vintage provider (strict excludes them, approximate includes the
deep history). Network is dependency-injected. no_alpha_claim preserved.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path

import pytest

from quantlab.data.vintage import build_provider_from_vintage

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "backfill_history.py"


def _load():
    spec = importlib.util.spec_from_file_location("backfill_history", MODULE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Resp:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        return None


def _epoch(d: str) -> int:
    return int(dt.datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())


def _yahoo_payload(dates: list[str], closes: list[float]) -> str:
    return json.dumps({"chart": {"result": [{
        "timestamp": [_epoch(d) for d in dates],
        "indicators": {"quote": [{"close": closes}]},
    }]}})


def _fred_payload(rows: list[tuple[str, float]]) -> str:
    return "DATE,VALUE\n" + "\n".join(f"{d},{v}" for d, v in rows)


def _fake_get(yahoo: dict[str, str] | None = None, fred: dict[str, str] | None = None,
              fail: set[str] | None = None):
    yahoo, fred, fail = yahoo or {}, fred or {}, fail or set()

    def get(url: str, **kw):
        for sym, payload in yahoo.items():
            if f"/chart/{sym}?" in url:
                if sym in fail:
                    raise RuntimeError("transient")
                return _Resp(payload)
        for series, payload in fred.items():
            if f"id={series}" in url:
                return _Resp(payload)
        if "oni.ascii" in url:
            return _Resp("ONI\n2026 1 2 3\n")
        raise AssertionError(f"unexpected url {url}")

    return get


def _run(mod, tmp: Path, *, get, yahoo, fred, noaa=True, skip_existing=True):
    return mod.backfill(tmp, available_date="2026-06-15", since="1990-01-01",
                        until="2026-06-15", captured_at="2026-06-15T00:00:00+00:00",
                        get=get, yahoo_symbols=yahoo, fred_series=fred,
                        include_noaa=noaa, skip_existing=skip_existing)


def test_backfill_marks_approximate_and_backfill(tmp_path: Path):
    mod = _load()
    get = _fake_get(yahoo={"^GSPC": _yahoo_payload(["1990-01-02", "2026-06-08"], [350.0, 5300.0])})
    _run(mod, tmp_path, get=get, yahoo=["^GSPC"], fred=[], noaa=False)
    rec = json.loads((tmp_path / "yahoo_idx_GSPC.json").read_text())
    assert rec["is_approximate"] is True
    assert rec["backfill"] is True
    assert rec["history_start"] == "1990-01-01"
    assert rec["source"] == "yahoo:^GSPC"
    assert rec["event_date"] == "2026-06-08"


def test_backfill_extracts_fred_event_date(tmp_path: Path):
    mod = _load()
    get = _fake_get(fred={"CPIAUCSL": _fred_payload([("1947-01-01", 21.5), ("2026-05-01", 320.0)])})
    _run(mod, tmp_path, get=get, yahoo=[], fred=["CPIAUCSL"], noaa=False)
    rec = json.loads((tmp_path / "fred_CPIAUCSL.json").read_text())
    assert rec["is_approximate"] is True
    assert rec["event_date"] == "2026-05-01"


def test_backfill_idempotent_skip_does_not_overwrite(tmp_path: Path):
    mod = _load()
    # Pre-existing file must be left byte-identical (vintage immutability).
    existing = tmp_path / "yahoo_idx_GSPC.json"
    tmp_path.mkdir(parents=True, exist_ok=True)
    existing.write_text('{"sentinel": true}', encoding="utf-8")
    get = _fake_get(yahoo={"^GSPC": _yahoo_payload(["2026-06-08"], [5300.0])})
    manifest = _run(mod, tmp_path, get=get, yahoo=["^GSPC"], fred=[], noaa=False)
    assert existing.read_text() == '{"sentinel": true}'
    assert manifest["skip"] == 1 and manifest["ok"] == 0


def test_backfill_per_source_degradation(tmp_path: Path):
    mod = _load()
    # ^IXIC fetch raises (even after retries); ^GSPC + FRED must still be written.
    get = _fake_get(
        yahoo={"^GSPC": _yahoo_payload(["2026-06-08"], [5300.0]),
               "^IXIC": _yahoo_payload(["2026-06-08"], [17000.0])},
        fred={"FEDFUNDS": _fred_payload([("1954-07-01", 0.8), ("2026-05-01", 5.0)])},
        fail={"^IXIC"})
    manifest = _run(mod, tmp_path, get=get, yahoo=["^GSPC", "^IXIC"], fred=["FEDFUNDS"], noaa=False)
    assert (tmp_path / "yahoo_idx_GSPC.json").exists()
    assert (tmp_path / "fred_FEDFUNDS.json").exists()
    assert not (tmp_path / "yahoo_idx_IXIC.json").exists()
    assert manifest["ok"] == 2 and manifest["fail"] == 1
    statuses = {s["source"]: s["status"] for s in manifest["sources"]}
    assert statuses["yahoo:^IXIC"].startswith("fail")


def test_with_retries_recovers_after_transient_failure():
    mod = _load()
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("transient")
        return "ok"

    assert mod._with_retries(flaky, attempts=3, sleep_s=0) == "ok"
    assert calls["n"] == 2


def test_manifest_records_run_and_is_approximate(tmp_path: Path):
    mod = _load()
    get = _fake_get(yahoo={"^GSPC": _yahoo_payload(["2026-06-08"], [5300.0])})
    _run(mod, tmp_path, get=get, yahoo=["^GSPC"], fred=[], noaa=True)
    manifest = json.loads((tmp_path / "_backfill_manifest.json").read_text())
    assert manifest["approximate"] is True
    assert manifest["claim_boundary"] == "no_alpha_claim"
    assert manifest["since"] == "1990-01-01"


# --- REQ-B21-002: integration through the vintage provider ---

def test_backfill_loads_strict_excludes_approximate_includes(tmp_path: Path):
    mod = _load()
    raw_root = tmp_path / "raw"
    out_dir = raw_root / "backfill-1990-01-01"
    get = _fake_get(yahoo={"^GSPC": _yahoo_payload(
        ["1990-01-02", "2000-03-10", "2008-09-15", "2020-03-23", "2026-06-08"],
        [350.0, 1500.0, 1200.0, 2237.0, 5300.0])})
    mod.backfill(out_dir, available_date="2026-06-15", since="1990-01-01",
                 until="2026-06-15", captured_at="2026-06-15T00:00:00+00:00",
                 get=get, yahoo_symbols=["^GSPC"], fred_series=[], include_noaa=False)

    # approximate mode: deep history visible (available_date := event_date)
    approx = build_provider_from_vintage(raw_root, approximate_availability=True)
    prices = approx._prices
    gspc = prices[prices["symbol"] == "^GSPC"]
    assert len(gspc) == 5
    assert str(gspc["event_date"].min().date()) == "1990-01-02"

    # strict mode: backfill (is_approximate=true) excluded -> no rows
    strict = build_provider_from_vintage(raw_root, strict=True)
    assert len(strict._prices[strict._prices["symbol"] == "^GSPC"]) == 0
