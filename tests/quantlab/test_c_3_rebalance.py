"""C-3 time + regime rebalance hook tests."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings, strategies as st


def _regime_provider(price_values):
    from quantlab.data.provider import InMemoryPITDataProvider

    dates = pd.date_range("2020-01-31", periods=len(price_values), freq="ME")
    prices = pd.DataFrame(
        [
            {"symbol": "SP500", "event_date": d, "available_date": d, "close": float(v)}
            for d, v in zip(dates, price_values)
        ]
    )
    listings = pd.DataFrame(
        [{"symbol": "SP500", "list_date": pd.Timestamp("2019-01-01"), "delist_date": pd.NaT}]
    )
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro), dates


def test_time_rebalance_schedule_uses_calendar_frequency():
    from quantlab.portfolio import time_rebalance_dates

    dates = pd.date_range("2021-01-31", periods=6, freq="ME")

    assert time_rebalance_dates(dates, "monthly") == list(dates)
    assert time_rebalance_dates(dates, "quarterly") == [dates[2], dates[5]]
    assert time_rebalance_dates(dates, "semiannual") == [dates[5]]


def test_regime_rebalance_includes_first_time_due_and_regime_changes():
    from quantlab.portfolio import select_rebalance_dates

    dates = pd.date_range("2021-01-31", periods=6, freq="ME")
    labels = ["risk_on", "risk_on", "risk_on", "defensive", "defensive", "risk_on"]

    assert select_rebalance_dates(dates, labels, frequency="quarterly") == [
        dates[0],
        dates[2],
        dates[3],
        dates[5],
    ]


@settings(max_examples=80)
@given(labels=st.lists(st.sampled_from(["risk_on", "defensive", "unknown"]), min_size=1, max_size=36))
def test_pbt_regime_rebalance_is_ordered_subset_and_captures_changes(labels):
    from quantlab.portfolio import select_rebalance_dates

    dates = pd.date_range("2020-01-31", periods=len(labels), freq="ME")
    selected = select_rebalance_dates(dates, labels, frequency=None)

    assert selected
    assert selected[0] == dates[0]
    assert selected == sorted(selected)
    assert set(selected).issubset(set(dates))

    selected_positions = [dates.get_loc(d) for d in selected]
    for pos in selected_positions[1:]:
        assert labels[pos] != labels[pos - 1]
    for pos in range(1, len(labels)):
        if labels[pos] != labels[pos - 1]:
            assert dates[pos] in selected


def test_regime_rebalance_smoke_consumes_first_regime_classifier():
    from quantlab.models import FirstRegimeClassifier
    from quantlab.portfolio import select_regime_rebalance_dates

    up = 100 * np.cumprod(np.full(15, 1.01))
    down = up[-1] * np.cumprod(np.full(15, 0.98))
    data, dates = _regime_provider(np.concatenate([up, down]))
    classifier = FirstRegimeClassifier(price_symbol="SP500", lookback=12)

    selected = select_regime_rebalance_dates(dates[12:], classifier, data, frequency="quarterly")

    assert selected[0] == dates[12]
    assert any(d > dates[15] for d in selected)
    assert classifier.predict(selected[-1], data).label in {"risk_on", "defensive", "unknown"}


def test_rebalance_rejects_mismatched_dates_and_regime_labels():
    from quantlab.portfolio import select_rebalance_dates

    dates = pd.date_range("2021-01-31", periods=2, freq="ME")

    with pytest.raises(ValueError, match="same length"):
        select_rebalance_dates(dates, ["risk_on"], frequency="monthly")
