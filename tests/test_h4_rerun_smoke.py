"""H4-7 — real-backend rerun smoke (AC-H4-02, FMEA-H4-01): the load-bearing guard.

Starts the *real* live-rerun ASGI backend on a governed dynamic port and proves it
returns a FRESHLY COMPUTED, checksum-verified artifact — not a replayed fixture — by
asserting that perturbing the seed changes the report checksum. A stubbed backend that
returns a constant fixture is shown to FAIL the very same freshness assertion, so a stub
can never produce a green "live" result (Global Constraint #11: no false-green demos).

Trace: AC-H4-02.1/.2, FMEA-H4-01.
"""
from __future__ import annotations

import json
import socket
import threading
import time
from contextlib import contextmanager
from typing import Any, Callable

import numpy as np
import pandas as pd
import pytest
import requests
import uvicorn

from quantlab.data.provider import InMemoryPITDataProvider
from quantlab.showcase.rerun_service import make_app


def _provider() -> InMemoryPITDataProvider:
    rng = np.random.default_rng(11)
    dates = pd.date_range("2016-01-31", periods=48, freq="ME")
    rows = []
    for si, sym in enumerate(("GROWTH", "STEADY")):
        c = 100.0 + si * 5.0
        drift = 0.010 if si == 0 else 0.004
        for d in dates:
            c *= float(1 + rng.normal(drift, 0.03))
            rows.append({"symbol": sym, "event_date": d, "available_date": d, "close": round(c, 4)})
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("2014-01-01"),
                              "delist_date": pd.NaT} for s in ("GROWTH", "STEADY")])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(pd.DataFrame(rows), listings, macro)


def _params(seed: int) -> dict:
    return {"backend": "reference", "hiddenUnits": 4, "lookback": 6, "epochs": 5,
            "seed": seed, "rebalance": "monthly", "symbols": ["GROWTH", "STEADY"]}


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = int(s.getsockname()[1])
    s.close()
    return port


@contextmanager
def _serve(app: Any):
    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", lifespan="off")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        for _ in range(200):
            if server.started:
                break
            time.sleep(0.05)
        if not server.started:
            raise RuntimeError("rerun backend did not start")
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def _post_checksum(base_url: str, seed: int) -> tuple[int, dict]:
    response = requests.post(f"{base_url}/api/experiment/rerun",
                             json={"parameters": _params(seed)}, timeout=60)
    return response.status_code, response.json()


def _assert_fresh_compute(post: Callable[[int], tuple[int, dict]]) -> None:
    """The real-backend contract: a computed artifact whose checksum tracks the inputs.

    A genuine compute returns ``computed`` for both seeds AND a *different* reportChecksum
    (the seed changes the model init/training). A fixture-returning stub cannot satisfy this.
    """
    s0, p0 = post(0)
    s1, p1 = post(1)
    assert s0 == 200 and p0["status"] == "computed", "real backend must compute for seed 0"
    assert s1 == 200 and p1["status"] == "computed", "real backend must compute for seed 1"
    assert len(p0["artifact"]["reportChecksum"]) == 64
    assert p0["artifact"]["reportChecksum"] != p1["artifact"]["reportChecksum"], (
        "freshly computed checksum must depend on inputs (fixture/stub would be constant)"
    )


@pytest.mark.smoke
def test_real_backend_smoke_returns_fresh_compute():
    with _serve(make_app(provider_factory=_provider)) as base_url:
        _assert_fresh_compute(lambda seed: _post_checksum(base_url, seed))


@pytest.mark.smoke
def test_real_backend_is_deterministic_for_identical_params():
    with _serve(make_app(provider_factory=_provider)) as base_url:
        _, a = _post_checksum(base_url, 0)
        _, b = _post_checksum(base_url, 0)
        assert a["artifact"]["reportChecksum"] == b["artifact"]["reportChecksum"]


def test_stub_backend_fails_the_freshness_assertion():
    """Negative (AC-H4-02.2): a stub returning a constant fixture cannot go green.

    Drives the exact freshness assertion the real smoke uses; it MUST raise, proving the
    smoke detects a non-computing stub instead of falsely passing it.
    """
    fixture = {
        "status": "computed",
        "artifact": {"reportChecksum": "f" * 64},  # constant regardless of input
    }

    def stub_post(_seed: int) -> tuple[int, dict]:
        return 200, json.loads(json.dumps(fixture))

    with pytest.raises(AssertionError):
        _assert_fresh_compute(stub_post)
