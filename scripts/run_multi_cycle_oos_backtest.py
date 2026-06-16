#!/usr/bin/env python
"""CLI — multi-cycle, multi-asset OOS-net evaluation across D model families (CR-RDO-005).

Loads the CR-B21 deep historical backfill (`data/vintage/raw/backfill-1990-01-01`)
with explicit `approximate_availability=True` (NOT true PIT — `is_approximate=true`,
strict-mode excluded), resolves the deepest co-temporal universe, and runs a
BuyAndHold baseline plus the regime / return-risk / robust D model families through
one shared multi-cycle window. Emits a checksummed leaderboard.

Exit codes: 0 = computed comparison written; 2 = fail-closed (insufficient data,
oversampled vs native cadence, or degenerate flat OOS). no_alpha_claim throughout.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quantlab.data.vintage import build_provider_from_vintage  # noqa: E402
from quantlab.models.regime import FirstRegimeClassifier, RegimeAllocationStrategy  # noqa: E402
from quantlab.models.return_risk import ForecastAllocationStrategy, ReturnRiskForecaster  # noqa: E402
from quantlab.models.robust_optimization import (  # noqa: E402
    RobustOptimizationStrategy, RobustPortfolioModel,
)
from quantlab.research.real_data_oos import (  # noqa: E402
    SamplingFrequencyError, assess_data_sufficiency,
)
from quantlab.research import multi_cycle_oos as mco  # noqa: E402
from quantlab.strategies import BuyAndHold  # noqa: E402
from quantlab.tracking import LocalResultStore  # noqa: E402

_REPO = Path(__file__).resolve().parents[1]
_BACKFILL_ROOT = _REPO / "data" / "vintage" / "raw" / "backfill-1990-01-01"
_DEFAULT_OUT = (_REPO / ".agents" / "specs" / "real-data-oos-backtest" / "reports"
                / "multi-cycle-family-oos-artifact.json")
# 25y forces a window spanning dot-com / GFC / COVID / 2022 while staying multi-asset.
_MIN_HISTORY_MONTHS = 300.0

_COST_CONFIG = {"commission_bps": 5, "slippage_bps": 5, "tw_transaction_tax_bps": 0,
                "us_dividend_withholding_pct": 0, "fx_spread_bps": 0}
_WALK_FORWARD = {"train_window_months": 12, "test_window_months": 6, "step_months": 6}


def _config() -> dict[str, Any]:
    return {"rebalance": "monthly", "mode": "net", "cost_config": _COST_CONFIG,
            "walk_forward": _WALK_FORWARD, "seed": 0}


def _families():
    """family_name -> (universe -> Strategy). Each declares no_alpha_claim."""
    def regime_factory(u):
        # Deepest-history index drives the price-trend; T10Y2Y curve is degraded
        # (missing in the current backfill — CR-B21 FRED residual). Risk-on tilts to
        # the higher-beta tail asset, defensive concentrates the lead index.
        return RegimeAllocationStrategy(
            FirstRegimeClassifier(price_symbol=u[0]),
            risk_on_weights={u[-1]: 1.0}, defensive_weights={u[0]: 1.0},
        )

    return {
        "regime": regime_factory,
        "return_risk": lambda u: ForecastAllocationStrategy(ReturnRiskForecaster(list(u))),
        "robust": lambda u: RobustOptimizationStrategy(RobustPortfolioModel(list(u))),
    }


def run_multi_cycle_oos(provider: Any, *, generated_at: str, out: str | Path | None = None,
                        min_assets: int = 2, min_history_months: float = _MIN_HISTORY_MONTHS) -> int:
    config = _config()
    suff = assess_data_sufficiency(provider, min_assets=min_assets,
                                   min_history_months=min_history_months)
    if not suff.sufficient:
        report = mco.build_multi_cycle_insufficient_report(
            suff, config={**config, "availability_mode": "approximate_event_date"})
        art = mco.build_multi_cycle_artifact(report, artifact_uri=_uri(out),
                                             generated_at=generated_at)
        _emit(art, out)
        print(f"insufficient_data: {suff.reason}", file=sys.stderr)
        return 2

    store = LocalResultStore(":memory:")
    try:
        report = mco.build_multi_cycle_family_oos_report(
            provider, families=_families(), baseline_build=lambda u: BuyAndHold(list(u)),
            config=config, min_assets=min_assets, min_history_months=min_history_months,
            store=store, availability_mode="approximate_event_date",
        )
    except SamplingFrequencyError:
        return _fail_closed(suff, config, out, generated_at, "oversampled_vs_native_frequency")
    except ValueError as exc:
        reason = "degenerate_flat_oos" if "degenerate" in str(exc) else "comparison_failed"
        return _fail_closed(suff, config, out, generated_at, reason)

    art = mco.build_multi_cycle_artifact(report, artifact_uri=_uri(out), generated_at=generated_at)
    _emit(art, out)
    return 0


def _fail_closed(suff: Any, config: dict, out: str | Path | None, generated_at: str,
                 reason: str) -> int:
    report = mco.build_multi_cycle_insufficient_report(
        suff, config={**config, "availability_mode": "approximate_event_date"})
    report["reason"] = reason
    art = mco.build_multi_cycle_artifact(report, artifact_uri=_uri(out), generated_at=generated_at)
    _emit(art, out)
    print(f"insufficient_data: {reason}", file=sys.stderr)
    return 2


def _uri(out: str | Path | None) -> str:
    return f"file://{Path(out).resolve()}" if out else "stdout://multi-cycle-family-oos"


def _emit(artifact: dict, out: str | Path | None) -> None:
    if out:
        mco.write_multi_cycle_artifact(artifact, out)
    else:
        import json
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Multi-cycle multi-asset family OOS-net backtest")
    parser.add_argument("--out", default=str(_DEFAULT_OUT), help="output artifact path (or '-' for stdout)")
    parser.add_argument("--vintage-root", default=str(_BACKFILL_ROOT))
    parser.add_argument("--generated-at", default=None)
    parser.add_argument("--min-history-months", type=float, default=_MIN_HISTORY_MONTHS)
    args = parser.parse_args(list(argv) if argv is not None else None)

    generated_at = args.generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = None if args.out == "-" else args.out
    # SP500 promoted to a price asset so a future curve-bearing regime can use it;
    # Yahoo deep equities load as price assets automatically. Approximate availability.
    provider = build_provider_from_vintage(
        args.vintage_root, fred_price_series={"SP500"}, approximate_availability=True)
    return run_multi_cycle_oos(provider, generated_at=generated_at, out=out,
                               min_assets=2, min_history_months=args.min_history_months)


if __name__ == "__main__":
    raise SystemExit(main())
