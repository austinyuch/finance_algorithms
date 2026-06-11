"""D-1 first regime model signal contract — RED phase tests."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _provider(price_values, macro_rows=None):
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
    macro = pd.DataFrame(macro_rows or [], columns=["series", "event_date", "available_date", "value"])
    if not macro.empty:
        macro["event_date"] = pd.to_datetime(macro["event_date"])
        macro["available_date"] = pd.to_datetime(macro["available_date"])
    return InMemoryPITDataProvider(prices, listings, macro), dates


def test_regime_signal_is_stable_and_framework_light():
    from quantlab.models.regime import FirstRegimeClassifier, RegimeSignal

    values = 100 * np.cumprod(np.full(18, 1.01))
    macro_rows = [
        {"series": "T10Y2Y", "event_date": "2021-05-31", "available_date": "2021-05-31", "value": 0.8}
    ]
    data, dates = _provider(values, macro_rows)
    clf = FirstRegimeClassifier(price_symbol="SP500", lookback=12)

    signal = clf.predict(dates[-1], data)
    assert isinstance(signal, RegimeSignal)
    assert signal.label == "risk_on"
    assert signal.confidence > 0
    assert signal.feature_status["price_trend"] == "available"
    assert signal.feature_status["yield_curve"] == "available"
    assert clf.predict(dates[-1], data) == signal


def test_regime_missing_features_falls_back_to_unknown():
    from quantlab.models.regime import FirstRegimeClassifier

    data, dates = _provider([100.0, 101.0])
    signal = FirstRegimeClassifier(price_symbol="SP500", lookback=12).predict(dates[-1], data)

    assert signal.label == "unknown"
    assert signal.confidence == 0.0
    assert signal.feature_status["price_trend"] == "missing"
    assert signal.feature_status["yield_curve"] == "missing"


def test_regime_uses_asof_gate_for_price_and_macro_revisions():
    from quantlab.models.regime import FirstRegimeClassifier

    values = 100 * np.cumprod(np.full(18, 1.01))
    macro_rows = [
        {"series": "T10Y2Y", "event_date": "2021-05-31", "available_date": "2021-05-31", "value": 0.8},
        # Future revision should not be visible at 2021-06-30.
        {"series": "T10Y2Y", "event_date": "2021-05-31", "available_date": "2021-08-31", "value": -1.0},
    ]
    data, dates = _provider(values, macro_rows)
    clf = FirstRegimeClassifier(price_symbol="SP500", lookback=12)

    before_revision = clf.predict(pd.Timestamp("2021-06-30"), data)
    after_revision = clf.predict(pd.Timestamp("2021-09-30"), data)

    assert before_revision.label == "risk_on"
    assert after_revision.label == "defensive"


def test_regime_detects_defensive_trend_without_macro():
    from quantlab.models.regime import FirstRegimeClassifier

    values = 100 * np.cumprod(np.full(18, 0.99))
    data, dates = _provider(values)

    signal = FirstRegimeClassifier(price_symbol="SP500", lookback=12).predict(dates[-1], data)
    assert signal.label == "defensive"
    assert signal.feature_status["price_trend"] == "available"
