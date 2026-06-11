"""Time and regime rebalance triggers for C-3."""
from __future__ import annotations

from typing import Any, Sequence

import pandas as pd


_FREQUENCY_PERIODS = {
    "monthly": 1,
    "quarterly": 3,
    "semiannual": 6,
}


def _to_timestamps(dates: Sequence[Any]) -> list[pd.Timestamp]:
    return [pd.Timestamp(d) for d in dates]


def time_rebalance_dates(dates: Sequence[Any], frequency: str | None = "monthly") -> list[pd.Timestamp]:
    """Select calendar-based rebalance dates from an ordered date sequence."""
    ordered = _to_timestamps(dates)
    if not ordered:
        return []
    if frequency is None:
        return []
    if frequency not in _FREQUENCY_PERIODS:
        raise ValueError(f"unsupported rebalance frequency: {frequency}")
    step = _FREQUENCY_PERIODS[frequency]
    return [d for i, d in enumerate(ordered, start=1) if i % step == 0]


def select_rebalance_dates(
    dates: Sequence[Any],
    regime_labels: Sequence[str],
    frequency: str | None = "monthly",
) -> list[pd.Timestamp]:
    """Select dates triggered by first observation, time cadence, or regime changes."""
    ordered = _to_timestamps(dates)
    labels = [str(label) for label in regime_labels]
    if len(ordered) != len(labels):
        raise ValueError("dates and regime_labels must have the same length")
    if not ordered:
        return []

    time_due = set(time_rebalance_dates(ordered, frequency))
    selected: list[pd.Timestamp] = []
    previous_label: str | None = None
    for date, label in zip(ordered, labels):
        is_first = previous_label is None
        regime_changed = previous_label is not None and label != previous_label
        if is_first or date in time_due or regime_changed:
            selected.append(date)
        previous_label = label
    return selected


def select_regime_rebalance_dates(
    dates: Sequence[Any],
    classifier: Any,
    data: Any,
    frequency: str | None = "monthly",
) -> list[pd.Timestamp]:
    """Select rebalance dates by querying a D-style regime classifier."""
    ordered = _to_timestamps(dates)
    labels = [str(classifier.predict(asof, data).label) for asof in ordered]
    return select_rebalance_dates(ordered, labels, frequency=frequency)
