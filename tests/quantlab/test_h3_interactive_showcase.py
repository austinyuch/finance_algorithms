"""H-3 interactive research UI canonical payload tests."""
from __future__ import annotations

from quantlab.showcase.scenario import build_canonical_dashboard_artifact


def test_h3_canonical_payload_carries_interactive_research_lineage(tmp_path):
    payload = build_canonical_dashboard_artifact(tmp_path / "work")

    interactive = payload["interactiveResearch"]
    assert interactive["mode"] == "static_replay"
    assert interactive["status"] == "computed"
    assert interactive["claimBoundary"] == "no_alpha_claim"
    assert interactive["metricAuthority"] == "out_of_sample_net_only"
    assert interactive["parameters"] == {
        "backend": "reference",
        "hiddenUnits": 4,
        "lookback": 6,
        "epochs": 20,
        "seed": 0,
        "rebalance": "monthly",
        "symbols": ["GROWTH", "STEADY"],
    }
    assert interactive["resolvedBackend"] == {
        "requested": "reference",
        "resolved": "reference",
        "fallbackReason": None,
    }
    assert interactive["dataLineage"]["source"] == "cr_b21_approximate_backfill"
    assert interactive["dataLineage"]["approximateAvailability"] is True
    assert interactive["dataLineage"]["strictPitExcluded"] is True
    assert interactive["dataLineage"]["warning"] == "research_mode_approximate_availability"
    assert interactive["artifact"]["experimentId"]
    assert interactive["artifact"]["reportChecksum"]
    assert len(interactive["artifact"]["reportChecksum"]) == 64
    assert len(interactive["rows"]) >= 2
    assert any(row["isBaseline"] for row in interactive["rows"])
    assert interactive["rows"] == sorted(
        interactive["rows"],
        key=lambda row: row["oosNetSharpe"],
        reverse=True,
    )
    assert "no_alpha_claim" in interactive["warnings"]
    assert "research_mode_approximate_availability" in interactive["warnings"]
