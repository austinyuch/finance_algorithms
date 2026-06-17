"""Self-contained SVG/HTML visualization for the deep-model performance report (REQ-H-VIZ-001).

Renders a single inline SVG (and an HTML wrapper) with NO external/CDN reference and no
client-side data fetch, so it renders under headless validation and `file://`. Pure and
deterministic for equal report input.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

_W = 920
_PANEL_H = 170
_PAD = 48
_COLORS = ["#2563eb", "#d97706", "#059669", "#9333ea"]


def _poly(series: Sequence[float], x0: int, y0: int, w: int, h: int) -> str:
    values = list(series)
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    n = len(values)
    step = w / (n - 1) if n > 1 else w
    pts = []
    for i, v in enumerate(values):
        x = x0 + (i * step if n > 1 else 0)
        y = y0 + h - ((v - lo) / span) * h
        pts.append(f"{x:.2f},{y:.2f}")
    return " ".join(pts)


def _panel_label(text: str, x: int, y: int) -> str:
    return (f'<text x="{x}" y="{y}" font-family="sans-serif" font-size="13" '
            f'font-weight="600" fill="#111827">{text}</text>')


def _returns_from_equity(equity: Sequence[float]) -> list[float]:
    out: list[float] = []
    prev = 1.0
    for value in equity:
        out.append(value / prev - 1.0)
        prev = value
    return out


def _histogram(returns: Sequence[float], x0: int, y0: int, w: int, h: int, bins: int = 16) -> str:
    if not returns:
        return ""
    lo, hi = min(returns), max(returns)
    span = (hi - lo) or 1.0
    counts = [0] * bins
    for r in returns:
        idx = min(bins - 1, int((r - lo) / span * bins))
        counts[idx] += 1
    peak = max(counts) or 1
    bar_w = w / bins
    rects = []
    for i, c in enumerate(counts):
        bar_h = (c / peak) * h
        x = x0 + i * bar_w
        y = y0 + h - bar_h
        rects.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w - 1:.2f}" '
                     f'height="{bar_h:.2f}" fill="#2563eb" opacity="0.75" />')
    return "".join(rects)


def render_performance_report_svg(report: Mapping[str, Any]) -> str:
    rows = report["rows"]
    model_name = report["model_name"]
    model = next((r for r in rows if r["strategy_name"] == model_name), rows[0])
    inner_w = _W - 2 * _PAD
    panels: list[str] = []

    # Panel 1 — equity curves (all strategies)
    y = _PAD
    panels.append(_panel_label("Equity curve (relative performance, no_alpha_claim)", _PAD, y - 14))
    for idx, row in enumerate(rows):
        color = _COLORS[idx % len(_COLORS)]
        pts = _poly(row["equity_curve"], _PAD, y, inner_w, _PANEL_H)
        if pts:
            panels.append(f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{pts}" />')
        panels.append(f'<text x="{_PAD + 6}" y="{y + 16 + idx * 16}" font-family="sans-serif" '
                      f'font-size="11" fill="{color}">{row["strategy_name"]} '
                      f'(OOS-net Sharpe {row["oos_net_sharpe"]:.3f})</text>')

    # Panel 2 — drawdown (model)
    y = _PAD + _PANEL_H + _PAD
    panels.append(_panel_label(f"Drawdown — {model_name}", _PAD, y - 14))
    pts = _poly(model["drawdown"], _PAD, y, inner_w, _PANEL_H)
    if pts:
        panels.append(f'<polyline fill="none" stroke="#dc2626" stroke-width="2" points="{pts}" />')

    # Panel 3 — learning curve (model)
    y = _PAD + 2 * (_PANEL_H + _PAD)
    panels.append(_panel_label(f"Learning curve (training loss) — {model_name}", _PAD, y - 14))
    pts = _poly(model.get("learning_curve", []), _PAD, y, inner_w, _PANEL_H)
    if pts:
        panels.append(f'<polyline fill="none" stroke="#059669" stroke-width="2" points="{pts}" />')

    # Panel 4 — return distribution (model)
    y = _PAD + 3 * (_PANEL_H + _PAD)
    panels.append(_panel_label(f"Return distribution — {model_name}", _PAD, y - 14))
    panels.append(_histogram(_returns_from_equity(model["equity_curve"]), _PAD, y, inner_w, _PANEL_H))

    height = _PAD + 4 * (_PANEL_H + _PAD)
    body = "".join(panels)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_W}" height="{height}" '
        f'viewBox="0 0 {_W} {height}" role="img" '
        f'aria-label="Deep model performance report: equity curve, drawdown, learning curve, '
        f'return distribution (no_alpha_claim)">'
        f'<rect width="{_W}" height="{height}" fill="#ffffff" />'
        f"{body}</svg>"
    )


def render_performance_report_html(report: Mapping[str, Any]) -> str:
    svg = render_performance_report_svg(report)
    rows = report["rows"]
    items = "".join(
        f'<li>{r["strategy_name"]}{" (baseline)" if r["is_baseline"] else ""}: '
        f'OOS-net Sharpe {r["oos_net_sharpe"]:.3f}, '
        f'vol {r["distribution"]["volatility"]:.4f}, '
        f'5% VaR {r["distribution"]["var_5pct"]:.4f}</li>'
        for r in rows
    )
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\" />"
        "<title>Deep Model Performance Report</title></head><body>"
        "<h1>Deep Model Performance Report</h1>"
        f"<p>Claim boundary: <strong>{report['claim_boundary']}</strong>; "
        f"metric authority: {report['metric_authority']}. "
        "Ranked on out-of-sample net Sharpe only; baseline kept visible.</p>"
        f"<ul>{items}</ul>"
        f"<figure>{svg}<figcaption>Equity curve, drawdown, learning curve and return "
        "distribution for the deep model versus the dumb baseline.</figcaption></figure>"
        "</body></html>"
    )
