#!/usr/bin/env python3
"""B-2 demo:載入真實 vintage → 報告就緒狀態 →(資料夠就)跑回測。

把累積中的 vintage snapshot 以 FRED 價格代理當資產載入,誠實報告目前有多少真實
macro / price 資料;若價格資產 >=2 且歷史夠,就跑一個靜態配置回測 demo。

用法:uv run python scripts/run_vintage_slice.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quantlab.data.vintage import build_provider_from_vintage
from quantlab.runner import run_and_log
from quantlab.strategies import StaticWeights
from quantlab.tracking import LocalResultStore

VINTAGE_ROOT = Path(__file__).resolve().parents[1] / "data" / "vintage" / "raw"
PRICE_PROXIES = {"SP500", "NASDAQCOM", "PCOPPUSDM", "DCOILWTICO", "DEXTAUS"}


def main() -> int:
    p = build_provider_from_vintage(VINTAGE_ROOT, fred_price_series=PRICE_PROXIES)
    macro_series = sorted(set(p._macro["series"])) if len(p._macro) else []
    price_assets = sorted(set(p._prices["symbol"])) if len(p._prices) else []

    print(f"vintage root : {VINTAGE_ROOT}")
    print(f"macro series : {len(macro_series)}  {macro_series}")
    print(f"price assets : {len(price_assets)}  {price_assets}")

    if len(price_assets) < 2:
        print("\n[readiness] 真實價格資產不足(<2)→ 跳過回測。")
        print("price proxies 從下一次 snapshot(已加入 FRED_SERIES)開始累積;")
        print("待累積足夠歷史後,本腳本即可在真實資料上跑配置回測。")
        return 0

    # 有足夠價格 → 跑等權靜態配置 demo(後續可換 HedgeStrategy / LSTM)
    span = p._prices["event_date"]
    cfg = {"start": str(span.min().date()), "end": str(span.max().date()), "rebalance": "monthly",
           "fill": "same_close", "mode": "net",
           "cost_config": {"commission_bps": 5, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
                           "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
           "seed": 0, "data_version": "vintage",
           "walk_forward": {"train_window_months": 12, "test_window_months": 6, "step_months": 6}}
    store = LocalResultStore(Path("/tmp") / "vintage_slice.db")
    _, res = run_and_log(StaticWeights({s: 1.0 for s in price_assets}), p, cfg, store)
    full = next(m for m in res["metrics"] if m["segment"] == "full")
    print(f"\n[backtest] StaticWeights 等權 {price_assets}")
    print(f"  cumulative={full['cumulative_return']:.4f} vol={full['annualized_vol']:.4f} "
          f"maxDD={full['max_drawdown']:.4f} sharpe={full['sharpe']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
