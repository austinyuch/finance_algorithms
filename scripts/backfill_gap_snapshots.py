#!/usr/bin/env python3
"""補洞:重建每日 snapshot 遺漏日(gap-fill,標記 approximate)。

用途:當 daily loop 因環境 egress 被擋(見 03-data-vintage-snapshot-policy.md
Decision 6)連續多日未擷取時,事後把遺漏的每日 snapshot 目錄補回。

HONESTY BOUNDARY(與 scripts/backfill_history.py 一致):
  今天才擷取的資料**不是**真實 point-in-time —— FRED 給的是最新*修訂*值,
  行情雖多為終值但仍是事後取得。故每筆一律 `is_approximate=true` + `backfill=true`
  + `gap_fill=true`。strict PIT 模式(quantlab/data/provider.py)會排除這些列,
  真實 PIT 集合不受污染;唯 `approximate_availability=True` 研究模式才會採用。

Lookahead 安全:對每個補洞日 D,各源 raw 只保留 `event_date <= D` 的觀測,
  且 `available_date = D >= event_date`,故即使 default 模式逐筆採 available_date
  也不會看到未來值。為避免與既有 1990 backfill 重複整段歷史,FRED 只截取
  `--window-since` 之後的視窗列(歷史 <= window-since 已在既有 backfill / 每日擷取中)。

輸出:data/vintage/raw/{D}/{source_id}.json(與 daily_snapshot.py 同佈局),
  immutable / append-only:已存在則跳過,絕不覆寫。

用法:
  uv run python scripts/backfill_gap_snapshots.py --since 2026-06-13 --until 2026-07-12
  uv run python scripts/backfill_gap_snapshots.py --since 2026-06-13 --until 2026-07-12 --dry-run
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import sys
from pathlib import Path
from typing import Any, Callable

try:
    import requests
except ImportError:  # pragma: no cover
    print("需要 requests:uv add requests", file=sys.stderr)
    raise

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = REPO_ROOT / "data" / "vintage" / "raw"
TIMEOUT = 30
_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

# 與 daily_snapshot.py 相同宇宙(FRED 總經 + 價格代理;Yahoo 行情;NOAA ONI)。
FRED_SERIES = [
    "FEDFUNDS", "CPIAUCSL", "GDPC1", "DGS10", "DGS2", "T10Y2Y", "UNRATE",
    "SP500", "NASDAQCOM", "PCOPPUSDM", "DCOILWTICO", "DEXTAUS",
]
YAHOO_SYMBOLS = [
    "SPY", "AGG", "TLT", "GLD", "DBC", "BTC-USD", "2330.TW", "^TWII", "TWD=X",
]
NOAA_ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"


def _safe_source_id(source_id: str) -> str:
    return source_id.replace(":", "_").replace("^", "idx_")


def _daterange(since: str, until: str) -> list[dt.date]:
    d0 = dt.date.fromisoformat(since)
    d1 = dt.date.fromisoformat(until)
    out = []
    cur = d0
    while cur <= d1:
        out.append(cur)
        cur += dt.timedelta(days=1)
    return out


def _business_days(since: str, until: str) -> list[dt.date]:
    return [d for d in _daterange(since, until) if d.weekday() < 5]


# ---- one-shot fetchers(整段抓一次,之後逐日切片)---------------------------

def fetch_fred_full(series: str, *, get: Callable = requests.get) -> str:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    r = get(url, headers={"User-Agent": _UA}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def _epoch(d: dt.date) -> int:
    return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())


def fetch_yahoo_range(symbol: str, since: str, until: str, *, get: Callable = requests.get) -> str:
    # period2 exclusive 上界多加一天,確保含 until 當日。
    p1 = _epoch(dt.date.fromisoformat(since))
    p2 = _epoch(dt.date.fromisoformat(until) + dt.timedelta(days=1))
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?period1={p1}&period2={p2}&interval=1d")
    r = get(url, headers={"User-Agent": _UA}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def fetch_noaa(*, get: Callable = requests.get) -> str:
    r = get(NOAA_ONI_URL, headers={"User-Agent": _UA}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


# ---- 逐日切片(只保留 event_date 落在 [window_since, D] 的觀測)-------------

def slice_fred(raw: str, window_since: str, asof: dt.date) -> tuple[str, str | None]:
    """回 (trimmed_csv, last_event_date)。header 保留,列僅取視窗內且 <= asof。"""
    rows = list(csv.reader(io.StringIO(raw)))
    if not rows:
        return "", None
    header, body = rows[0], rows[1:]
    lo = dt.date.fromisoformat(window_since)
    kept: list[list[str]] = []
    last_event: str | None = None
    for row in body:
        if len(row) < 2 or not row[0]:
            continue
        try:
            ev = dt.date.fromisoformat(row[0])
        except ValueError:
            continue
        if ev < lo or ev > asof:
            continue
        kept.append(row)
        last_event = row[0]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(kept)
    return buf.getvalue(), last_event


def slice_yahoo(raw: str, window_since: str, asof: dt.date) -> tuple[str, str | None]:
    """裁剪 chart JSON 的 timestamp/quote 陣列到 [window_since, asof]。回 (json, last_event)。"""
    data = json.loads(raw)
    result = (data.get("chart", {}).get("result") or [None])[0]
    if not result:
        return json.dumps(data, ensure_ascii=False), None
    lo = dt.date.fromisoformat(window_since)
    timestamps = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    adj = (result.get("indicators", {}).get("adjclose") or [{}])
    keys = [k for k in ("open", "high", "low", "close", "volume") if k in quote]

    keep_idx: list[int] = []
    last_event: str | None = None
    for i, ts in enumerate(timestamps):
        d = dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).date()
        if d < lo or d > asof:
            continue
        keep_idx.append(i)
        last_event = d.strftime("%Y-%m-%d")

    result["timestamp"] = [timestamps[i] for i in keep_idx]
    for k in keys:
        col = quote.get(k) or []
        quote[k] = [col[i] if i < len(col) else None for i in keep_idx]
    if adj and isinstance(adj[0], dict) and "adjclose" in adj[0]:
        col = adj[0].get("adjclose") or []
        adj[0]["adjclose"] = [col[i] if i < len(col) else None for i in keep_idx]
    return json.dumps(data, ensure_ascii=False), last_event


def _record(source: str, available_date: str, raw: str, event_date: str | None,
            *, window_since: str, captured_at: str) -> dict[str, Any]:
    return {
        "source": source,
        "available_date": available_date,   # 補洞日 D
        "is_approximate": True,              # 事後擷取,非真實 PIT
        "backfill": True,
        "gap_fill": True,
        "gap_window_since": window_since,
        "captured_at": captured_at,
        "raw": raw,
        "event_date": event_date,
    }


def _write(out_dir: Path, source_id: str, payload: dict[str, Any], dry: bool) -> str:
    fpath = out_dir / f"{_safe_source_id(source_id)}.json"
    if dry:
        return "DRY"
    if fpath.exists():
        return "SKIP"
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / f".{_safe_source_id(source_id)}.json.tmp"
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(fpath)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return "OK"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="重建遺漏的每日 snapshot 日(approximate gap-fill)")
    ap.add_argument("--since", required=True, help="補洞起日(含),ISO")
    ap.add_argument("--until", required=True, help="補洞迄日(含),ISO")
    ap.add_argument("--window-since", default=None,
                    help="FRED/Yahoo 視窗下界;預設 = --since(只補視窗內觀測,避免重複歷史)")
    ap.add_argument("--reuse-from", type=Path, default=None,
                    help="從既有 snapshot 目錄讀 FRED/NOAA raw(免重抓、避開 FRED 節流);"
                         "該目錄的 fred_*/noaa_oni 已含視窗內觀測時使用")
    ap.add_argument("--out-root", type=Path, default=OUT_ROOT)
    ap.add_argument("--include-weekends", action="store_true",
                    help="連週末也建目錄(預設只建工作日,週末無新觀測)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    window_since = args.window_since or args.since
    captured_at = dt.datetime.now(dt.timezone.utc).isoformat()
    days = (_daterange(args.since, args.until) if args.include_weekends
            else _business_days(args.since, args.until))
    if not days:
        print("[gap-fill] no days in range", file=sys.stderr)
        return 1

    print(f"[gap-fill] since={args.since} until={args.until} days={len(days)} "
          f"window_since={window_since}" + ("  (DRY-RUN)" if args.dry_run else ""))

    # 1) 整段抓一次(逐源 degrade)。FRED/NOAA 可從既有 snapshot 重用(免重抓)。
    fred_raw: dict[str, str] = {}
    yahoo_raw: dict[str, str] = {}
    noaa_raw: str | None = None
    fetch_fail = 0

    def _reuse_raw(src_dir: Path, source_id: str) -> str | None:
        fpath = src_dir / f"{_safe_source_id(source_id)}.json"
        if not fpath.exists():
            return None
        rec = json.loads(fpath.read_text(encoding="utf-8"))
        raw = rec.get("raw")
        return raw if isinstance(raw, str) else None

    if args.reuse_from is not None:
        for s in FRED_SERIES:
            raw = _reuse_raw(args.reuse_from, f"fred:{s}")
            if raw is not None:
                fred_raw[s] = raw
            else:
                print(f"  REUSE-MISS fred:{s} (not in {args.reuse_from})", file=sys.stderr)
        noaa_raw = _reuse_raw(args.reuse_from, "noaa:oni")
    else:
        for s in FRED_SERIES:
            try:
                fred_raw[s] = fetch_fred_full(s)
            except Exception as e:
                fetch_fail += 1
                print(f"  FETCH-FAIL fred:{s}: {type(e).__name__}: {e}", file=sys.stderr)
        try:
            noaa_raw = fetch_noaa()
        except Exception as e:
            fetch_fail += 1
            print(f"  FETCH-FAIL noaa:oni: {type(e).__name__}: {e}", file=sys.stderr)

    for s in YAHOO_SYMBOLS:
        try:
            yahoo_raw[s] = fetch_yahoo_range(s, window_since, args.until)
        except Exception as e:
            fetch_fail += 1
            print(f"  FETCH-FAIL yahoo:{s}: {type(e).__name__}: {e}", file=sys.stderr)

    if fetch_fail and not fred_raw and not yahoo_raw and noaa_raw is None:
        print("[gap-fill] all fetches failed — is egress allowlisted? aborting.", file=sys.stderr)
        return 1

    # 2) 逐日切片並寫檔。
    ok = skip = 0
    for d in days:
        asof = d
        dstr = d.isoformat()
        out_dir = args.out_root / dstr
        for s, raw in fred_raw.items():
            trimmed, last_event = slice_fred(raw, window_since, asof)
            rec = _record(f"fred:{s}", dstr, trimmed, last_event,
                          window_since=window_since, captured_at=captured_at)
            st = _write(out_dir, f"fred:{s}", rec, args.dry_run)
            ok += st == "OK"; skip += st == "SKIP"
        for s, raw in yahoo_raw.items():
            trimmed, last_event = slice_yahoo(raw, window_since, asof)
            rec = _record(f"yahoo:{s}", dstr, trimmed, last_event,
                          window_since=window_since, captured_at=captured_at)
            st = _write(out_dir, f"yahoo:{s}", rec, args.dry_run)
            ok += st == "OK"; skip += st == "SKIP"
        if noaa_raw is not None:
            rec = _record("noaa:oni", dstr, noaa_raw, None,
                          window_since=window_since, captured_at=captured_at)
            st = _write(out_dir, "noaa:oni", rec, args.dry_run)
            ok += st == "OK"; skip += st == "SKIP"

    print(f"[gap-fill] done. days={len(days)} files_ok={ok} skip={skip} fetch_fail={fetch_fail}")
    return 0 if fetch_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
