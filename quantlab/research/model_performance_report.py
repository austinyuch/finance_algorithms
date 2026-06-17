"""Deterministic statistical performance report for deep-model research (REQ-H-STATREPORT-001).

Pure function over per-strategy **net return series**: ranks on out-of-sample net Sharpe
only, keeps the baseline visible, and reports distribution statistics, a rolling-Sharpe
series, a drawdown series, an equity curve, and (for the deep model) the learning curve.
Every report carries `no_alpha_claim` and a deterministic checksum. Degenerate/empty input
fails closed rather than emitting non-finite statistics.

This is a research layer (numpy/pandas allowed); it is not the backtest core and imports
no ML framework. The return series it consumes are realized PIT-forward paths (weights
always decided strictly before the realized period), so the path is out-of-sample by
construction — `no_alpha_claim`, mechanism evidence, not a strategy verdict.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

import numpy as np

_ROUND = 10
_METRIC_AUTHORITY = "out_of_sample_net_only"
_CLAIM = "no_alpha_claim"


def _r(value: float) -> float:
    return round(float(value), _ROUND)


def _validate(series: np.ndarray, name: str) -> None:
    if series.size < 2:
        raise ValueError(f"performance report needs >=2 net returns for {name!r}")
    if not np.all(np.isfinite(series)):
        raise ValueError(f"non-finite net returns for {name!r}")
    if float(series.std(ddof=0)) <= 1e-12:
        raise ValueError(f"degenerate (flat) net return series for {name!r}; cannot report")


def _distribution_stats(series: np.ndarray) -> dict[str, float]:
    mean = float(series.mean())
    std = float(series.std(ddof=0))
    z = (series - mean) / std
    return {
        "mean": _r(mean),
        "volatility": _r(std),
        "skew": _r(float(np.mean(z ** 3))),
        "excess_kurtosis": _r(float(np.mean(z ** 4) - 3.0)),
        "var_5pct": _r(float(-np.percentile(series, 5))),
    }


def _rolling_sharpe(series: np.ndarray, window: int, ppy: int) -> list[float]:
    window = max(2, min(window, series.size))
    scale = float(np.sqrt(ppy))
    out: list[float] = []
    for end in range(window, series.size + 1):
        chunk = series[end - window:end]
        std = float(chunk.std(ddof=0))
        out.append(_r((float(chunk.mean()) / std) * scale if std > 1e-12 else 0.0))
    return out


def _drawdown_series(series: np.ndarray) -> tuple[list[float], list[float]]:
    equity = np.cumprod(1.0 + series)
    peak = np.maximum.accumulate(equity)
    drawdown = equity / peak - 1.0
    return [_r(v) for v in equity.tolist()], [_r(v) for v in drawdown.tolist()]


def _oos_net_sharpe(series: np.ndarray, ppy: int) -> float:
    std = float(series.std(ddof=0))
    return _r((float(series.mean()) / std) * float(np.sqrt(ppy)) if std > 1e-12 else 0.0)


def _checksum(report: Mapping[str, Any]) -> str:
    payload = {k: v for k, v in report.items() if k != "checksum"}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_deep_model_performance_report(
    return_series: Mapping[str, Sequence[float]],
    *,
    learning_curve: Sequence[float],
    model_name: str,
    baseline_name: str,
    periods_per_year: int = 12,
    rolling_window: int = 12,
) -> dict[str, Any]:
    """Build the deterministic, checksummed statistical performance report."""
    if model_name not in return_series or baseline_name not in return_series:
        raise ValueError("return_series must contain both the model and the baseline")

    rows: list[dict[str, Any]] = []
    for name, raw in return_series.items():
        series = np.asarray(list(raw), dtype="float64")
        _validate(series, name)
        equity, drawdown = _drawdown_series(series)
        row: dict[str, Any] = {
            "strategy_name": name,
            "is_baseline": name == baseline_name,
            "oos_net_sharpe": _oos_net_sharpe(series, periods_per_year),
            "distribution": _distribution_stats(series),
            "rolling_sharpe": _rolling_sharpe(series, rolling_window, periods_per_year),
            "drawdown": drawdown,
            "equity_curve": equity,
            "observations": int(series.size),
        }
        if name == model_name:
            row["learning_curve"] = [_r(v) for v in learning_curve]
        rows.append(row)

    rows.sort(key=lambda r: r["oos_net_sharpe"], reverse=True)

    report: dict[str, Any] = {
        "claim_boundary": _CLAIM,
        "metric_authority": _METRIC_AUTHORITY,
        "model_name": model_name,
        "baseline_name": baseline_name,
        "periods_per_year": int(periods_per_year),
        "rolling_window": int(rolling_window),
        "rows": rows,
    }
    report["checksum"] = _checksum(report)
    return report
