"""CLI tests — scripts/run_real_data_oos_backtest.py (spec: real-data-oos-backtest).

Covers REQ-RDO-001 (exit 0 + computed artifact on sufficient data) and
REQ-RDO-003 (exit 2 + insufficient_data artifact, fail closed). Also asserts the
honest current state: real on-disk vintage data is still insufficient.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd

from quantlab.data.provider import InMemoryPITDataProvider
from quantlab.research.real_data_oos import assess_data_sufficiency

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_real_data_oos_backtest.py"


def _load():
    spec = importlib.util.spec_from_file_location("run_real_data_oos_backtest", MODULE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _provider(symbols, n_months) -> InMemoryPITDataProvider:
    dates = pd.date_range("2023-01-31", periods=n_months, freq="ME")
    factors = [1.03, 0.98, 1.02, 0.97, 1.04, 0.99]
    prows = []
    for si, sym in enumerate(symbols):
        c = 100.0 + si * 7.0
        for i, d in enumerate(dates):
            c *= factors[(i + si) % len(factors)]
            prows.append({"symbol": sym, "event_date": d, "available_date": d,
                          "close": round(c, 4)})
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("2020-01-01"),
                              "delist_date": pd.NaT} for s in symbols])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(pd.DataFrame(prows), listings, macro)


def test_cli_sufficient_data_exits_zero_and_writes_computed_artifact(tmp_path: Path):
    mod = _load()
    out = tmp_path / "art.json"
    rc = mod.run_real_data_oos(_provider(["AAA", "BBB"], 24), generated_at="2026-06-13T00:00:00Z",
                               out=out)
    assert rc == 0
    artifact = json.loads(out.read_text())
    assert artifact["status"] == "computed"
    assert artifact["claim_boundary"] == "no_alpha_claim"
    assert artifact["row_count"] == 2


def test_cli_thin_data_fails_closed_exit_two(tmp_path: Path):
    mod = _load()
    out = tmp_path / "art.json"
    rc = mod.run_real_data_oos(_provider(["AAA", "BBB"], 3), generated_at="2026-06-13T00:00:00Z",
                               out=out)
    assert rc == 2
    artifact = json.loads(out.read_text())
    assert artifact["status"] == "insufficient_data"
    assert artifact["row_count"] == 0
    assert artifact["claim_boundary"] == "no_alpha_claim"


def test_cli_single_index_runs_computed_timing_comparison(tmp_path: Path):
    # CR-RDO-003: a single market index is valid (min_assets=1) — SMA-timing
    # candidate vs buy-and-hold baseline, a non-degenerate comparison.
    mod = _load()
    out = tmp_path / "art.json"
    rc = mod.run_real_data_oos(_provider(["AAA"], 24), generated_at="2026-06-14T00:00:00Z",
                               out=out, availability_mode="approximate_event_date")
    assert rc == 0
    artifact = json.loads(out.read_text())
    assert artifact["status"] == "computed"
    assert artifact["report"]["availability_mode"] == "approximate_event_date"
    names = {r["strategy_name"] for r in artifact["report"]["rows"]}
    assert names == {"SmaTimingStrategy", "BuyAndHold"}


def test_cli_min_assets_two_with_one_asset_fails_closed(tmp_path: Path):
    mod = _load()
    rc = mod.run_real_data_oos(_provider(["AAA"], 24), generated_at="t", min_assets=2)
    assert rc == 2


def test_cli_degenerate_flat_oos_fails_closed(tmp_path: Path):
    # True-PIT single-capture vintage is invisible to historical as-ofs -> flat
    # OOS -> the CLI must fail closed (degenerate), not emit a "computed" claim.
    from quantlab.data.vintage import build_provider_from_vintage

    mod = _load()
    out = tmp_path / "art.json"
    provider = build_provider_from_vintage(mod.VINTAGE_ROOT, fred_price_series={"SP500"})  # true PIT
    rc = mod.run_real_data_oos(provider, generated_at="t", out=out)
    assert rc == 2
    artifact = json.loads(out.read_text())
    assert artifact["status"] == "insufficient_data"
    assert artifact["report"]["reason"] == "degenerate_flat_oos"


def test_cli_oversampled_mixed_frequency_fails_closed(tmp_path: Path):
    # CR-RDO-004: a quarterly asset under the default monthly rebalance is
    # oversampled (stale forward-fill would fabricate flat returns) -> fail closed
    # with an explicit reason, never a misleading "computed" claim.
    mod = _load()
    monthly = pd.date_range("2010-01-31", periods=180, freq="ME")
    quarterly = pd.date_range("2010-03-31", periods=60, freq="QE")
    factors = [1.03, 0.98, 1.02, 0.97, 1.04, 0.99]
    prows = []
    for si, (sym, dates) in enumerate((("MON", monthly), ("QTR", quarterly))):
        c = 100.0 + si * 7.0
        for i, d in enumerate(dates):
            c *= factors[(i + si) % len(factors)]
            prows.append({"symbol": sym, "event_date": d, "available_date": d, "close": round(c, 4)})
    listings = pd.DataFrame([{"symbol": s, "list_date": pd.Timestamp("2000-01-01"),
                              "delist_date": pd.NaT} for s in ("MON", "QTR")])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    provider = InMemoryPITDataProvider(pd.DataFrame(prows), listings, macro)

    out = tmp_path / "art.json"
    rc = mod.run_real_data_oos(provider, generated_at="t", out=out, min_assets=2)
    assert rc == 2
    artifact = json.loads(out.read_text())
    assert artifact["status"] == "insufficient_data"
    assert artifact["report"]["reason"] == "oversampled_vs_native_frequency"


def test_real_disk_vintage_data_runs_a_computed_comparison(tmp_path: Path):
    # Honest current-state guard: real accumulated vintage data (FRED price
    # proxies carry decades of history) IS sufficient for a walk-forward OOS
    # comparison, so the CLI runs end-to-end and emits a computed artifact.
    # Boundary: the default proxy universe is not co-temporal (a 1992-start FRED
    # proxy mixed with 2026-only equities); OOS-net values are mechanism evidence
    # under no_alpha_claim, not a strategy verdict.
    from quantlab.data.vintage import build_provider_from_vintage

    mod = _load()
    provider = build_provider_from_vintage(mod.VINTAGE_ROOT, fred_price_series=mod.PRICE_PROXIES)
    suff = assess_data_sufficiency(provider)
    assert suff.sufficient is True
    assert suff.asset_count >= 2

    out = tmp_path / "real.json"
    rc = mod.run_real_data_oos(provider, generated_at="2026-06-13T00:00:00Z", out=out)
    assert rc == 0
    artifact = json.loads(out.read_text())
    assert artifact["status"] == "computed"
    assert artifact["claim_boundary"] == "no_alpha_claim"
    assert any(r["is_baseline"] for r in artifact["report"]["rows"])
