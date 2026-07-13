"""Tests — scripts/backfill_gap_snapshots.py (daily-loop gap-fill).

Covers the correctness-critical, network-free slicing logic: per-day cumulative
windowing, lookahead-safety (no event_date > the backfilled day D), approximate
marking, and business-day selection. FRED/NOAA are reused from an on-disk
snapshot; only Yahoo is network-bound, so slicing is fully unit-testable.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "backfill_gap_snapshots.py"


def _load():
    spec = importlib.util.spec_from_file_location("backfill_gap_snapshots", MODULE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _epoch(d: str) -> int:
    return int(dt.datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())


def test_business_days_excludes_weekends():
    mod = _load()
    # 2026-06-13 is a Saturday; range spans two weekends.
    days = mod._business_days("2026-06-13", "2026-06-22")
    assert dt.date(2026, 6, 13) not in days  # Sat
    assert dt.date(2026, 6, 14) not in days  # Sun
    assert dt.date(2026, 6, 15) in days      # Mon
    assert all(d.weekday() < 5 for d in days)


def test_slice_fred_cumulative_and_lookahead_safe():
    mod = _load()
    raw = "DATE,VALUE\n2026-06-10,1.0\n2026-06-15,2.0\n2026-07-01,3.0\n2026-07-20,4.0\n"
    # asof 2026-06-15, window from 2026-06-13: drops the pre-window 06-10 and
    # the future 07-01 / 07-20 rows.
    trimmed, last = mod.slice_fred(raw, "2026-06-13", dt.date(2026, 6, 15))
    rows = [ln for ln in trimmed.strip().splitlines()[1:]]
    assert rows == ["2026-06-15,2.0"]
    assert last == "2026-06-15"
    # a later asof accumulates more window rows but never a future one.
    trimmed2, last2 = mod.slice_fred(raw, "2026-06-13", dt.date(2026, 7, 1))
    dates2 = [r.split(",")[0] for r in trimmed2.strip().splitlines()[1:]]
    assert dates2 == ["2026-06-15", "2026-07-01"]
    assert all(d <= "2026-07-01" for d in dates2)
    assert last2 == "2026-07-01"


def test_slice_yahoo_cumulative_and_lookahead_safe():
    mod = _load()
    raw = json.dumps({"chart": {"result": [{
        "timestamp": [_epoch("2026-06-15"), _epoch("2026-06-16"), _epoch("2026-07-05")],
        "indicators": {"quote": [{"close": [10.0, 11.0, 12.0]}]},
    }]}})
    trimmed, last = mod.slice_yahoo(raw, "2026-06-13", dt.date(2026, 6, 16))
    res = json.loads(trimmed)["chart"]["result"][0]
    got = [dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d")
           for t in res["timestamp"]]
    assert got == ["2026-06-15", "2026-06-16"]           # future 07-05 dropped
    assert res["indicators"]["quote"][0]["close"] == [10.0, 11.0]
    assert last == "2026-06-16"


def test_record_marks_approximate_backfill_gapfill():
    mod = _load()
    rec = mod._record("fred:DGS10", "2026-06-15", "DATE,VALUE\n2026-06-15,4.4\n",
                      "2026-06-15", window_since="2026-06-13", captured_at="x")
    assert rec["is_approximate"] is True
    assert rec["backfill"] is True
    assert rec["gap_fill"] is True
    assert rec["available_date"] == "2026-06-15"


def test_write_is_immutable(tmp_path):
    mod = _load()
    out = tmp_path / "2026-06-15"
    rec = mod._record("fred:DGS10", "2026-06-15", "raw1", "2026-06-15",
                      window_since="2026-06-13", captured_at="x")
    assert mod._write(out, "fred:DGS10", rec, dry=False) == "OK"
    # second write must skip, never overwrite (append-only immutability).
    rec2 = dict(rec, raw="raw2")
    assert mod._write(out, "fred:DGS10", rec2, dry=False) == "SKIP"
    on_disk = json.loads((out / "fred_DGS10.json").read_text())
    assert on_disk["raw"] == "raw1"
