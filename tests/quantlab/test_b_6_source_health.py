"""B-6 source health registry tests.

RED: added before quantlab.data.source_health exists.
"""
from __future__ import annotations

from hypothesis import given, strategies as st


def test_source_health_summary_marks_stooq_blocked_without_reenabling_defaults():
    from quantlab.data.source_health import SourceHealthRegistry

    registry = SourceHealthRegistry()
    registry.record("stooq", "2330.tw", status="blocked", default_enabled=False, reason="HTTP 404")
    registry.record("yahoo", "2330.TW", status="available", default_enabled=True, reason="chart ok")
    registry.record("fred", "PCOPPUSDM", status="available", default_enabled=True)

    summary = registry.summary()

    assert summary["stooq"]["status"] == "blocked"
    assert summary["stooq"]["default_enabled"] is False
    assert summary["yahoo"]["status"] == "available"
    assert summary["fred"]["status"] == "available"
    assert summary["claim_boundary"] == "source_contract_status_only"


def test_source_health_registry_requires_explicit_status_for_unknown_sources():
    from quantlab.data.source_health import SourceHealthRegistry

    registry = SourceHealthRegistry()
    registry.record("vendor-x", "abc", status="unknown", default_enabled=False)

    summary = registry.summary()

    assert summary["vendor-x"]["status"] == "unknown"
    assert summary["vendor-x"]["default_enabled"] is False
    assert summary["claim_boundary"] == "source_contract_status_only"


@given(
    source=st.text(min_size=1, max_size=24).filter(lambda s: s.strip() != ""),
    symbol=st.text(min_size=1, max_size=24).filter(lambda s: s.strip() != ""),
    status=st.sampled_from(["available", "blocked", "degraded", "unknown"]),
)
def test_pbt_source_health_summary_preserves_latest_source_status(source, symbol, status):
    from quantlab.data.source_health import SourceHealthRegistry

    registry = SourceHealthRegistry()
    registry.record(source, symbol, status="unknown", default_enabled=False)
    registry.record(source, symbol, status=status, default_enabled=(status == "available"))

    key = source.strip().lower()
    summary = registry.summary()

    assert summary[key]["status"] == status
    assert summary[key]["symbols"][-1] == symbol.strip()
