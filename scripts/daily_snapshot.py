#!/usr/bin/env python3
"""每日 point-in-time snapshot 擷取器(最小版,perishable-data 捕捉用)。

依資料治理決策:
  .agents/specs/allweather-portfolio-platform/03-data-vintage-snapshot-policy.md

設計目標:
  - 零重依賴:只用 stdlib + requests(repo 已有 requests)。
  - 公開、免金鑰端點(FRED fredgraph CSV / Stooq quotes / NOAA ONI)。
  - Append-only / immutable:每日每源寫一次,已存在則跳過(永不覆寫)。
  - Bitemporal:每筆 stamp `available_date = 擷取日`(自建 snapshot = 真實可得日,
    `is_approximate=false`),`event_date` 盡量自 payload 解析。
  - Degrade gracefully:逐源 try/except,網路/端點失敗只記錄、不中斷。

輸出:
  data/vintage/raw/{YYYY-MM-DD}/{source_id}.json

用法:
  python3 scripts/daily_snapshot.py            # 擷取今日
  python3 scripts/daily_snapshot.py --dry-run  # 只列要抓什麼,不寫檔

注意:這是 standalone 捕捉工具,刻意不依賴 quantlab/A0。Epic B 正式開發時,
      會把此流程整合進 bitemporal 儲存與 data_version 管理。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover
    print("需要 requests:uv add requests(或 pip install requests)", file=sys.stderr)
    raise

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
OUT_ROOT = REPO_ROOT / "data" / "vintage" / "raw"
TIMEOUT = 20

# FRED 序列(fredgraph CSV,免金鑰)。每日抓當前值 = 向前自建 vintage。
# 含總經 + 價格代理(SP500/那指/銅/油/台幣匯率)— FRED 在沙箱可用,繞過 Stooq 404。
# 載入時哪些當「價格資產」由 vintage loader 的 fred_price_series 決定(見 quantlab/data/vintage.py)。
FRED_SERIES = [
    # 總經
    "FEDFUNDS", "CPIAUCSL", "GDPC1", "DGS10", "DGS2", "T10Y2Y", "UNRATE",
    # 價格代理(可當資產回測)
    "SP500", "NASDAQCOM", "PCOPPUSDM", "DCOILWTICO", "DEXTAUS",
]

# 預設把哪些 FRED series 當價格資產(供 loader 參考;此處僅文件化清單)
FRED_PRICE_PROXIES = ["SP500", "NASDAQCOM", "PCOPPUSDM", "DCOILWTICO", "DEXTAUS"]

def _csv_env_symbols(name: str, default: list[str]) -> list[str]:
    raw = os.environ.get(name)
    if raw is None:
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# Stooq 報價(免金鑰 CSV)。2026-06-11 本環境重複 404,故預設停用以免 daily
# snapshot 假性失敗;若要重試,設定 QUANTLAB_STOOQ_SYMBOLS="spy.us,2330.tw"。
STOOQ_SYMBOLS = _csv_env_symbols("QUANTLAB_STOOQ_SYMBOLS", [])

# Yahoo chart fallback(免金鑰 JSON)。Stooq 在本環境穩定 404 時仍可捕捉 TSMC/TWSE。
YAHOO_SYMBOLS = [
    "SPY", "AGG", "TLT", "GLD", "DBC",
    "BTC-USD",
    "2330.TW", "^TWII",
    "TWD=X",
]

# NOAA Oceanic Niño Index(El Niño/ENSO),純文字。
NOAA_ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"


def _safe_source_id(source_id: str) -> str:
    return source_id.replace(":", "_").replace("^", "idx_")


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def _write(out_dir: Path, source_id: str, payload: dict[str, Any], dry: bool) -> str:
    """Append-only:已存在則跳過,絕不覆寫(immutable snapshot)。"""
    fpath = out_dir / f"{source_id}.json"
    if dry:
        return f"DRY  {source_id}"
    if fpath.exists():
        return f"SKIP {source_id}(今日已存在,immutable)"
    out_dir.mkdir(parents=True, exist_ok=True)
    fpath.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"OK   {source_id}"


def _source_health_summary() -> dict[str, object]:
    from quantlab.data.source_health import SourceHealthRegistry

    registry = SourceHealthRegistry()
    for series in FRED_SERIES:
        registry.record("fred", series, status="available", default_enabled=True,
                        reason="configured fredgraph source")
    if STOOQ_SYMBOLS:
        for symbol in STOOQ_SYMBOLS:
            registry.record("stooq", symbol, status="unknown", default_enabled=True,
                            reason="operator opt-in source")
    else:
        registry.record("stooq", "*", status="blocked", default_enabled=False,
                        reason="disabled by source-contract policy after observed 404s")
    for symbol in YAHOO_SYMBOLS:
        registry.record("yahoo", symbol, status="available", default_enabled=True,
                        reason="configured chart fallback source")
    registry.record("noaa", "oni", status="available", default_enabled=True,
                    reason="configured public text source")
    return registry.summary()


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _record(source: str, available_date: str, raw: Any, **extra: Any) -> dict[str, Any]:
    return {
        "source": source,
        "available_date": available_date,  # 自建 snapshot = 真實可得日
        "is_approximate": False,
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "raw": raw,
        **extra,
    }


def fetch_fred(series: str, available_date: str) -> dict[str, Any]:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    lines = [ln for ln in r.text.strip().splitlines() if ln]
    last = lines[-1].split(",") if len(lines) > 1 else []
    event_date = last[0] if last else None  # CSV 最後一列的 observation date
    return _record(f"fred:{series}", available_date, r.text, event_date=event_date)


def fetch_stooq(symbol: str, available_date: str) -> dict[str, Any]:
    url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    text = r.text.strip()
    # 第二列含 date 欄位(event_date = 報價日)
    rows = text.splitlines()
    event_date = rows[1].split(",")[1] if len(rows) > 1 else None
    return _record(f"stooq:{symbol}", available_date, text, event_date=event_date)


def _latest_yahoo_event_date(raw: str) -> str | None:
    data = json.loads(raw)
    result = (data.get("chart", {}).get("result") or [None])[0]
    if not result:
        return None
    timestamps = result.get("timestamp") or []
    quotes = result.get("indicators", {}).get("quote") or []
    closes = quotes[0].get("close", []) if quotes else []
    valid = [(ts, close) for ts, close in zip(timestamps, closes) if close is not None]
    if not valid:
        return None
    return dt.datetime.fromtimestamp(int(valid[-1][0]), dt.timezone.utc).strftime("%Y-%m-%d")


def fetch_yahoo_chart(symbol: str, available_date: str) -> dict[str, Any]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d"
    r = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    text = r.text.strip()
    return _record(f"yahoo:{symbol}", available_date, text,
                   event_date=_latest_yahoo_event_date(text))


def fetch_noaa_oni(available_date: str) -> dict[str, Any]:
    r = requests.get(NOAA_ONI_URL, timeout=TIMEOUT)
    r.raise_for_status()
    return _record("noaa:oni", available_date, r.text)


def main() -> int:
    ap = argparse.ArgumentParser(description="每日 point-in-time snapshot 擷取器")
    ap.add_argument("--dry-run", action="store_true", help="只列出要抓的源,不寫檔")
    ap.add_argument("--report-json", type=Path,
                    help="write machine-readable run summary/source-health JSON")
    args = ap.parse_args()

    available_date = _today()
    out_dir = OUT_ROOT / available_date

    jobs: list[tuple[str, Any]] = []
    jobs += [(f"fred:{s}", lambda s=s: fetch_fred(s, available_date)) for s in FRED_SERIES]
    jobs += [(f"stooq:{s}", lambda s=s: fetch_stooq(s, available_date)) for s in STOOQ_SYMBOLS]
    jobs += [(f"yahoo:{s}", lambda s=s: fetch_yahoo_chart(s, available_date)) for s in YAHOO_SYMBOLS]
    jobs += [("noaa:oni", lambda: fetch_noaa_oni(available_date))]

    print(f"[snapshot] available_date={available_date}  out={out_dir}  jobs={len(jobs)}"
          + ("  (DRY-RUN)" if args.dry_run else ""))

    ok = skip = fail = dry = 0
    job_reports: list[dict[str, Any]] = []
    for source_id, fn in jobs:
        safe_id = _safe_source_id(source_id)
        try:
            payload = None if args.dry_run else fn()
            status = _write(out_dir, safe_id, payload or {}, args.dry_run)
            if status.startswith("OK"):
                ok += 1
                outcome = "ok"
            elif status.startswith("SKIP"):
                skip += 1
                outcome = "skip"
            elif status.startswith("DRY"):
                dry += 1
                outcome = "dry"
            else:
                outcome = "unknown"
            job_reports.append({
                "source_id": source_id,
                "safe_id": safe_id,
                "status": outcome,
            })
            print(f"  {status}")
        except Exception as e:  # degrade gracefully:逐源失敗不中斷
            fail += 1
            job_reports.append({
                "source_id": source_id,
                "safe_id": safe_id,
                "status": "fail",
                "error_type": type(e).__name__,
                "error": str(e),
            })
            print(f"  FAIL {source_id}: {type(e).__name__}: {e}", file=sys.stderr)

    print(f"[snapshot] done. ok={ok} skip={skip} fail={fail}")
    if args.report_json:
        _write_report(args.report_json, {
            "available_date": available_date,
            "out_dir": str(out_dir),
            "dry_run": bool(args.dry_run),
            "counts": {"ok": ok, "skip": skip, "fail": fail, "dry": dry},
            "jobs": job_reports,
            "source_health": _source_health_summary(),
        })
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
