"""CLI tests — CR-RDO-005 multi-cycle multi-asset OOS-net backtest.

Integration / e2e / smoke for `scripts/run_multi_cycle_oos_backtest.py`:
- integration+e2e: real CR-B21 deep backfill -> exit 0, computed, >=2 assets,
  multi-cycle window, families ranked, artifact validates (REQ-RDO5-005);
- e2e fail-closed: insufficient / oversampled / degenerate -> exit 2 with reason;
- smoke: a minimal computed run writes a schema-valid artifact fast.
no_alpha_claim throughout.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd

from quantlab.data.provider import InMemoryPITDataProvider
from quantlab.research.multi_cycle_oos import validate_multi_cycle_artifact

_MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_multi_cycle_oos_backtest.py"
_spec = importlib.util.spec_from_file_location("run_multi_cycle_oos_backtest", _MODULE_PATH)
cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cli)

_REPO = Path(__file__).resolve().parents[1]
_BACKFILL = _REPO / "data" / "vintage" / "raw" / "backfill-1990-01-01"
_COMMITTED_ARTIFACT = (_REPO / ".agents" / "specs" / "real-data-oos-backtest" / "reports"
                       / "multi-cycle-family-oos-artifact.json")


def _provider(specs, *, flat=False):
    prows = []
    factors = [1.03, 0.98, 1.02, 0.97, 1.04, 0.99]
    for si, (sym, start, n, freq) in enumerate(specs):
        dates = pd.date_range(start, periods=n, freq=freq)
        c = 100.0 + si * 9
        for i, d in enumerate(dates):
            if not flat:
                c *= factors[(i * (si + 1)) % len(factors)]
            prows.append({"symbol": sym, "event_date": d, "available_date": d,
                          "close": 100.0 if flat else round(c, 4)})
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("1990-01-01"),
                              "delist_date": pd.NaT} for s, _, _, _ in specs])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(pd.DataFrame(prows), listings, macro)


def test_integration_committed_real_artifact_is_multi_cycle_multi_asset():
    """Integration: validate the committed real deep-history evidence artifact.

    The expensive ~9-min engine run over 2000->2026 is performed once via
    `uv run python scripts/run_multi_cycle_oos_backtest.py` and committed; this
    test validates that committed evidence cheaply (same pattern as the
    single-window `real-data-oos-artifact.json`). Regenerable on demand.
    """
    assert _COMMITTED_ARTIFACT.exists(), "run scripts/run_multi_cycle_oos_backtest.py to generate"
    art = json.loads(_COMMITTED_ARTIFACT.read_text())
    validate_multi_cycle_artifact(art)
    report = art["report"]
    assert report["status"] == "computed"
    assert art["claim_boundary"] == "no_alpha_claim"
    # multi-asset
    assert len(report["asset_set"]) >= 2
    # multi-cycle: deep window covers at least GFC, COVID, 2022 (dot-com if >=1993 start)
    covered = {c["name"] for c in report["data_provenance"]["cycles_covered"]}
    assert {"gfc", "covid", "rate_shock_2022"} <= covered
    assert report["data_provenance"]["overlap_months"] >= 300.0
    # baseline visible + families ranked desc
    assert any(r["is_baseline"] for r in report["rows"])
    sharpes = [r["oos_net_sharpe"] for r in report["rows"]]
    assert sharpes == sorted(sharpes, reverse=True)
    assert {"baseline", "regime", "return_risk", "robust"} <= {r["model_family"] for r in report["rows"]}
    # approximate availability, never alpha
    assert report["availability_mode"] == "approximate_event_date"


def test_e2e_insufficient_exits_2(tmp_path):
    provider = _provider([("AAA", "2024-01-01", 60, "D"), ("BBB", "2024-01-01", 60, "D")])
    out = tmp_path / "a.json"
    rc = cli.run_multi_cycle_oos(provider, generated_at="2026-06-16T00:00:00Z", out=out,
                                 min_assets=2, min_history_months=300.0)
    assert rc == 2
    art = json.loads(out.read_text())
    assert art["status"] == "insufficient_data" and art["row_count"] == 0


def test_e2e_oversampled_exits_2(tmp_path):
    provider = _provider([("DLY", "2010-01-01", 4000, "D"), ("QTR", "2010-01-01", 64, "QE")])
    out = tmp_path / "a.json"
    rc = cli.run_multi_cycle_oos(provider, generated_at="2026-06-16T00:00:00Z", out=out,
                                 min_assets=2, min_history_months=18.0)
    assert rc == 2
    art = json.loads(out.read_text())
    assert art["report"]["reason"] == "oversampled_vs_native_frequency"


def test_e2e_degenerate_exits_2(tmp_path):
    provider = _provider([("AAA", "2010-01-01", 4000, "D"), ("BBB", "2010-01-01", 4000, "D")], flat=True)
    out = tmp_path / "a.json"
    rc = cli.run_multi_cycle_oos(provider, generated_at="2026-06-16T00:00:00Z", out=out,
                                 min_assets=2, min_history_months=18.0)
    assert rc == 2
    art = json.loads(out.read_text())
    assert art["report"]["reason"] == "degenerate_flat_oos"


def test_smoke_minimal_computed_artifact_is_valid(tmp_path):
    """Smoke: a small synthetic computed run writes a schema-valid artifact fast."""
    provider = _provider([("AAA", "2016-01-01", 1500, "D"), ("BBB", "2016-01-01", 1500, "D")])
    out = tmp_path / "smoke.json"
    rc = cli.run_multi_cycle_oos(provider, generated_at="2026-06-16T00:00:00Z", out=out,
                                 min_assets=2, min_history_months=18.0)
    assert rc == 0
    art = json.loads(out.read_text())
    validate_multi_cycle_artifact(art)
    assert art["report"]["status"] == "computed"
