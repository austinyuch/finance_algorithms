"""Live backend rerun service (slice H-4, REQ-H4-001/002/003/006).

A thin orchestration layer that recomputes an Epic H experiment from user-selected
parameters through the **existing** deterministic pipeline
(``scripts/run_dl_experiment.py::run_experiment``) and normalizes the result into the
``live_compute`` interactive-research contract (the same block H-3 renders, with
``mode="live_compute"``). It validates parameters, fails closed on invalid input or
insufficient data, and never fabricates rows.

Honesty posture: every computed result is ``no_alpha_claim``, ranks OOS-net only with the
baseline visible, and carries approximate-vs-strict-PIT provenance. There is no
current-asof allocation / "buy now" output (REQ-H4-008, charter guard for Lane 2).

⚠️ Framework isolation: orchestration only — this module must not import torch/tf/jax.
The optional torch backend is reached lazily inside ``NumpyMLPForecaster``, unchanged.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Mapping

_CLAIM = "no_alpha_claim"
_AUTHORITY = "out_of_sample_net_only"
_BACKENDS = ("reference", "pytorch", "jax", "tensorflow")
_REBALANCES = ("monthly", "quarterly")

# SSOT for the supported parameter ranges (mirrors the H-3 dashboard contract ranges).
PARAMETER_RANGES: dict[str, Any] = {
    "hiddenUnits": {"min": 2, "max": 64, "step": 1},
    "lookback": {"min": 3, "max": 24, "step": 1},
    "epochs": {"min": 5, "max": 200, "step": 5},
    "seed": {"min": 0, "max": 999, "step": 1},
    "rebalance": list(_REBALANCES),
    "backend": list(_BACKENDS),
}

_INT_FIELDS = ("hiddenUnits", "lookback", "epochs", "seed")


def validate_parameters(parameters: Mapping[str, Any]) -> list[str]:
    """Return a list of validation errors (empty == valid). Fail-closed, no computation."""
    errors: list[str] = []
    if not isinstance(parameters, Mapping):
        return ["parameters must be an object"]

    backend = parameters.get("backend")
    if backend not in _BACKENDS:
        errors.append(f"backend must be one of {list(_BACKENDS)}")
    rebalance = parameters.get("rebalance")
    if rebalance not in _REBALANCES:
        errors.append(f"rebalance must be one of {list(_REBALANCES)}")

    for field in _INT_FIELDS:
        rng = PARAMETER_RANGES[field]
        value = parameters.get(field)
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{field} must be an integer")
            continue
        if value < rng["min"] or value > rng["max"]:
            errors.append(f"{field} must be within [{rng['min']}, {rng['max']}]")
        elif (value - rng["min"]) % rng["step"] != 0:
            errors.append(f"{field} must align to step {rng['step']} from {rng['min']}")

    symbols = parameters.get("symbols")
    if (not isinstance(symbols, (list, tuple)) or len(symbols) < 2
            or len(set(symbols)) != len(symbols)
            or not all(isinstance(s, str) and s for s in symbols)):
        errors.append("symbols must be >=2 unique non-empty strings")
    return errors


def _fail_closed(parameters: Mapping[str, Any], message: str, *, reason: str,
                 status: str = "fail_closed", compute_source: str = "live_backend") -> dict[str, Any]:
    return {
        "mode": "live_compute",
        "status": status,
        "lifecycle": status,
        "computeSource": compute_source,
        "claimBoundary": _CLAIM,
        "message": message,
        "reason": reason,
    }


def _points(values: list[float]) -> list[dict[str, Any]]:
    return [{"label": str(i + 1), "value": float(v)} for i, v in enumerate(values)]


def _returns_from_equity(equity: list[float]) -> list[float]:
    """Reconstruct the realized period returns from the equity curve (cumprod(1+r))."""
    out: list[float] = []
    for prev, cur in zip(equity, equity[1:]):
        out.append(float(cur / prev - 1.0) if prev else 0.0)
    return out


def _cagr(equity: list[float], periods_per_year: int) -> float:
    n = len(equity)
    final = equity[-1] if n else 1.0
    if n < 1 or final <= 0.0:
        return -1.0 if final <= 0.0 else 0.0
    return float(final ** (periods_per_year / n) - 1.0)


def _row_payload(row: Mapping[str, Any], periods_per_year: int) -> dict[str, Any]:
    equity = [float(v) for v in row["equity_curve"]]
    drawdown = [float(v) for v in row["drawdown"]]
    return {
        "strategyName": str(row["strategy_name"]),
        "isBaseline": bool(row["is_baseline"]),
        "oosNetSharpe": float(row["oos_net_sharpe"]),
        "oosNetCagr": _cagr(equity, periods_per_year),
        "maxDrawdown": float(min(drawdown)) if drawdown else 0.0,
        "equityCurve": _points(equity),
        "drawdown": _points(drawdown),
        "returnDistribution": _returns_from_equity(equity),
        "learningCurve": _points([float(v) for v in row.get("learning_curve", [])]),
    }


def build_live_payload(result: Mapping[str, Any], parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a computed ``run_experiment`` result into the live_compute contract block.

    Reuses the run_experiment performance report as the single calculation authority — no
    re-derivation of metrics here. Rows stay OOS-net sorted (the report already sorts) with
    the baseline visible.
    """
    report = result["performance_report"]
    ppy = int(report.get("periods_per_year", 12))
    rows = [_row_payload(r, ppy) for r in report["rows"]]
    window = result.get("data_window") or {}
    requested = str(parameters.get("backend"))
    resolved = str(result.get("backend") or requested)
    checksum = str(report["checksum"])
    return {
        "mode": "live_compute",
        "status": "computed",
        "lifecycle": "computed",
        "computeSource": "live_backend",
        "claimBoundary": _CLAIM,
        "metricAuthority": _AUTHORITY,
        "parameters": dict(parameters),
        "resolvedBackend": {
            "requested": requested,
            "resolved": resolved,
            "fallbackReason": None if resolved == requested
            else f"{requested} backend unavailable; fell back to {resolved}",
        },
        "dataLineage": {
            "source": "cr_b21_approximate_backfill",
            "dataWindow": {"start": str(window.get("start")), "end": str(window.get("end"))},
            "approximateAvailability": True,
            "strictPitExcluded": True,
            "warning": "research_mode_approximate_availability",
        },
        "artifact": {
            "experimentId": str(result["experiment_id"]),
            "reportChecksum": checksum,
            "artifactPath": str(result.get("artifact_path") or ""),
            "vizPath": str(result.get("viz_path") or ""),
        },
        "rows": rows,
        "warnings": [
            "no_alpha_claim",
            "out_of_sample_net_only",
            "research_mode_approximate_availability",
            "live_compute",
        ],
    }


def run_rerun(parameters: Mapping[str, Any], *, provider: Any,
              periods_per_year: int = 12) -> dict[str, Any]:
    """Validate → recompute via run_experiment (temp workspace) → normalize, fail-closed.

    ``provider`` is injected so the service is testable on a synthetic PIT panel; the ASGI
    app builds the real CR-B21 approximate-availability provider (see ``build_default_provider``).
    """
    from scripts.run_dl_experiment import run_experiment

    errors = validate_parameters(parameters)
    if errors:
        return _fail_closed(parameters, "; ".join(errors), reason="invalid_parameters")

    with tempfile.TemporaryDirectory(prefix="quantlab-rerun-") as tmp:
        workspace = Path(tmp)
        result = run_experiment(
            provider,
            symbols=list(parameters["symbols"]),
            hidden_units=int(parameters["hiddenUnits"]),
            lookback=int(parameters["lookback"]),
            epochs=int(parameters["epochs"]),
            seed=int(parameters["seed"]),
            rebalance=str(parameters["rebalance"]),
            backend=str(parameters["backend"]),
            out_path=workspace / "rerun.json",
            viz_path=workspace / "rerun.svg",
            registry_path=workspace / "rerun-registry.jsonl",
            periods_per_year=periods_per_year,
        )
        if result.get("status") != "computed":
            return _fail_closed(
                parameters,
                f"insufficient data for rerun: {result.get('reason', 'unknown')}",
                reason=str(result.get("reason") or "insufficient_data"),
            )
        # the workspace artifact/viz paths are temp-scoped; do not leak them as the public
        # artifactPath — present the in-memory checksummed report as the live artifact.
        result = dict(result)
        result["artifact_path"] = "live_compute (in-memory, not persisted)"
        result["viz_path"] = "live_compute (in-memory, not persisted)"
        return build_live_payload(result, parameters)


def build_default_provider(vintage_root: str = "data/vintage/raw/backfill-1990-01-01") -> Any:
    """Research-mode provider over the CR-B21 deep backfill (approximate availability)."""
    from quantlab.data.vintage import build_provider_from_vintage

    return build_provider_from_vintage(vintage_root, approximate_availability=True)


# --- minimal dependency-free ASGI app (real backend for the H4-7 smoke) ---

_RERUN_PATH = "/api/experiment/rerun"


async def _read_body(receive: Any) -> bytes:
    body = b""
    more = True
    while more:
        message = await receive()
        body += message.get("body", b"") or b""
        more = message.get("more_body", False)
    return body


def _json_response(status_code: int, payload: Mapping[str, Any]) -> tuple[int, bytes]:
    return status_code, json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _handle_rerun(body: bytes, *, provider_factory: Any) -> tuple[int, bytes]:
    try:
        request = json.loads(body or b"{}")
    except json.JSONDecodeError:
        return _json_response(400, _fail_closed({}, "invalid JSON body", reason="bad_request"))
    parameters = request.get("parameters") if isinstance(request, Mapping) else None
    if not isinstance(parameters, Mapping):
        return _json_response(400, _fail_closed({}, "request requires a 'parameters' object",
                                                reason="bad_request"))
    provider = provider_factory()
    result = run_rerun(parameters, provider=provider)
    return _json_response(200 if result.get("status") == "computed" else 422, result)


def make_app(provider_factory: Any = build_default_provider) -> Any:
    """Build the ASGI app. ``provider_factory`` is injectable for the real-backend smoke."""

    async def app(scope: Mapping[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":  # pragma: no cover - lifespan/websocket unused
            return
        method = scope.get("method", "GET")
        path = scope.get("path", "")
        if path != _RERUN_PATH:
            status_code, payload = _json_response(404, {"status": "error", "message": "not found"})
        elif method != "POST":
            status_code, payload = _json_response(405, {"status": "error",
                                                        "message": "method not allowed"})
        else:
            body = await _read_body(receive)
            status_code, payload = _handle_rerun(body, provider_factory=provider_factory)
        await send({"type": "http.response.start", "status": status_code,
                    "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": payload})

    return app


app = make_app()


__all__ = [
    "PARAMETER_RANGES",
    "validate_parameters",
    "build_live_payload",
    "run_rerun",
    "build_default_provider",
    "make_app",
    "app",
]
