"""Multi-cycle, multi-asset OOS-net evaluation across D model families (CR-RDO-005).

Overlay on the completed ``real-data-oos-backtest`` and ``d-model-family-evaluation``
baselines. Runs a dumb baseline plus every registered D model family through the
**same** real co-temporal universe / as-of window, in one pass, and emits a
checksumed leaderboard ranked on out-of-sample **net** Sharpe only.

This is ``no_alpha_claim`` *mechanism + comparability* evidence on
approximate-availability deep history — explicitly NOT true PIT and NOT a strategy
verdict. Every single-window honesty guard is *reused* (not re-implemented):
co-temporal sufficiency (CR-RDO-001), sampling-frequency oversampling (CR-RDO-004),
and flat-OOS degeneracy (CR-RDO-003). It fails closed — never green — when the
deep data cannot support an honest comparison.

⚠️ Framework isolation: research/orchestration only — no torch/tensorflow/jax.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping
from pathlib import Path

import pandas as pd

from quantlab.research.oos_artifact import artifact_checksum
from quantlab.research.real_data_oos import (
    SamplingFrequencyError,
    assess_data_sufficiency,
    classify_cadence,
    is_oversampled,
    rebalance_cadence_days,
)

_CLAIM = "no_alpha_claim"
_AUTHORITY = "out_of_sample_net_only"
_ARTIFACT_KIND = "multi_cycle_family_oos_artifact"
_STATUSES = {"computed", "insufficient_data"}
_DEGENERATE_VOL_EPS = 1e-6
# Multi-cycle default: ~20y forces a window spanning multiple stress episodes.
_DEFAULT_MIN_HISTORY_MONTHS = 240.0

# Canonical market-stress episodes (descriptive provenance only — no engine logic
# depends on these dates; they only label which cycles a window actually spanned).
CANONICAL_CYCLES: tuple[tuple[str, str], ...] = (
    ("dot_com", "2000-03-10"),
    ("gfc", "2008-09-15"),
    ("covid", "2020-03-23"),
    ("rate_shock_2022", "2022-06-16"),
)

StrategyFactory = Callable[[tuple[str, ...]], Any]


def cycles_in_window(start: Any, end: Any) -> tuple[dict[str, str], ...]:
    """Canonical stress episodes whose date falls within ``[start, end]``.

    Deterministic function of the window only; returns a subset of
    ``CANONICAL_CYCLES`` ordered by date.
    """
    if start is None or end is None:
        return ()
    lo, hi = pd.Timestamp(start), pd.Timestamp(end)
    if lo > hi:
        lo, hi = hi, lo
    return tuple(
        {"name": name, "date": date}
        for name, date in CANONICAL_CYCLES
        if lo <= pd.Timestamp(date) <= hi
    )


def _oos_metric(result: Mapping[str, Any]) -> Mapping[str, Any]:
    for metric in result.get("metrics", []):
        if metric.get("segment") == "out_of_sample" and metric.get("basis") == "net":
            return metric
    raise ValueError("multi-cycle OOS comparison requires an out_of_sample net Sharpe")


def _claim_of(result: Mapping[str, Any]) -> str | None:
    metadata = result.get("strategy_metadata") or {}
    claim = metadata.get("claim_boundary")
    return None if claim is None else str(claim)


def _assert_no_overclaim(result: Mapping[str, Any]) -> None:
    """Reject an *explicit* non-no_alpha_claim record.

    A claim-silent dumb baseline (e.g. ``BuyAndHold``, which omits the key) is
    accepted — it makes no alpha claim. Only a record that explicitly declares a
    boundary other than ``no_alpha_claim`` is an overclaim and fails closed.
    """
    claim = _claim_of(result)
    if claim is not None and claim != _CLAIM:
        raise ValueError(
            f"multi-cycle OOS comparison rejects overclaiming record "
            f"(strategy_metadata.claim_boundary={claim!r}, expected {_CLAIM!r})"
        )


def _run(strategy: Any, provider: Any, run_cfg: Mapping[str, Any], store: Any | None,
         *, model_family: str, is_baseline: bool) -> dict[str, Any]:
    from quantlab.engine import VectorizedEngine

    result = VectorizedEngine().run(strategy, provider, dict(run_cfg))
    result["is_baseline"] = is_baseline
    result["model_family"] = model_family
    if store is not None:
        store.log(result)
    return result


def build_multi_cycle_family_oos_report(
    provider: Any, *,
    families: Mapping[str, StrategyFactory],
    baseline_build: StrategyFactory,
    config: Mapping[str, Any],
    min_assets: int = 2,
    min_history_months: float = _DEFAULT_MIN_HISTORY_MONTHS,
    store: Any | None = None,
    availability_mode: str = "approximate_event_date",
) -> dict[str, Any]:
    """Run baseline + every family over ONE shared co-temporal universe/window.

    Fails closed (raises) on: insufficient co-temporal data, oversampling vs
    native cadence (``SamplingFrequencyError``), degenerate flat OOS, or an
    explicit overclaiming record. Ranks OOS-net only; baseline always visible.
    """
    if not families:
        raise ValueError("multi-cycle OOS comparison requires at least one model family")
    if config.get("mode", "net") != "net":
        raise ValueError("multi-cycle OOS comparison requires mode=net for OOS-net authority")

    suff = assess_data_sufficiency(provider, min_assets=min_assets,
                                   min_history_months=min_history_months)
    if not suff.sufficient:
        raise ValueError(f"insufficient real data for multi-cycle OOS comparison: {suff.reason}")

    # CR-RDO-004 (reused): refuse to rebalance finer than the coarsest selected
    # asset's native cadence — that fabricates flat returns and inflates Sharpe.
    rebalance = str(config.get("rebalance", "monthly"))
    rebalance_days = rebalance_cadence_days(rebalance)
    if is_oversampled(suff.coarsest_cadence_days, rebalance_days):
        raise SamplingFrequencyError(
            "oversampled multi-cycle OOS comparison: rebalance cadence "
            f"({rebalance}, ~{rebalance_days:.1f}d) is finer than the coarsest "
            f"selected asset native cadence (~{suff.coarsest_cadence_days:.1f}d)."
        )

    # Resolve the shared universe/window ONCE so every family is comparable.
    universe = tuple(suff.cotemporal_universe)
    start: str | None
    end: str | None
    if config.get("start") and config.get("end"):
        start, end = str(config["start"]), str(config["end"])
    else:
        # sufficiency passing guarantees a resolved co-temporal overlap window.
        start, end = suff.overlap_start, suff.overlap_end
    run_cfg = {**config, "start": start, "end": end, "mode": "net"}

    runs: list[tuple[str, dict[str, Any]]] = []
    baseline_result = _run(baseline_build(universe), provider, run_cfg, store,
                           model_family="baseline", is_baseline=True)
    runs.append(("baseline", baseline_result))
    for family_name, build in families.items():
        runs.append((family_name, _run(build(universe), provider, run_cfg, store,
                                        model_family=family_name, is_baseline=False)))

    rows: list[dict[str, Any]] = []
    family_status: dict[str, Any] = {}
    max_oos_vol = 0.0
    for family_name, result in runs:
        _assert_no_overclaim(result)
        oos = _oos_metric(result)
        max_oos_vol = max(max_oos_vol, float(oos.get("annualized_vol", 0.0)))
        rows.append({
            "model_family": family_name,
            "strategy_name": str(result.get("strategy_name") or ""),
            "oos_net_sharpe": float(oos["sharpe"]),
            "is_baseline": bool(result.get("is_baseline")),
            "run_id": str(result.get("run_id") or ""),
        })
        family_status[family_name] = dict(result.get("strategy_metadata") or {})

    if max_oos_vol < _DEGENERATE_VOL_EPS:
        raise ValueError(
            "degenerate multi-cycle OOS comparison: flat out-of-sample returns "
            f"(max OOS vol {max_oos_vol:.2e}). Load with approximate_availability "
            "or accumulate true-vintage data before claiming a computed comparison."
        )

    rows.sort(key=lambda r: r["oos_net_sharpe"], reverse=True)
    return {
        "status": "computed",
        "claim_boundary": _CLAIM,
        "metric_authority": _AUTHORITY,
        "rows": rows,
        "families": sorted({r["model_family"] for r in rows}),
        "baseline_run_ids": [r["run_id"] for r in rows if r["is_baseline"]],
        "asset_set": list(universe),
        "asof_window": {"start": start, "end": end},
        "availability_mode": availability_mode,
        "cost_config": dict(config.get("cost_config") or {}),
        "data_provenance": {
            "availability_mode": availability_mode,
            "universe": list(universe),
            "asset_count": suff.asset_count,
            "history_span_months": suff.history_span_months,
            "overlap_start": suff.overlap_start,
            "overlap_end": suff.overlap_end,
            "overlap_months": suff.overlap_months,
            "sampling_frequency": {
                "by_symbol": dict(suff.sampling_frequencies),
                "coarsest_cadence": classify_cadence(suff.coarsest_cadence_days),
                "coarsest_native_days": round(suff.coarsest_cadence_days, 4),
                "rebalance": rebalance,
                "rebalance_days": round(rebalance_days, 4),
                "homogeneous": suff.frequency_homogeneous,
            },
            "cycles_covered": list(cycles_in_window(start, end)),
            "family_status": family_status,
        },
    }


def build_multi_cycle_insufficient_report(
    suff: Any, *, config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = config or {}
    window = None
    if suff.history_start and suff.history_end:
        window = {"start": suff.history_start, "end": suff.history_end}
    return {
        "status": "insufficient_data",
        "claim_boundary": _CLAIM,
        "metric_authority": _AUTHORITY,
        "rows": [],
        "families": [],
        "baseline_run_ids": [],
        "asset_set": list(suff.price_assets),
        "asof_window": window,
        "availability_mode": str(cfg.get("availability_mode") or "approximate_event_date"),
        "cost_config": dict(cfg.get("cost_config") or {}),
        "reason": suff.reason,
        "data_provenance": {
            "asset_count": suff.asset_count,
            "history_span_months": suff.history_span_months,
            "min_assets": suff.min_assets,
            "min_history_months": suff.min_history_months,
        },
    }


def build_multi_cycle_artifact(
    report: Mapping[str, Any], *, artifact_uri: str, generated_at: str,
) -> dict[str, Any]:
    status = report.get("status")
    if status not in _STATUSES:
        raise ValueError(f"unknown multi-cycle OOS report status: {status!r}")
    if report.get("claim_boundary") != _CLAIM:
        raise ValueError("multi-cycle OOS artifact must preserve no_alpha_claim")
    if report.get("metric_authority") != _AUTHORITY:
        raise ValueError("multi-cycle OOS artifact requires out_of_sample_net_only authority")
    rows = report.get("rows")
    if not isinstance(rows, list):
        raise ValueError("multi-cycle OOS artifact requires a rows list")
    if status == "computed":
        if not rows:
            raise ValueError("computed multi-cycle OOS artifact requires rows")
        if not any(bool(r.get("is_baseline")) for r in rows):
            raise ValueError("computed multi-cycle OOS artifact requires a visible baseline row")
    elif rows:
        raise ValueError("insufficient_data report must not carry comparison rows")

    clean_uri, clean_at = artifact_uri.strip(), generated_at.strip()
    if not clean_uri or not clean_at:
        raise ValueError("multi-cycle OOS artifact requires artifact_uri and generated_at")

    checksum = artifact_checksum(clean_uri, clean_at, dict(report))
    return {
        "artifact_kind": _ARTIFACT_KIND,
        "status": status,
        "claim_boundary": _CLAIM,
        "metric_authority": _AUTHORITY,
        "artifact_uri": clean_uri,
        "generated_at": clean_at,
        "row_count": len(rows),
        "report": dict(report),
        "checksum": checksum,
    }


def validate_multi_cycle_artifact(artifact: Mapping[str, Any]) -> None:
    if artifact.get("artifact_kind") != _ARTIFACT_KIND:
        raise ValueError("unknown multi-cycle family OOS artifact")
    if artifact.get("status") not in _STATUSES:
        raise ValueError("multi-cycle OOS artifact has unknown status")
    if artifact.get("claim_boundary") != _CLAIM:
        raise ValueError("multi-cycle OOS artifact must preserve no_alpha_claim")
    if artifact.get("metric_authority") != _AUTHORITY:
        raise ValueError("multi-cycle OOS artifact requires out_of_sample_net_only authority")
    report = artifact.get("report")
    if not isinstance(report, Mapping):
        raise ValueError("multi-cycle OOS artifact requires report")
    rows = report.get("rows")
    if not isinstance(rows, list):
        raise ValueError("multi-cycle OOS artifact requires rows list")
    if artifact.get("row_count") != len(rows):
        raise ValueError("multi-cycle OOS artifact row_count mismatch")
    if artifact.get("status") == "computed" and not any(bool(r.get("is_baseline")) for r in rows):
        raise ValueError("computed multi-cycle OOS artifact requires a visible baseline row")
    expected = artifact_checksum(artifact.get("artifact_uri"), artifact.get("generated_at"), report)
    if artifact.get("checksum") != expected:
        raise ValueError("multi-cycle OOS artifact checksum mismatch")


def write_multi_cycle_artifact(artifact: Mapping[str, Any], path: str | Path) -> Path:
    import json

    validate_multi_cycle_artifact(artifact)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(dict(artifact), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


__all__ = [
    "CANONICAL_CYCLES",
    "cycles_in_window",
    "build_multi_cycle_family_oos_report",
    "build_multi_cycle_insufficient_report",
    "build_multi_cycle_artifact",
    "validate_multi_cycle_artifact",
    "write_multi_cycle_artifact",
]
