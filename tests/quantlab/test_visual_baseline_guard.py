"""CR-FBP-001 — the traceability hash-surface check tolerates a deterministically
re-pinned baseline (baseline == current) while still catching a distinct stale
baseline hash."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_GUARDS = Path(__file__).resolve().parent / "test_governance_guards.py"


def _helper():
    spec = importlib.util.spec_from_file_location("_gg_for_guard_test", _GUARDS)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod._assert_hash_surface_publishes_current


CUR = "a" * 64
STALE = "b" * 64


def test_accepts_repinned_baseline_equal_to_current():
    # baseline == current (0-pixel deterministic re-pin): publishing the hash is fine.
    _helper()(f"screenshot {CUR} proven", CUR, CUR)


def test_accepts_distinct_baseline_when_only_current_published():
    _helper()(f"screenshot {CUR} proven", CUR, STALE)


def test_requires_current_hash_present():
    with pytest.raises(AssertionError):
        _helper()("no hash here", CUR, STALE)


def test_rejects_distinct_stale_baseline_hash_present():
    with pytest.raises(AssertionError):
        _helper()(f"current {CUR} but also stale {STALE}", CUR, STALE)
