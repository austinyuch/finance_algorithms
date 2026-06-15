#!/usr/bin/env python3
"""Historical vintage backfill (CR-B21) — deep multi-cycle history, marked approximate.

Fetches deep history (Yahoo ``period1=<since>``, full FRED series, NOAA ONI) for
the configured universe and writes ``is_approximate=true`` vintage records under
``data/vintage/raw/backfill-<since>/``.

HONESTY BOUNDARY: data fetched today is NOT true point-in-time — ``available_date``
is the capture date, and FRED macro values are latest-*revised*. Every record is
marked ``is_approximate=true`` + ``backfill=true``. In strict PIT mode the loader
excludes these rows (only genuine daily captures remain); only
``approximate_availability=True`` exposes them (``available_date = event_date``),
enabling multi-regime research backtests under ``no_alpha_claim``. Never true PIT,
never an alpha claim. (Stooq stays de-scoped — see CR-B20.)

Usage:
  uv run python scripts/backfill_history.py [--since 1990-01-01] [--until YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import datetime as dt
import functools
import json
import time
from pathlib import Path
from typing import Any, Callable, Sequence

import requests

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_ROOT = ROOT / "data" / "vintage" / "raw"
TIMEOUT = 30
_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

# Deep indices (^GSPC 1927, ^IXIC 1971) added for 1990+ equity coverage beyond the
# ETF start dates; remaining symbols mirror the daily YAHOO_SYMBOLS universe.
YAHOO_BACKFILL: list[str] = [
    "^GSPC", "^IXIC", "SPY", "AGG", "TLT", "GLD", "DBC", "BTC-USD",
    "2330.TW", "^TWII", "TWD=X",
]
FRED_BACKFILL: list[str] = [
    "FEDFUNDS", "CPIAUCSL", "GDPC1", "DGS10", "DGS2", "T10Y2Y", "UNRATE",
    "SP500", "NASDAQCOM", "PCOPPUSDM", "DCOILWTICO", "DEXTAUS",
]
NOAA_ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

Getter = Callable[..., Any]


def _safe_source_id(source_id: str) -> str:
    return source_id.replace(":", "_").replace("^", "idx_")


def _epoch(date_str: str) -> int:
    return int(dt.datetime.strptime(date_str, "%Y-%m-%d")
               .replace(tzinfo=dt.timezone.utc).timestamp())


def _with_retries(fn: Callable[[], str], *, attempts: int = 3, sleep_s: float = 1.5) -> str:
    """Retry transient network failures (the live probe hit intermittent HTTP 000)."""
    last: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — transient network/HTTP; retry
            last = exc
            if i < attempts - 1 and sleep_s:
                time.sleep(sleep_s)
    assert last is not None
    raise last


def fetch_yahoo_history(symbol: str, since: str, until: str, *, get: Getter = requests.get) -> str:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?period1={_epoch(since)}&period2={_epoch(until)}&interval=1d")
    r = get(url, headers={"User-Agent": _UA}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def fetch_fred_full(series: str, *, get: Getter = requests.get) -> str:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    r = get(url, headers={"User-Agent": _UA}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def fetch_noaa(*, get: Getter = requests.get) -> str:
    r = get(NOAA_ONI_URL, headers={"User-Agent": _UA}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def _last_yahoo_event_date(raw: str) -> str | None:
    data = json.loads(raw)
    result = (data.get("chart", {}).get("result") or [None])[0]
    if not result:
        return None
    timestamps = result.get("timestamp") or []
    quotes = result.get("indicators", {}).get("quote") or []
    closes = quotes[0].get("close", []) if quotes else []
    valid = [ts for ts, close in zip(timestamps, closes) if close is not None]
    if not valid:
        return None
    return dt.datetime.fromtimestamp(int(valid[-1]), dt.timezone.utc).strftime("%Y-%m-%d")


def _last_fred_event_date(raw: str) -> str | None:
    lines = [ln for ln in raw.strip().splitlines() if ln]
    if len(lines) <= 1:
        return None
    return lines[-1].split(",")[0]


def _no_event(_raw: str) -> None:
    """Event-date extractor for sources without a tabular last-row (e.g. NOAA ONI)."""
    return None


def _record(source: str, available_date: str, raw: str, event_date: str | None,
            *, since: str, captured_at: str) -> dict[str, Any]:
    return {
        "source": source,
        "available_date": available_date,
        "is_approximate": True,   # NOT true PIT — fetched today, macro is revised
        "backfill": True,
        "history_start": since,
        "captured_at": captured_at,
        "raw": raw,
        "event_date": event_date,
    }


def _write(out_dir: Path, source_id: str, payload: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{_safe_source_id(source_id)}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def backfill(
    out_dir: Path, *, available_date: str, since: str, until: str, captured_at: str,
    get: Getter = requests.get,
    yahoo_symbols: Sequence[str] = tuple(YAHOO_BACKFILL),
    fred_series: Sequence[str] = tuple(FRED_BACKFILL),
    include_noaa: bool = True,
    skip_existing: bool = True,
) -> dict[str, Any]:
    """Fetch deep history per source; degrade per source; skip existing (immutable)."""
    results: list[dict[str, str]] = []

    def _do(source_id: str, fetch: Callable[[], str], last_event: Callable[[str], str | None]) -> None:
        fpath = out_dir / f"{_safe_source_id(source_id)}.json"
        if skip_existing and fpath.exists():
            results.append({"source": source_id, "status": "skip"})
            return
        try:
            raw = _with_retries(fetch)
            _write(out_dir, source_id,
                   _record(source_id, available_date, raw, last_event(raw),
                           since=since, captured_at=captured_at))
            results.append({"source": source_id, "status": "ok"})
        except Exception as exc:  # noqa: BLE001 — per-source degradation
            results.append({"source": source_id, "status": f"fail:{type(exc).__name__}"})

    for sym in yahoo_symbols:
        _do(f"yahoo:{sym}",
            functools.partial(fetch_yahoo_history, sym, since, until, get=get),
            _last_yahoo_event_date)
    for series in fred_series:
        _do(f"fred:{series}",
            functools.partial(fetch_fred_full, series, get=get),
            _last_fred_event_date)
    if include_noaa:
        _do("noaa:oni", functools.partial(fetch_noaa, get=get), _no_event)

    manifest = {
        "kind": "historical_backfill_manifest",
        "approximate": True,
        "claim_boundary": "no_alpha_claim",
        "since": since, "until": until,
        "available_date": available_date, "captured_at": captured_at,
        "ok": sum(r["status"] == "ok" for r in results),
        "skip": sum(r["status"] == "skip" for r in results),
        "fail": sum(r["status"].startswith("fail") for r in results),
        "sources": results,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "_backfill_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Deep historical vintage backfill (approximate)")
    ap.add_argument("--since", default="1990-01-01")
    ap.add_argument("--until", default=None, help="ISO date; default today UTC")
    ap.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    ap.add_argument("--capture-date", default=None, help="available_date; default today UTC")
    args = ap.parse_args(argv)

    now = dt.datetime.now(dt.timezone.utc)
    until = args.until or now.strftime("%Y-%m-%d")
    available_date = args.capture_date or now.strftime("%Y-%m-%d")
    out_dir = args.out_root / f"backfill-{args.since}"

    manifest = backfill(out_dir, available_date=available_date, since=args.since,
                        until=until, captured_at=now.isoformat())
    print(f"[backfill] out={out_dir} since={args.since} until={until} "
          f"ok={manifest['ok']} skip={manifest['skip']} fail={manifest['fail']}")
    return 0 if manifest["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
