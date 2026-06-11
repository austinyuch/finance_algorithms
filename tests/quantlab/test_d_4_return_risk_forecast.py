"""D-4 return/risk forecast model tests.

RED/GREEN/REFACTOR trace:
- RED: tests are added before `quantlab.models.return_risk` exists.
- GREEN: implement deterministic PIT forecast + allocation strategy.
- REFACTOR: keep behavior stable while clarifying degraded-status handling.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


def _provider_from_prices(prices_by_symbol: dict[str, list[float]], start: str = "2018-01-31"):
    from quantlab.data.provider import InMemoryPITDataProvider

    dates = pd.date_range(start, periods=len(next(iter(prices_by_symbol.values()))), freq="ME")
    rows = [
        {"symbol": sym, "event_date": date, "available_date": date, "close": float(value)}
        for sym, values in prices_by_symbol.items()
        for date, value in zip(dates, values)
    ]
    listings = pd.DataFrame(
        [{"symbol": sym, "list_date": pd.Timestamp("2017-01-01"), "delist_date": pd.NaT}
         for sym in prices_by_symbol]
    )
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(pd.DataFrame(rows), listings, macro), dates


def _synthetic_market(n: int = 72):
    growth = 100 * np.cumprod(np.full(n, 1.012))
    steady = 100 * np.cumprod(np.full(n, 1.003))
    return _provider_from_prices({"GROWTH": list(growth), "STEADY": list(steady)})


def _cfg(dates):
    return {
        "start": str(dates[0].date()),
        "end": str(dates[-1].date()),
        "rebalance": "monthly",
        "fill": "same_close",
        "mode": "net",
        "cost_config": {"commission_bps": 5, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
                        "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
        "seed": 0,
        "data_version": "synth-return-risk",
        "walk_forward": {"train_window_months": 36, "test_window_months": 12, "step_months": 12},
    }


def test_return_risk_forecaster_is_pit_safe_and_deterministic():
    from quantlab.models import ReturnRiskForecaster

    data, dates = _synthetic_market()
    forecaster = ReturnRiskForecaster(["GROWTH", "STEADY"], lookback=12, min_obs=6)

    early = forecaster.forecast(dates[20], data)
    late = forecaster.forecast(dates[-1], data)

    assert early == forecaster.forecast(dates[20], data)
    assert {f.symbol for f in late} == {"GROWTH", "STEADY"}
    assert all(f.status == "ok" for f in late)
    assert all(np.isfinite(f.expected_return) and np.isfinite(f.volatility) for f in late)
    assert early[0].expected_return == pytest.approx(late[0].expected_return)


def test_forecast_strategy_fallback_metadata_for_degraded_history():
    from quantlab.models import ForecastAllocationStrategy, ReturnRiskForecaster

    data, dates = _synthetic_market(n=5)
    strategy = ForecastAllocationStrategy(
        ReturnRiskForecaster(["GROWTH", "STEADY"], lookback=12, min_obs=6),
        vol_cap=0.30,
    )

    weights = strategy.generate_signal(dates[-1], data)

    assert weights == pytest.approx({"GROWTH": 0.5, "STEADY": 0.5})
    assert strategy.metadata["forecast_status"] == "degraded"
    assert strategy.metadata["claim_boundary"] == "no_alpha_claim"


@settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    a=st.lists(st.floats(min_value=1.001, max_value=1.05, allow_nan=False,
                         allow_infinity=False), min_size=18, max_size=48),
    b=st.lists(st.floats(min_value=1.001, max_value=1.05, allow_nan=False,
                         allow_infinity=False), min_size=18, max_size=48),
)
def test_pbt_forecast_weights_are_long_only_and_sum_to_one(a, b):
    from quantlab.models import ForecastAllocationStrategy, ReturnRiskForecaster

    n = min(len(a), len(b))
    prices = {
        "A": list(100 * np.cumprod(np.asarray(a[:n]))),
        "B": list(100 * np.cumprod(np.asarray(b[:n]))),
    }
    data, dates = _provider_from_prices(prices)
    strategy = ForecastAllocationStrategy(ReturnRiskForecaster(["A", "B"], lookback=12, min_obs=6))

    weights = strategy.generate_signal(dates[-1], data)

    assert set(weights) == {"A", "B"}
    assert all(np.isfinite(v) and v >= -1e-9 for v in weights.values())
    assert sum(weights.values()) == pytest.approx(1.0)


def test_return_risk_benchmark_logs_oos_baseline_and_no_alpha_claim(tmp_path):
    from quantlab.models import run_return_risk_forecast_benchmark
    from quantlab.tracking import LocalResultStore

    data, dates = _synthetic_market()
    store = LocalResultStore(tmp_path / "d2.sqlite")

    report = run_return_risk_forecast_benchmark(
        data,
        dates,
        store,
        symbols=["GROWTH", "STEADY"],
        config=_cfg(dates),
    )

    assert report["claim_boundary"] == "no_alpha_claim"
    assert {row["strategy_name"] for row in report["leaderboard"]} == {
        "ForecastAllocationStrategy",
        "StaticWeights",
    }
    assert all(row["oos_net_sharpe"] is not None for row in report["leaderboard"])
    assert report["forecast_run_id"]
    assert report["baseline_run_id"]
