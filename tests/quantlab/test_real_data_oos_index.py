"""Tests — CR-RDO-003 market-index real-data OOS: approximate availability,
SMA-timing strategy, degeneracy guard, availability_mode marker."""
from __future__ import annotations

import pandas as pd
import pytest

from quantlab.data.provider import InMemoryPITDataProvider
from quantlab.research.real_data_oos import build_real_data_oos_report
from quantlab.strategies import BuyAndHold, SmaTimingStrategy


def _provider(closes, *, symbol="IDX", available_equals_event=True, start="2016-01-31"):
    dates = pd.date_range(start, periods=len(closes), freq="ME")
    rows = [{"symbol": symbol, "event_date": d,
             "available_date": d if available_equals_event else pd.Timestamp("2099-01-01"),
             "close": float(c)} for d, c in zip(dates, closes)]
    listings = pd.DataFrame([{"symbol": symbol, "list_date": pd.Timestamp("1990-01-01"),
                              "delist_date": pd.NaT}])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(pd.DataFrame(rows), listings, macro)


_FACTORS = [1.03, 0.98, 1.02, 0.97, 1.04, 0.99]


def _varying(n):
    c, out = 100.0, []
    for i in range(n):
        c *= _FACTORS[i % len(_FACTORS)]
        out.append(round(c, 4))
    return out


def _cfg():
    return {"rebalance": "monthly", "mode": "net", "cost_config": {"commission_bps": 5},
            "walk_forward": {"train_window_months": 12, "test_window_months": 6, "step_months": 6}}


# --- approximate availability (loader) ---

def test_approximate_availability_sets_event_date_availability():
    from quantlab.data.vintage import build_provider_from_vintage
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "data" / "vintage" / "raw"
    p = build_provider_from_vintage(root, fred_price_series={"SP500"}, approximate_availability=True)
    pr = p._prices
    assert len(pr) and (pr["available_date"] == pr["event_date"]).all()
    # default (true PIT) keeps the capture-date availability (>> event dates)
    p_pit = build_provider_from_vintage(root, fred_price_series={"SP500"})
    assert (p_pit._prices["available_date"] > p_pit._prices["event_date"]).any()


# --- SMA timing strategy ---

def test_sma_timing_invests_above_sma_and_exits_below():
    rising = _provider([10, 11, 12, 13, 14, 15, 16], available_equals_event=True)
    strat = SmaTimingStrategy("IDX", window=3)
    # last (16) > SMA of last 3 (14,15,16=15) -> invested
    assert strat.generate_signal(pd.Timestamp("2016-07-31"), rising)["IDX"] == 1.0
    falling = _provider([20, 19, 18, 17, 16, 15, 14], available_equals_event=True)
    # last (14) < SMA of last 3 (16,15,14=15) -> cash
    assert falling and SmaTimingStrategy("IDX", window=3).generate_signal(
        pd.Timestamp("2016-07-31"), falling)["IDX"] == 0.0


def test_sma_timing_rejects_bad_window():
    with pytest.raises(ValueError):
        SmaTimingStrategy("IDX", window=1)


# --- degeneracy guard + availability_mode ---

def test_degeneracy_guard_raises_on_flat_oos():
    flat = _provider([100.0] * 30, available_equals_event=True)  # constant price -> flat returns
    with pytest.raises(ValueError, match="degenerate"):
        build_real_data_oos_report(flat, candidate=SmaTimingStrategy("IDX", window=6),
                                   baseline=BuyAndHold(["IDX"]), config=_cfg(), min_assets=1)


def test_report_records_availability_mode_and_is_non_degenerate():
    prov = _provider(_varying(30), available_equals_event=True)
    report = build_real_data_oos_report(
        prov, candidate=SmaTimingStrategy("IDX", window=6), baseline=BuyAndHold(["IDX"]),
        config=_cfg(), min_assets=1, availability_mode="approximate_event_date")
    assert report["status"] == "computed"
    assert report["availability_mode"] == "approximate_event_date"
    assert report["data_provenance"]["availability_mode"] == "approximate_event_date"
    assert any(r["is_baseline"] for r in report["rows"])
    assert len(report["rows"]) == 2
