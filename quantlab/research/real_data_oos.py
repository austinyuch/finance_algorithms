"""Real-data >=2-asset OOS-net backtest slice (spec: real-data-oos-backtest).

Runs the existing A0 ``VectorizedEngine`` over real point-in-time vintage data
for a candidate strategy and a dumb baseline, and emits a checksumed OOS-net
comparison artifact. No engine / loader / cost / metric semantics change here:
this module is composition + honest gating only.

Honesty boundary: this proves *mechanism* on real-source-format data. It never
claims alpha; every artifact carries ``claim_boundary="no_alpha_claim"``. When
fewer than ``min_assets`` price assets exist, or accumulated history is below the
walk-forward window, it fails closed to ``status="insufficient_data"`` instead of
emitting a comparison that could read as validated.

This is research/orchestration, not backtest core: it may use pandas and import
``quantlab.runner`` / ``quantlab.data`` / ``quantlab.strategies``; it must not
import any ML framework (kept green by import-linter, which only forbids that in
``quantlab.engine`` / ``quantlab.data``).
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any, Mapping

_CLAIM = "no_alpha_claim"
_AUTHORITY = "out_of_sample_net_only"
_ARTIFACT_KIND = "real_data_oos_backtest_artifact"
_STATUSES = {"computed", "insufficient_data"}
# Default min history = train(12) + test(6) of the default walk-forward window.
_DEFAULT_MIN_HISTORY_MONTHS = 18.0

# CR-RDO-004: oversampling tolerance — fail closed only when the rebalance cadence
# is more than (1 + tol)x finer than the coarsest selected asset's native cadence.
_OVERSAMPLE_TOL = 0.5
_REBALANCE_DAYS = {"daily": 1.0, "weekly": 7.0, "monthly": 30.4375, "quarterly": 91.3125}


class SamplingFrequencyError(ValueError):
    """Raised when the rebalance cadence is finer than an asset's native cadence.

    Rebalancing/sampling more often than an asset actually updates forward-fills
    stale prices into fabricated flat-return periods, which understates volatility
    and inflates the OOS-net Sharpe — a dishonest comparison. CR-RDO-004 fails
    closed instead of emitting a misleading ``computed`` result.
    """


@dataclass(frozen=True)
class SamplingFrequency:
    symbol: str
    median_spacing_days: float
    cadence: str  # "daily" | "weekly" | "monthly" | "quarterly" | "irregular"


def classify_cadence(days: float) -> str:
    """Canonical cadence label from a median inter-observation spacing in days."""
    if days <= 0:
        return "irregular"
    if days <= 4:
        return "daily"
    if days <= 10:
        return "weekly"
    if days <= 45:
        return "monthly"
    if days <= 135:
        return "quarterly"
    return "irregular"


def rebalance_cadence_days(rebalance: str) -> float:
    """Approximate days between rebalances; unknown labels fall back to monthly."""
    return _REBALANCE_DAYS.get(str(rebalance), 30.4375)


def is_oversampled(coarsest_native_days: float, rebalance_days: float,
                   *, tol: float = _OVERSAMPLE_TOL) -> bool:
    """True when the rebalance cadence is meaningfully finer than the coarsest asset."""
    return coarsest_native_days > rebalance_days * (1.0 + tol)


def _median_spacing_days(events: Any) -> float:
    uniq = sorted({d for d in events})
    if len(uniq) < 2:
        return 0.0
    diffs = [(uniq[i + 1] - uniq[i]).days for i in range(len(uniq) - 1)]
    return float(statistics.median(diffs))


def estimate_sampling_frequencies(provider: Any) -> dict[str, SamplingFrequency]:
    """Per-asset native sampling frequency from the PIT price panel's event_dates."""
    prices = provider.price_panel()
    out: dict[str, SamplingFrequency] = {}
    if not len(prices):
        return out
    for sym, grp in prices.groupby("symbol"):
        days = _median_spacing_days(grp["event_date"])
        out[str(sym)] = SamplingFrequency(str(sym), days, classify_cadence(days))
    return out


@dataclass(frozen=True)
class DataSufficiency:
    price_assets: tuple[str, ...]
    asset_count: int
    history_start: str | None
    history_end: str | None
    history_span_months: float
    min_assets: int
    min_history_months: float
    sufficient: bool
    # "ok" | "fewer_than_min_assets" | "history_below_min_window" | "no_cotemporal_overlap"
    reason: str
    # CR-RDO-001: the co-temporal subset that actually shares the walk-forward window.
    cotemporal_universe: tuple[str, ...] = ()
    overlap_start: str | None = None
    overlap_end: str | None = None
    overlap_months: float = 0.0
    # CR-RDO-004: native sampling cadence of the traded (co-temporal) universe.
    sampling_frequencies: tuple[tuple[str, str], ...] = ()
    coarsest_cadence_days: float = 0.0
    frequency_homogeneous: bool = True


def _asset_spans(provider: Any) -> dict[str, tuple[Any, Any]]:
    """Per-asset (earliest, latest) event_date over rows with *usable* closes.

    A row whose ``close`` is non-finite (NaN/±inf) or non-positive is invalid
    market data, not a tradable price — the same boundary the A0 engine enforces
    in ``VectorizedEngine._close`` (CR-A0-CHAOS-001). Spans (and therefore the
    co-temporal universe) are computed from usable rows only, so an asset with no
    usable closes contributes no span and drops out of the universe: a
    NaN/garbage-poisoned asset fails sufficiency *closed* instead of silently
    entering the comparison at a fabricated weight while the engine drops its legs.
    """
    # usable (finite, positive) closes only — the provider applies the same boundary as
    # VectorizedEngine._close (CR-A0-CHAOS-001), so a NaN/garbage-poisoned asset has no
    # span and drops out of the co-temporal universe (fails sufficiency closed).
    usable = provider.price_panel(usable_only=True)
    spans: dict[str, tuple[Any, Any]] = {}
    if not len(usable):
        return spans
    for sym, grp in usable.groupby("symbol"):
        events = grp["event_date"]
        spans[str(sym)] = (events.min(), events.max())
    return spans


def _overlap_months(spans: Mapping[str, tuple[Any, Any]]) -> tuple[Any, Any, float]:
    """Shared window of a set of assets: [max(start), min(end)] in months (negative if disjoint)."""
    start = max(v[0] for v in spans.values())
    end = min(v[1] for v in spans.values())
    months = ((end - start).days / 30.4375) if end >= start else -1.0
    return start, end, months


def resolve_cotemporal_universe(
    provider: Any, *, min_history_months: float = _DEFAULT_MIN_HISTORY_MONTHS, min_assets: int = 2,
) -> tuple[tuple[str, ...], str | None, str | None]:
    """Largest >=min_assets subset that shares a window >= min_history_months.

    Exact: enumerates subsets from largest size down and returns the first size
    that has a qualifying subset, breaking ties by longest shared window then
    lexicographically. Greedy single-drop is unsafe when several assets share the
    binding constraint (e.g. two short-history symbols both pinning the window),
    so for the small asset counts in this lab we enumerate. Returns
    ``((), None, None)`` when no qualifying co-temporal subset exists.
    """
    spans = _asset_spans(provider)
    syms = sorted(spans)
    if len(syms) < min_assets:
        return (), None, None
    if len(syms) <= 18:
        for size in range(len(syms), min_assets - 1, -1):
            qualifying = []
            for combo in combinations(syms, size):
                start, end, months = _overlap_months({k: spans[k] for k in combo})
                if months >= min_history_months:
                    qualifying.append((months, combo, start, end))
            if qualifying:
                qualifying.sort(key=lambda x: (x[0], x[1]))
                _, combo, start, end = qualifying[-1]
                return tuple(combo), str(start.date()), str(end.date())
        return (), None, None
    # Fallback (very large asset sets, not expected here): greedy single-drop.
    keep = dict(spans)
    while len(keep) > min_assets:
        start, end, months = _overlap_months(keep)
        if months >= min_history_months:
            return tuple(sorted(keep)), str(start.date()), str(end.date())
        late_start = max(keep, key=lambda k: (keep[k][0], k))
        early_end = min(keep, key=lambda k: (keep[k][1], k))
        gains = {v: _overlap_months({k: s for k, s in keep.items() if k != v})[2]
                 for v in {late_start, early_end}}
        del keep[max(gains, key=lambda k: (gains[k], k))]
    start, end, months = _overlap_months(keep)
    if months >= min_history_months:
        return tuple(sorted(keep)), str(start.date()), str(end.date())
    return (), None, None


def assess_data_sufficiency(
    provider: Any, *, min_assets: int = 2, min_history_months: float = _DEFAULT_MIN_HISTORY_MONTHS,
) -> DataSufficiency:
    """Decide whether real price data can support a walk-forward OOS comparison.

    CR-RDO-001 makes this overlap-aware: sufficiency requires >=``min_assets``
    that share a *common* event_date window >= ``min_history_months`` (a coarse
    calendar span over a non-co-temporal asset mix produced a degenerate
    comparison). Fails closed with an explicit reason otherwise.
    """
    spans = _asset_spans(provider)
    assets = tuple(sorted(spans))
    if assets:
        start, end = provider.event_span()
        span_months = round((end - start).days / 30.4375, 4)
        start_s, end_s = str(start.date()), str(end.date())
    else:
        span_months, start_s, end_s = 0.0, None, None

    universe, o_start, o_end = resolve_cotemporal_universe(
        provider, min_history_months=min_history_months, min_assets=min_assets)
    overlap_months = _overlap_months({k: spans[k] for k in universe})[2] if universe else 0.0

    # CR-RDO-004: cadence of the traded universe (fall back to all assets when no
    # co-temporal subset qualifies, so provenance stays informative either way).
    freqs = estimate_sampling_frequencies(provider)
    scope = universe if universe else assets
    scoped = {sym: freqs[sym] for sym in scope if sym in freqs}
    sampling_frequencies = tuple(sorted((sym, f.cadence) for sym, f in scoped.items()))
    coarsest_cadence_days = max((f.median_spacing_days for f in scoped.values()), default=0.0)
    frequency_homogeneous = len({f.cadence for f in scoped.values()}) <= 1

    if len(assets) < min_assets:
        sufficient, reason = False, "fewer_than_min_assets"
    elif universe:
        sufficient, reason = True, "ok"
    else:
        # No >=min_assets subset reaches the window. Distinguish a thin-but-
        # overlapping panel (history below window) from genuinely disjoint assets.
        full_overlap = _overlap_months(spans)[2] if len(assets) >= min_assets else -1.0
        sufficient = False
        reason = "history_below_min_window" if full_overlap >= 0.0 else "no_cotemporal_overlap"

    return DataSufficiency(
        price_assets=assets, asset_count=len(assets),
        history_start=start_s, history_end=end_s, history_span_months=span_months,
        min_assets=min_assets, min_history_months=float(min_history_months),
        sufficient=sufficient, reason=reason,
        cotemporal_universe=universe,
        overlap_start=o_start, overlap_end=o_end, overlap_months=round(overlap_months, 4),
        sampling_frequencies=sampling_frequencies,
        coarsest_cadence_days=round(coarsest_cadence_days, 4),
        frequency_homogeneous=frequency_homogeneous,
    )


_DEGENERATE_VOL_EPS = 1e-6


def _oos_metric(result: Mapping[str, Any]) -> Mapping[str, Any]:
    for metric in result.get("metrics", []):
        if metric.get("segment") == "out_of_sample" and metric.get("basis") == "net":
            return metric
    raise ValueError("real-data OOS comparison requires an out_of_sample net Sharpe")


def _oos_net_sharpe(result: Mapping[str, Any]) -> float:
    return float(_oos_metric(result)["sharpe"])


def _window(provider: Any, config: Mapping[str, Any]) -> tuple[str, str]:
    if config.get("start") and config.get("end"):
        return str(config["start"]), str(config["end"])
    start, end = provider.event_span()
    return str(start.date()), str(end.date())


def build_real_data_oos_report(
    provider: Any, *, candidate: Any, baseline: Any, config: Mapping[str, Any],
    min_assets: int = 2, min_history_months: float = _DEFAULT_MIN_HISTORY_MONTHS,
    store: Any | None = None, availability_mode: str = "true_pit",
) -> dict[str, Any]:
    """Run candidate + baseline over real PIT data; rank OOS-net only, baseline visible.

    Fails closed (raises) when the OOS comparison is *degenerate* — every
    strategy's out-of-sample net return series is flat (≈0 vol). That happens
    when single-capture vintage data (``available_date`` = capture date) is
    PIT-invisible to historical as-ofs, so the backtest sees no data and reports
    a misleading "computed" result. ``availability_mode`` records whether the
    provider used ``true_pit`` or explicit ``approximate_event_date`` availability.
    """
    suff = assess_data_sufficiency(provider, min_assets=min_assets,
                                   min_history_months=min_history_months)
    if not suff.sufficient:
        raise ValueError(f"insufficient real data for OOS comparison: {suff.reason}")

    if config.get("mode", "net") != "net":
        raise ValueError("real-data OOS comparison requires mode=net for OOS-net authority")

    # CR-RDO-004: refuse to rebalance/sample finer than the coarsest selected
    # asset's native cadence — that would forward-fill stale prices into fabricated
    # flat returns, understating vol and inflating the OOS-net Sharpe.
    rebalance = str(config.get("rebalance", "monthly"))
    rebalance_days = rebalance_cadence_days(rebalance)
    if is_oversampled(suff.coarsest_cadence_days, rebalance_days):
        raise SamplingFrequencyError(
            "oversampled real-data OOS comparison: rebalance cadence "
            f"({rebalance}, ~{rebalance_days:.1f}d) is finer than the coarsest "
            f"selected asset native cadence (~{suff.coarsest_cadence_days:.1f}d); "
            "the loader would forward-fill stale prices into fabricated flat "
            "returns. Harmonize to the coarsest cadence or drop the low-frequency "
            "asset before claiming a computed comparison."
        )

    # Run over the co-temporal overlap window so every selected asset has data.
    if config.get("start") and config.get("end"):
        start, end = str(config["start"]), str(config["end"])
    elif suff.overlap_start and suff.overlap_end:
        start, end = suff.overlap_start, suff.overlap_end
    else:
        start, end = _window(provider, config)
    run_cfg = {**config, "start": start, "end": end, "mode": "net"}

    rows: list[dict[str, Any]] = []
    max_oos_vol = 0.0
    for strategy, is_baseline in ((candidate, False), (baseline, True)):
        result = _run(strategy, provider, run_cfg, store, is_baseline)
        oos = _oos_metric(result)
        max_oos_vol = max(max_oos_vol, float(oos.get("annualized_vol", 0.0)))
        rows.append({
            "strategy_name": str(result.get("strategy_name") or ""),
            "oos_net_sharpe": float(oos["sharpe"]),
            "is_baseline": is_baseline,
            "run_id": str(result.get("run_id") or ""),
        })
    if max_oos_vol < _DEGENERATE_VOL_EPS:
        raise ValueError(
            "degenerate real-data OOS comparison: flat out-of-sample returns "
            f"(max OOS vol {max_oos_vol:.2e}). Single-capture vintage data is "
            "PIT-invisible to historical as-ofs; load with approximate_availability "
            "or accumulate true-vintage data before claiming a computed comparison."
        )
    rows.sort(key=lambda r: r["oos_net_sharpe"], reverse=True)

    universe_asof = list(provider.universe(end))
    return {
        "status": "computed",
        "claim_boundary": _CLAIM,
        "metric_authority": _AUTHORITY,
        "rows": rows,
        "asset_set": list(suff.cotemporal_universe),
        "asof_window": {"start": start, "end": end},
        "availability_mode": availability_mode,
        "cost_config": dict(config.get("cost_config") or {}),
        "data_provenance": {
            "availability_mode": availability_mode,
            "asset_count": suff.asset_count,
            "history_start": suff.history_start,
            "history_end": suff.history_end,
            "history_span_months": suff.history_span_months,
            "cotemporal_universe": list(suff.cotemporal_universe),
            "overlap_start": suff.overlap_start,
            "overlap_end": suff.overlap_end,
            "overlap_months": suff.overlap_months,
            "universe_asof": universe_asof,
            "sampling_frequency": {
                "by_symbol": dict(suff.sampling_frequencies),
                "coarsest_cadence": classify_cadence(suff.coarsest_cadence_days),
                "coarsest_native_days": round(suff.coarsest_cadence_days, 4),
                "rebalance": rebalance,
                "rebalance_days": round(rebalance_days, 4),
                "homogeneous": suff.frequency_homogeneous,
            },
        },
    }


def _run(strategy: Any, provider: Any, run_cfg: Mapping[str, Any], store: Any | None,
         is_baseline: bool) -> dict[str, Any]:
    from quantlab.engine import VectorizedEngine

    result = VectorizedEngine().run(strategy, provider, dict(run_cfg))
    result["is_baseline"] = is_baseline
    if store is not None:
        # Mark the record before logging so the store records is_baseline and
        # validates the finite OOS-net Sharpe.
        store.log(result)
    return result


def build_insufficient_data_report(
    suff: DataSufficiency, *, config: Mapping[str, Any] | None = None,
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
        "asset_set": list(suff.price_assets),
        "asof_window": window,
        "cost_config": dict(cfg.get("cost_config") or {}),
        "reason": suff.reason,
        "data_provenance": {
            "asset_count": suff.asset_count,
            "history_start": suff.history_start,
            "history_end": suff.history_end,
            "history_span_months": suff.history_span_months,
            "min_assets": suff.min_assets,
            "min_history_months": suff.min_history_months,
        },
    }


def _canonical_json(value: Mapping[str, Any]) -> str:
    # CR-RDO-005 refactor: delegate to the shared helper (byte-identical output)
    # so the single-window and multi-cycle artifacts share one checksum definition.
    from quantlab.research.oos_artifact import canonical_json

    return canonical_json(value)


def build_real_data_oos_artifact(
    report: Mapping[str, Any], *, artifact_uri: str, generated_at: str,
) -> dict[str, Any]:
    status = report.get("status")
    if status not in _STATUSES:
        raise ValueError(f"unknown real-data OOS report status: {status!r}")
    if report.get("claim_boundary") != _CLAIM:
        raise ValueError("real-data OOS artifact must preserve no_alpha_claim")
    if report.get("metric_authority") != _AUTHORITY:
        raise ValueError("real-data OOS artifact requires out_of_sample_net_only authority")
    rows = report.get("rows")
    if not isinstance(rows, list):
        raise ValueError("real-data OOS artifact requires a rows list")
    if status == "computed":
        if not rows:
            raise ValueError("computed real-data OOS artifact requires rows")
        if not any(bool(r.get("is_baseline")) for r in rows):
            raise ValueError("computed real-data OOS artifact requires a visible baseline row")
    elif rows:
        raise ValueError("insufficient_data report must not carry comparison rows")

    clean_uri, clean_at = artifact_uri.strip(), generated_at.strip()
    if not clean_uri or not clean_at:
        raise ValueError("real-data OOS artifact requires artifact_uri and generated_at")

    payload = {"artifact_uri": clean_uri, "generated_at": clean_at, "report": dict(report)}
    checksum = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
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


def validate_real_data_oos_artifact(artifact: Mapping[str, Any]) -> None:
    if artifact.get("artifact_kind") != _ARTIFACT_KIND:
        raise ValueError("unknown real-data OOS backtest artifact")
    if artifact.get("status") not in _STATUSES:
        raise ValueError("real-data OOS artifact has unknown status")
    if artifact.get("claim_boundary") != _CLAIM:
        raise ValueError("real-data OOS artifact must preserve no_alpha_claim")
    if artifact.get("metric_authority") != _AUTHORITY:
        raise ValueError("real-data OOS artifact requires out_of_sample_net_only authority")
    report = artifact.get("report")
    if not isinstance(report, Mapping):
        raise ValueError("real-data OOS artifact requires report")
    rows = report.get("rows")
    if not isinstance(rows, list):
        raise ValueError("real-data OOS artifact requires rows list")
    if artifact.get("row_count") != len(rows):
        raise ValueError("real-data OOS artifact row_count mismatch")
    if artifact.get("status") == "computed" and not any(bool(r.get("is_baseline")) for r in rows):
        raise ValueError("computed real-data OOS artifact requires a visible baseline row")
    payload = {
        "artifact_uri": artifact.get("artifact_uri"),
        "generated_at": artifact.get("generated_at"),
        "report": report,
    }
    expected = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    if artifact.get("checksum") != expected:
        raise ValueError("real-data OOS artifact checksum mismatch")


def write_real_data_oos_artifact(artifact: Mapping[str, Any], path: str | Path) -> Path:
    validate_real_data_oos_artifact(artifact)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(dict(artifact), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


__all__ = [
    "DataSufficiency",
    "SamplingFrequency",
    "SamplingFrequencyError",
    "assess_data_sufficiency",
    "classify_cadence",
    "estimate_sampling_frequencies",
    "is_oversampled",
    "rebalance_cadence_days",
    "resolve_cotemporal_universe",
    "build_real_data_oos_report",
    "build_insufficient_data_report",
    "build_real_data_oos_artifact",
    "validate_real_data_oos_artifact",
    "write_real_data_oos_artifact",
]
