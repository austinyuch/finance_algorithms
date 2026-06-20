"""H4-2/H4-8/H4-9 — live backend rerun service (REQ-H4-001/002/003/006/008).

The service recomputes an Epic H experiment from validated parameters through the real
``run_experiment`` pipeline and normalizes it into the ``live_compute`` contract. These
tests pin: fail-closed validation, computed-payload shape (OOS-net sorted, baseline
visible, no_alpha_claim), determinism, insufficient-data fail-closed, the charter guard
(no actionable signal), and the dependency-free ASGI transport.

Trace: REQ-H4-001/002/003/006/008, AC-H4-01, FMEA-H4-03/04/05.
"""
from __future__ import annotations

import asyncio
import json

import numpy as np
import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from quantlab.data.provider import InMemoryPITDataProvider
from quantlab.showcase import rerun_service as svc

_PPY = 12


def _provider(symbols=("GROWTH", "STEADY"), n_months=96) -> InMemoryPITDataProvider:
    rng = np.random.default_rng(11)
    dates = pd.date_range("2016-01-31", periods=n_months, freq="ME")
    rows = []
    for si, sym in enumerate(symbols):
        c = 100.0 + si * 5.0
        drift = 0.010 if si == 0 else 0.004
        for d in dates:
            c *= float(1 + rng.normal(drift, 0.03))
            rows.append({"symbol": sym, "event_date": d, "available_date": d, "close": round(c, 4)})
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("2014-01-01"),
                              "delist_date": pd.NaT} for s in symbols])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(pd.DataFrame(rows), listings, macro)


def _params(**over):
    p = {"backend": "reference", "hiddenUnits": 4, "lookback": 6, "epochs": 10,
         "seed": 0, "rebalance": "monthly", "symbols": ["GROWTH", "STEADY"]}
    p.update(over)
    return p


# --- validation (REQ-H4-003) ---

def test_validate_accepts_well_formed_parameters():
    assert svc.validate_parameters(_params()) == []


def test_validate_rejects_unknown_backend():
    assert any("backend" in e for e in svc.validate_parameters(_params(backend="mxnet")))


def test_validate_rejects_non_step_aligned_epochs():
    # epochs step is 5; 12 is not aligned
    assert any("epochs" in e for e in svc.validate_parameters(_params(epochs=12)))


def test_validate_rejects_out_of_range_hidden_units():
    assert any("hiddenUnits" in e for e in svc.validate_parameters(_params(hiddenUnits=999)))


def test_validate_rejects_bool_as_integer():
    assert any("seed" in e for e in svc.validate_parameters(_params(seed=True)))


def test_validate_rejects_fewer_than_two_symbols():
    assert any("symbols" in e for e in svc.validate_parameters(_params(symbols=["ONLYONE"])))


def test_validate_rejects_duplicate_symbols():
    assert any("symbols" in e for e in svc.validate_parameters(_params(symbols=["A", "A"])))


# --- computed payload shape (REQ-H4-001/006) ---

def test_run_rerun_computed_payload_is_contract_shaped():
    out = svc.run_rerun(_params(), provider=_provider(), periods_per_year=_PPY)
    assert out["status"] == "computed"
    assert out["mode"] == "live_compute"
    assert out["lifecycle"] == "computed"
    assert out["computeSource"] == "live_backend"
    assert out["claimBoundary"] == "no_alpha_claim"
    assert out["metricAuthority"] == "out_of_sample_net_only"
    assert len(out["rows"]) >= 2
    # baseline visible
    assert any(r["isBaseline"] for r in out["rows"])
    # OOS-net sorted descending
    sharpes = [r["oosNetSharpe"] for r in out["rows"]]
    assert sharpes == sorted(sharpes, reverse=True)
    # 64-hex checksum + experiment id
    assert len(out["artifact"]["reportChecksum"]) == 64
    assert len(out["artifact"]["experimentId"]) >= 8
    assert "no_alpha_claim" in out["warnings"]
    # every row carries the chart series
    for r in out["rows"]:
        assert len(r["equityCurve"]) >= 2
        assert len(r["returnDistribution"]) >= 1
        assert all("label" in p and "value" in p for p in r["equityCurve"])


def test_run_rerun_does_not_leak_temp_artifact_path():
    out = svc.run_rerun(_params(), provider=_provider())
    assert "/tmp" not in out["artifact"]["artifactPath"]
    assert "rerun.json" not in out["artifact"]["artifactPath"]


# --- determinism (REQ-H4-002, AC-H4-01.2) ---

def test_run_rerun_is_deterministic():
    a = svc.run_rerun(_params(), provider=_provider())
    b = svc.run_rerun(_params(), provider=_provider())
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# --- fail-closed (REQ-H4-003) ---

def test_run_rerun_invalid_params_fail_closed_no_rows():
    out = svc.run_rerun(_params(backend="mxnet"), provider=_provider())
    assert out["status"] == "fail_closed"
    assert out["lifecycle"] == "fail_closed"
    assert "rows" not in out
    assert out["reason"] == "invalid_parameters"


def test_run_rerun_insufficient_data_fail_closed():
    out = svc.run_rerun(_params(), provider=_provider(n_months=10))
    assert out["status"] == "fail_closed"
    assert "rows" not in out


# --- charter guard (REQ-H4-008): no actionable / current-asof recommendation ---

def test_payload_carries_no_actionable_signal():
    out = svc.run_rerun(_params(), provider=_provider())
    blob = json.dumps(out).lower()
    for banned in ("buy now", "recommendation", "allocate now", "current_allocation",
                   "actionable", "signal_now"):
        assert banned not in blob


# --- PBT: valid grids compute or fail-closed, never raise; honesty invariants hold ---

@given(
    hidden=st.integers(min_value=2, max_value=8),
    lookback=st.integers(min_value=3, max_value=8),
    seed=st.integers(min_value=0, max_value=5),
    rebalance=st.sampled_from(["monthly", "quarterly"]),
)
@settings(max_examples=6, deadline=None)
def test_pbt_valid_grid_computes_with_visible_sorted_baseline(hidden, lookback, seed, rebalance):
    out = svc.run_rerun(
        _params(hiddenUnits=hidden, lookback=lookback, seed=seed, rebalance=rebalance, epochs=5),
        provider=_provider(),
    )
    assert out["status"] in {"computed", "fail_closed"}
    if out["status"] == "computed":
        assert any(r["isBaseline"] for r in out["rows"])
        sharpes = [r["oosNetSharpe"] for r in out["rows"]]
        assert sharpes == sorted(sharpes, reverse=True)
        assert out["claimBoundary"] == "no_alpha_claim"


# --- ASGI transport (dependency-free) ---

def _drive(app, method: str, path: str, body: bytes = b"") -> tuple[int, dict]:
    scope = {"type": "http", "method": method, "path": path}
    sent: list[dict] = []

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(app(scope, receive, send))
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    payload = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return status, (json.loads(payload) if payload else {})


def test_asgi_app_computes_on_post():
    app = svc.make_app(provider_factory=_provider)
    status, payload = _drive(app, "POST", "/api/experiment/rerun",
                             json.dumps({"parameters": _params()}).encode("utf-8"))
    assert status == 200
    assert payload["status"] == "computed"


def test_asgi_app_fail_closed_returns_422():
    app = svc.make_app(provider_factory=_provider)
    status, payload = _drive(app, "POST", "/api/experiment/rerun",
                             json.dumps({"parameters": _params(backend="mxnet")}).encode("utf-8"))
    assert status == 422
    assert payload["status"] == "fail_closed"


def test_asgi_app_rejects_bad_method_and_path():
    app = svc.make_app(provider_factory=_provider)
    assert _drive(app, "GET", "/api/experiment/rerun")[0] == 405
    assert _drive(app, "POST", "/nope")[0] == 404


def test_asgi_app_rejects_malformed_json():
    app = svc.make_app(provider_factory=_provider)
    status, payload = _drive(app, "POST", "/api/experiment/rerun", b"{not json")
    assert status == 400
