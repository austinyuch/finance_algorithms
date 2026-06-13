#!/usr/bin/env python3
"""Real-data >=2-asset OOS-net backtest CLI (spec: real-data-oos-backtest).

Loads accumulated real PIT vintage data, and — only when >=2 price assets with a
walk-forward-viable window exist — runs a candidate strategy against a dumb
baseline through the existing A0 engine and emits a checksumed OOS-net comparison
artifact. Otherwise it fails closed (exit 2) with an ``insufficient_data``
artifact. Every artifact carries ``claim_boundary=no_alpha_claim``; this proves
mechanism on real-source data, never alpha.

Usage:
  uv run python scripts/run_real_data_oos_backtest.py [--out PATH] [--generated-at ISO]
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quantlab.data.vintage import build_provider_from_vintage
from quantlab.research.real_data_oos import (
    assess_data_sufficiency,
    build_insufficient_data_report,
    build_real_data_oos_artifact,
    build_real_data_oos_report,
)
from quantlab.strategies import BuyAndHold, RandomStrategy, SmaTimingStrategy

VINTAGE_ROOT = Path(__file__).resolve().parents[1] / "data" / "vintage" / "raw"
PRICE_PROXIES = {"SP500", "NASDAQCOM", "PCOPPUSDM", "DCOILWTICO", "DEXTAUS"}
_COST_CONFIG = {"commission_bps": 5, "slippage_bps": 5, "tw_transaction_tax_bps": 0,
                "us_dividend_withholding_pct": 0, "fx_spread_bps": 0}
_WALK_FORWARD = {"train_window_months": 12, "test_window_months": 6, "step_months": 6}


def _config() -> dict[str, Any]:
    return {"rebalance": "monthly", "mode": "net", "cost_config": dict(_COST_CONFIG),
            "walk_forward": dict(_WALK_FORWARD), "seed": 0}


def run_real_data_oos(
    provider: Any, *, generated_at: str, out: str | Path | None = None,
    candidate: Any | None = None, baseline: Any | None = None,
    min_assets: int = 1, min_history_months: float = 18.0,
    availability_mode: str = "true_pit",
) -> int:
    """Core decision path (dependency-injected for tests). Returns the exit code."""
    config = _config()
    suff = assess_data_sufficiency(provider, min_assets=min_assets,
                                   min_history_months=min_history_months)
    artifact_uri = f"file://{Path(out).resolve()}" if out else "stdout://real-data-oos"

    if not suff.sufficient:
        report = build_insufficient_data_report(suff, config=config)
        artifact = build_real_data_oos_artifact(report, artifact_uri=artifact_uri,
                                                generated_at=generated_at)
        _emit(artifact, out)
        print(f"[fail-closed] status=insufficient_data reason={suff.reason} "
              f"assets={suff.asset_count} span_months={suff.history_span_months}", file=sys.stderr)
        return 2

    # CR-RDO-001: trade only the co-temporal subset that shares the walk-forward
    # window. CR-RDO-003: a single market index compares a timing candidate vs a
    # buy-and-hold baseline (>=2 assets keeps the cross-sectional random/static mix).
    assets = list(suff.cotemporal_universe)
    if candidate is not None:
        cand = candidate
    elif len(assets) == 1:
        cand = SmaTimingStrategy(assets[0], window=6)
    else:
        cand = RandomStrategy(assets, seed=0)
    base = baseline if baseline is not None else BuyAndHold(assets)
    try:
        report = build_real_data_oos_report(provider, candidate=cand, baseline=base, config=config,
                                            min_assets=min_assets, min_history_months=min_history_months,
                                            availability_mode=availability_mode)
    except ValueError as exc:
        # Degenerate (flat OOS — e.g. PIT-invisible single-capture data): fail
        # closed gracefully instead of emitting a misleading "computed" artifact.
        degenerate = replace(suff, sufficient=False, reason="degenerate_flat_oos")
        report = build_insufficient_data_report(degenerate, config=config)
        artifact = build_real_data_oos_artifact(report, artifact_uri=artifact_uri,
                                                generated_at=generated_at)
        _emit(artifact, out)
        print(f"[fail-closed] degenerate real-data OOS: {exc}", file=sys.stderr)
        return 2
    artifact = build_real_data_oos_artifact(report, artifact_uri=artifact_uri,
                                            generated_at=generated_at)
    _emit(artifact, out)
    return 0


def _emit(artifact: dict[str, Any], out: str | Path | None) -> None:
    text = json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True)
    if out is None:
        print(text)
        return
    from quantlab.research.real_data_oos import write_real_data_oos_artifact
    write_real_data_oos_artifact(artifact, out)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Real-data >=2-asset OOS-net backtest")
    parser.add_argument("--out", default=None, help="write checksumed artifact JSON here")
    parser.add_argument("--generated-at", default=None, help="ISO timestamp (default: now UTC)")
    args = parser.parse_args(argv)
    generated_at = args.generated_at or datetime.now(timezone.utc).isoformat()
    # CR-RDO-003: use the market index (SP500) — a high-frequency series with real
    # history — not the low-frequency macro proxies; with explicit approximate
    # (event-date) availability so single-capture vintage is visible to historical
    # as-ofs. NOT true PIT; the artifact records availability_mode accordingly.
    provider = build_provider_from_vintage(
        VINTAGE_ROOT, fred_price_series={"SP500"}, approximate_availability=True)
    return run_real_data_oos(provider, generated_at=generated_at, out=args.out,
                             min_assets=1, availability_mode="approximate_event_date")


if __name__ == "__main__":
    raise SystemExit(main())
