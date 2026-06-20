#!/usr/bin/env python
"""Parameterized deep-learning experiment CLI (REQ-H-EXPERIMENT-001).

Build a deep-learning experiment from tunable parameters, run the deep model plus a dumb
baseline through the A0 engine on >=2 co-temporal price assets, emit a checksummed
performance report + self-contained SVG, and record MLOps lineage in the
`ExperimentRegistry`. Fails closed with `status=insufficient_data` (exit 2) when there is
not enough co-temporal history; registers nothing in that case.

This is the "set parameters → run → see results" research mechanism. Every output carries
`no_alpha_claim`; deep history (CR-B21 backfill) is approximate and research-mode only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from quantlab.models import DeepForecastAllocationStrategy, NumpyMLPForecaster
from quantlab.mlops.experiment_registry import ExperimentRegistry
from quantlab.research import build_deep_model_performance_report, render_performance_report_svg
from quantlab.runner import run_and_log
from quantlab.strategies import StaticWeights
from quantlab.tracking import LocalResultStore

_MODEL_NAME = "DeepForecastAllocationStrategy"
_BASELINE_NAME = "StaticWeights"
_MIN_COTEMPORAL_MONTHS = 24


def exit_code_for(result: Mapping[str, Any]) -> int:
    """Map an experiment result to a process exit code (0 computed, 2 fail-closed)."""
    return 0 if result.get("status") == "computed" else 2


def _cotemporal_dates(provider: Any, symbols: Sequence[str]) -> list[pd.Timestamp]:
    panel = provider.price_panel()
    present = set(provider.symbols())
    requested = [s for s in symbols if s in present]
    if len(requested) < 2:
        return []
    date_sets = [set(panel.loc[panel["symbol"] == s, "event_date"]) for s in requested]
    common = sorted(set.intersection(*date_sets))
    return [pd.Timestamp(d) for d in common]


def _closes(data: Any, asof: pd.Timestamp, symbols: Sequence[str]) -> dict[str, float]:
    hist = data.history(asof, "close", list(symbols))
    out: dict[str, float] = {}
    for symbol in symbols:
        if symbol in hist.columns:
            col = hist[symbol].dropna()
            if col.size:
                out[symbol] = float(col.iloc[-1])
    return out


def realize_net_return_series(strategy: Any, data: Any, dates: Sequence[pd.Timestamp],
                              symbols: Sequence[str], *, commission_bps: float) -> list[float]:
    """Transparent realized net path: hold PIT weights one period, net of commission.

    Weights at each step are decided strictly before the realized return, so the path is
    out-of-sample by construction. This is the research statistical surface; the canonical
    OOS-net ranking still comes from the A0 engine leaderboard.
    """
    prev_w: dict[str, float] = {}
    series: list[float] = []
    for i in range(1, len(dates)):
        weights = dict(strategy.generate_signal(dates[i - 1], data))
        p_prev = _closes(data, dates[i - 1], symbols)
        p_now = _closes(data, dates[i], symbols)
        gross = sum(
            w * (p_now[s] / p_prev[s] - 1.0)
            for s, w in weights.items()
            if s in p_prev and s in p_now and p_prev[s] > 0
        )
        turnover = sum(abs(weights.get(s, 0.0) - prev_w.get(s, 0.0))
                       for s in set(weights) | set(prev_w))
        series.append(float(gross - turnover * commission_bps / 1e4))
        prev_w = weights
    return series


def _config(dates: Sequence[pd.Timestamp], rebalance: str) -> dict[str, Any]:
    return {
        "start": str(dates[0].date()),
        "end": str(dates[-1].date()),
        "rebalance": rebalance,
        "fill": "same_close",
        "mode": "net",
        "cost_config": {"commission_bps": 5, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
                        "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
        "seed": 0,
        "data_version": "deep-forecast-experiment",
        "walk_forward": {"train_window_months": 36, "test_window_months": 12, "step_months": 12},
    }


def run_experiment(
    provider: Any,
    *,
    symbols: Sequence[str],
    hidden_units: int,
    lookback: int,
    epochs: int,
    seed: int,
    rebalance: str,
    backend: str,
    out_path: str | Path,
    viz_path: str | Path,
    registry_path: str | Path,
    commission_bps: float = 5.0,
    periods_per_year: int = 12,
) -> dict[str, Any]:
    """Run one parameterized experiment; fail closed on insufficient co-temporal data."""
    out_path, viz_path, registry_path = Path(out_path), Path(viz_path), Path(registry_path)
    dates = _cotemporal_dates(provider, symbols)
    present = set(provider.symbols())
    requested = sorted({s for s in symbols if s in present})

    if len(requested) < 2 or len(dates) < _MIN_COTEMPORAL_MONTHS:
        return {
            "status": "insufficient_data",
            "reason": "fewer_than_2_assets" if len(requested) < 2 else "thin_cotemporal_history",
            "claim_boundary": "no_alpha_claim",
            "cotemporal_months": len(dates),
        }

    cfg = _config(dates, rebalance)
    forecaster = NumpyMLPForecaster(requested, lookback=lookback, hidden=hidden_units,
                                    epochs=epochs, seed=seed, backend=backend)
    model = DeepForecastAllocationStrategy(forecaster)
    baseline = StaticWeights({s: 1.0 for s in requested})

    store = LocalResultStore(out_path.with_suffix(".runs.sqlite"))
    try:
        model_run_id, _ = run_and_log(model, provider, cfg, store)
        baseline_run_id, _ = run_and_log(baseline, provider, cfg, store)
        leaderboard = store.leaderboard()
    finally:
        store.close()

    series = {
        _MODEL_NAME: realize_net_return_series(model, provider, dates, requested,
                                               commission_bps=commission_bps),
        _BASELINE_NAME: realize_net_return_series(baseline, provider, dates, requested,
                                                  commission_bps=commission_bps),
    }
    # representative full-history learning curve
    forecaster.forecast(dates[-1], provider)
    report = build_deep_model_performance_report(
        series, learning_curve=forecaster.training_trace,
        model_name=_MODEL_NAME, baseline_name=_BASELINE_NAME,
        periods_per_year=periods_per_year,
    )

    params = {
        "symbols": requested,
        "hidden_units": int(hidden_units),
        "lookback": int(lookback),
        "epochs": int(epochs),
        "seed": int(seed),
        "rebalance": rebalance,
        "backend": forecaster.backend,
        "commission_bps": float(commission_bps),
    }
    model_row = next(r for r in report["rows"] if r["strategy_name"] == _MODEL_NAME)
    registry = ExperimentRegistry(registry_path)
    entry = registry.register(
        "NumpyMLPForecaster", _MODEL_NAME, params,
        run_ids=[model_run_id, baseline_run_id],
        metrics={"oos_net_sharpe": float(model_row["oos_net_sharpe"])},
        claim_boundary="no_alpha_claim",
        tags=["epic-h", "deep-learning", forecaster.backend],
    )

    artifact = {
        "status": "computed",
        "claim_boundary": "no_alpha_claim",
        "backend": forecaster.backend,
        "experiment_id": entry.experiment_id,
        "parameters": params,
        "leaderboard": leaderboard,
        "performance_report": report,
        "viz_path": str(viz_path),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    viz_path.parent.mkdir(parents=True, exist_ok=True)
    viz_path.write_text(render_performance_report_svg(report), encoding="utf-8")

    return {
        "status": "computed",
        "artifact_path": str(out_path),
        "viz_path": str(viz_path),
        "experiment_id": entry.experiment_id,
        "backend": forecaster.backend,
        "parameters": params,
        "data_window": {"start": str(dates[0].date()), "end": str(dates[-1].date())},
        "performance_report": report,
        "leaderboard": leaderboard,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", nargs="+", default=["^GSPC", "^IXIC"],
                        help="price symbols (>=2 co-temporal assets)")
    parser.add_argument("--hidden-units", type=int, default=8)
    parser.add_argument("--lookback", type=int, default=6)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rebalance", default="monthly",
                        choices=["daily", "weekly", "monthly", "quarterly"])
    parser.add_argument("--backend", default="reference",
                        choices=["reference", "pytorch", "jax", "tensorflow"])
    parser.add_argument("--commission-bps", type=float, default=5.0)
    parser.add_argument("--vintage-root", default="data/vintage/raw/backfill-1990-01-01",
                        help="vintage snapshot root (research/approximate mode)")
    parser.add_argument("--out", default="out/dl-experiment.json")
    parser.add_argument("--viz", default="out/dl-experiment.svg")
    parser.add_argument("--registry", default="out/dl-experiments.jsonl")
    return parser


def _build_provider_from_vintage(args: argparse.Namespace) -> Any:
    # Research mode: approximate availability exposes the CR-B21 deep backfill (strict PIT
    # excludes it). Honest no_alpha_claim research surface.
    from quantlab.data.vintage import build_provider_from_vintage

    return build_provider_from_vintage(args.vintage_root, approximate_availability=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # --help / arg errors
        return int(exc.code or 0)

    try:
        provider = _build_provider_from_vintage(args)
    except Exception as exc:  # noqa: BLE001 — fail closed, honest
        print(f"[insufficient_data] could not build provider: {exc}", file=sys.stderr)
        return 2

    result = run_experiment(
        provider, symbols=args.symbols, hidden_units=args.hidden_units,
        lookback=args.lookback, epochs=args.epochs, seed=args.seed,
        rebalance=args.rebalance, backend=args.backend, commission_bps=args.commission_bps,
        out_path=args.out, viz_path=args.viz, registry_path=args.registry,
    )
    print(json.dumps({k: v for k, v in result.items()
                      if k in {"status", "experiment_id", "artifact_path", "reason",
                               "cotemporal_months"}}, ensure_ascii=False))
    return exit_code_for(result)


if __name__ == "__main__":
    raise SystemExit(main())
