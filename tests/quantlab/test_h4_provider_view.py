"""H4-1 — public PIT-provider read view (REQ-H4-007, AC-H4-05).

The rerun path and existing research/scripts must stop reaching into the private
``provider._prices``. These tests pin a public, copy-safe read surface for
universe/extent selection — ``symbols()``, ``event_span()``, ``price_panel()`` —
and assert it never leaks lookahead (it is extent-only; the as-of PIT gates
``get``/``history`` stay the only fetch path) and never returns invalid closes.

Trace: REQ-H4-007, AC-H4-05, FMEA-H4-06, ISSUE-DDD-PROVIDER-PRIVATE-001.
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from quantlab.data.provider import InMemoryPITDataProvider

_TS = pd.Timestamp
_LISTINGS = pd.DataFrame([
    {"symbol": "AAA", "list_date": _TS("2018-01-01"), "delist_date": pd.NaT},
    {"symbol": "BBB", "list_date": _TS("2018-01-01"), "delist_date": pd.NaT},
])
_MACRO = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])


def _provider(rows: list[dict]) -> InMemoryPITDataProvider:
    prices = pd.DataFrame(rows)
    return InMemoryPITDataProvider(prices, _LISTINGS.copy(), _MACRO.copy())


def _row(symbol: str, event: str, close: float) -> dict:
    d = _TS(event)
    return {"symbol": symbol, "event_date": d, "available_date": d, "close": close}


def _panel(closes_a: list[float], closes_b: list[float]) -> InMemoryPITDataProvider:
    dates = pd.date_range("2020-01-31", periods=max(len(closes_a), len(closes_b)), freq="ME")
    rows = []
    for d, c in zip(dates, closes_a):
        rows.append(_row("AAA", str(d.date()), c))
    for d, c in zip(dates, closes_b):
        rows.append(_row("BBB", str(d.date()), c))
    return _provider(rows)


def test_symbols_returns_sorted_unique_present_symbols():
    p = _panel([100.0, 110.0], [50.0, 55.0])
    assert p.symbols() == ["AAA", "BBB"]


def test_event_span_returns_overall_min_max():
    p = _panel([100.0, 110.0, 121.0], [50.0, 55.0, 60.0])
    start, end = p.event_span()
    assert start == _TS("2020-01-31")
    assert end == _TS("2020-03-31")


def test_event_span_empty_panel_is_none():
    p = _provider([])
    assert p.event_span() == (None, None)


def test_price_panel_returns_defensive_copy():
    p = _panel([100.0, 110.0], [50.0, 55.0])
    panel = p.price_panel()
    panel.loc[panel.index[0], "close"] = -999.0
    # mutating the returned frame must not corrupt provider state
    assert p.price_panel()["close"].min() > 0.0


def test_price_panel_symbol_filter():
    p = _panel([100.0, 110.0], [50.0, 55.0])
    only_a = p.price_panel(symbols=["AAA"])
    assert set(only_a["symbol"]) == {"AAA"}


def test_price_panel_usable_only_drops_non_finite_and_non_positive():
    p = _panel([100.0, float("nan"), -5.0, float("inf"), 121.0], [50.0, 55.0, 60.0, 65.0, 70.0])
    usable = p.price_panel(symbols=["AAA"], usable_only=True)
    # only the two finite-positive AAA closes survive
    assert sorted(usable["close"].tolist()) == [100.0, 121.0]


def test_price_panel_all_nan_asset_has_no_usable_rows():
    p = _panel([float("nan")] * 3, [50.0, 55.0, 60.0])
    usable = p.price_panel(usable_only=True)
    assert set(usable["symbol"]) == {"BBB"}


_ROOT = Path(__file__).resolve().parents[2]


def test_no_module_reaches_into_provider_private_prices():
    """AC-H4-05: no quantlab/ or scripts/ file reads `provider._prices`.

    Only `self._prices` inside the provider implementation is allowed; every other caller
    must use the public read view. Closes ISSUE-DDD-PROVIDER-PRIVATE-001.
    """
    offenders: list[str] = []
    for base in ("quantlab", "scripts"):
        for path in (_ROOT / base).rglob("*.py"):
            for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "._prices" not in line:
                    continue
                # the provider's own implementation legitimately uses self._prices
                if path.name == "provider.py" and "self._prices" in line:
                    continue
                offenders.append(f"{path.relative_to(_ROOT)}:{i}: {line.strip()}")
    assert not offenders, "private provider._prices reach-ins remain:\n" + "\n".join(offenders)


@given(
    closes=st.lists(
        st.one_of(st.floats(min_value=0.01, max_value=1e6),
                  st.just(float("nan")), st.just(float("-inf")),
                  st.just(float("inf")), st.just(0.0), st.floats(max_value=0.0)),
        min_size=1, max_size=20,
    )
)
@settings(max_examples=50, deadline=None)
def test_pbt_usable_panel_never_returns_invalid_close(closes):
    dates = pd.date_range("2020-01-31", periods=len(closes), freq="ME")
    rows = [_row("AAA", str(d.date()), c) for d, c in zip(dates, closes)]
    p = _provider(rows)
    usable = p.price_panel(usable_only=True)
    for c in usable["close"]:
        assert math.isfinite(c) and c > 0.0
