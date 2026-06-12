"""Deterministic HTML smoke renderer for the first F showcase slice."""
from __future__ import annotations

from html import escape
from typing import Any, Mapping


def _required_claim_boundary(row: Mapping[str, Any]) -> str:
    claim = row.get("claim_boundary")
    if claim != "no_alpha_claim":
        raise ValueError("dashboard rows must explicitly preserve claim_boundary=no_alpha_claim")
    return str(claim)


def _items(values: Mapping[str, Any]) -> str:
    return "".join(
        f"<li><span>{escape(str(k))}</span>: <strong>{escape(str(v))}</strong></li>"
        for k, v in sorted(values.items())
    )


def render_dashboard_html(summary: Mapping[str, Any]) -> str:
    leaderboard = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('strategy_name', '')))}</td>"
        f"<td>{escape(str(row.get('run_id', '')))}</td>"
        f"<td>{escape(str(row.get('oos_net_sharpe', '')))}</td>"
        f"<td>{escape(_required_claim_boundary(row))}</td>"
        "</tr>"
        for row in summary.get("leaderboard", [])
    )
    warnings = "".join(
        f"<li>{escape(str(warning))}</li>" for warning in summary.get("warnings", [])
    )
    experiments = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('model_family', '')))}</td>"
        f"<td>{escape(str(row.get('strategy_name', '')))}</td>"
        f"<td>{escape(str(row.get('readiness', 'registry_only')))}</td>"
        f"<td>{escape(_required_claim_boundary(row))}</td>"
        "</tr>"
        for row in summary.get("experiments", [])
    )
    summary_claim = _required_claim_boundary({"claim_boundary": summary.get("claim_boundary")})
    return (
        "<main>"
        "<section id=\"leaderboard\"><h2>Leaderboard</h2>"
        "<table><thead><tr><th>Strategy</th><th>Run</th><th>OOS Net Sharpe</th>"
        "<th>Claim</th></tr></thead>"
        f"<tbody>{leaderboard}</tbody></table></section>"
        "<section id=\"allocation-regime\"><h2>Allocation / Regime</h2>"
        f"<p>Regime: {escape(str(summary.get('regime', {}).get('label', 'unknown')))}</p>"
        f"<ul>{_items(summary.get('allocation', {}))}</ul></section>"
        "<section id=\"rebalance\"><h2>Rebalance</h2>"
        f"<p>{escape(', '.join(str(d) for d in summary.get('rebalance_dates', [])))}</p></section>"
        "<section id=\"experiments\"><h2>Experiment Registry</h2>"
        "<table><thead><tr><th>Family</th><th>Strategy</th><th>Readiness</th>"
        "<th>Claim</th></tr></thead>"
        f"<tbody>{experiments}</tbody></table></section>"
        "<section id=\"evidence\"><h2>Evidence</h2>"
        f"<p>{escape(summary_claim)}</p>"
        f"<ul>{warnings}</ul></section>"
        "</main>"
    )
