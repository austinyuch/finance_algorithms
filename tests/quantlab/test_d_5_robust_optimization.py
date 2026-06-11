"""D-5 robust portfolio optimization model tests."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings, strategies as st


def _provider(prices_by_symbol: dict[str, list[float]], start: str = "2017-01-31"):
    from quantlab.data.provider import InMemoryPITDataProvider

    dates = pd.date_range(start, periods=len(next(iter(prices_by_symbol.values()))), freq="ME")
    rows = [
        {"symbol": sym, "event_date": date, "available_date": date, "close": float(value)}
        for sym, values in prices_by_symbol.items()
        for date, value in zip(dates, values)
    ]
    listings = pd.DataFrame(
        [{"symbol": sym, "list_date": pd.Timestamp("2016-01-01"), "delist_date": pd.NaT}
         for sym in prices_by_symbol]
    )
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(pd.DataFrame(rows), listings, macro), dates


def _market(n: int = 72):
    smooth = 100 * np.cumprod(np.full(n, 1.006))
    volatile = 100 * np.cumprod(np.resize(np.array([1.04, 0.94, 1.05, 0.96]), n))
    return _provider({"SMOOTH": list(smooth), "VOL": list(volatile)})


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
        "data_version": "synth-robust-optimization",
        "walk_forward": {"train_window_months": 36, "test_window_months": 12, "step_months": 12},
    }


def test_downside_penalty_does_not_increase_adjusted_return():
    from quantlab.models import RobustPortfolioModel

    data, dates = _market()
    low = RobustPortfolioModel(["SMOOTH", "VOL"], downside_penalty=0.0, min_obs=6).estimate(dates[-1], data)
    high = RobustPortfolioModel(["SMOOTH", "VOL"], downside_penalty=2.0, min_obs=6).estimate(dates[-1], data)

    low_by_symbol = {estimate.symbol: estimate.adjusted_return for estimate in low}
    high_by_symbol = {estimate.symbol: estimate.adjusted_return for estimate in high}
    assert high_by_symbol["VOL"] <= low_by_symbol["VOL"]
    assert all(estimate.status == "ok" for estimate in high)


def test_robust_strategy_degraded_history_falls_back_and_preserves_claim_boundary():
    from quantlab.models import RobustOptimizationStrategy, RobustPortfolioModel

    data, dates = _market(n=5)
    strategy = RobustOptimizationStrategy(RobustPortfolioModel(["SMOOTH", "VOL"], min_obs=12))

    weights = strategy.generate_signal(dates[-1], data)

    assert weights == pytest.approx({"SMOOTH": 0.5, "VOL": 0.5})
    assert strategy.metadata["robust_status"] == "degraded"
    assert strategy.metadata["claim_boundary"] == "no_alpha_claim"


@settings(max_examples=40, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    a=st.lists(st.floats(min_value=0.95, max_value=1.08, allow_nan=False,
                         allow_infinity=False), min_size=18, max_size=42),
    b=st.lists(st.floats(min_value=0.95, max_value=1.08, allow_nan=False,
                         allow_infinity=False), min_size=18, max_size=42),
)
def test_pbt_robust_weights_are_long_only_and_sum_to_one(a, b):
    from quantlab.models import RobustOptimizationStrategy, RobustPortfolioModel

    n = min(len(a), len(b))
    data, dates = _provider({
        "A": list(100 * np.cumprod(np.asarray(a[:n]))),
        "B": list(100 * np.cumprod(np.asarray(b[:n]))),
    })
    strategy = RobustOptimizationStrategy(RobustPortfolioModel(["A", "B"], min_obs=6))

    weights = strategy.generate_signal(dates[-1], data)

    assert set(weights) == {"A", "B"}
    assert all(np.isfinite(v) and v >= -1e-9 for v in weights.values())
    assert sum(weights.values()) == pytest.approx(1.0)


def test_robust_benchmark_logs_oos_baseline_and_no_alpha_claim(tmp_path):
    from quantlab.models import run_robust_optimization_benchmark
    from quantlab.tracking import LocalResultStore

    data, dates = _market()
    store = LocalResultStore(tmp_path / "d3.sqlite")

    report = run_robust_optimization_benchmark(
        data,
        dates,
        store,
        symbols=["SMOOTH", "VOL"],
        config=_cfg(dates),
    )

    assert report["claim_boundary"] == "no_alpha_claim"
    assert {row["strategy_name"] for row in report["leaderboard"]} == {
        "RobustOptimizationStrategy",
        "StaticWeights",
    }
    assert all(row["oos_net_sharpe"] is not None for row in report["leaderboard"])
