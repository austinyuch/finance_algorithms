"""A0-2 向量化回測引擎 + 成本模型 — RED 階段測試。

對應 tasks.md A0-2 / REQ-A0-BT-001..006 / AC-A0-03 / PBT-1/5/6 / FMEA-A0-03/06。
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# --- 玩具 fixture:單一標的 X,月收盤 100→110→121(每月 +10%) ---

def _toy_engine_data():
    from quantlab.data.provider import InMemoryPITDataProvider

    ts = pd.Timestamp
    prices = pd.DataFrame(
        [
            {"symbol": "X", "event_date": ts("2020-01-31"), "available_date": ts("2020-01-31"), "close": 100.0},
            {"symbol": "X", "event_date": ts("2020-02-29"), "available_date": ts("2020-02-29"), "close": 110.0},
            {"symbol": "X", "event_date": ts("2020-03-31"), "available_date": ts("2020-03-31"), "close": 121.0},
        ]
    )
    listings = pd.DataFrame([{"symbol": "X", "list_date": ts("2019-01-01"), "delist_date": pd.NaT}])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro)


def _base_config(mode="gross", costs_zero=True):
    cc = {"commission_bps": 0, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
          "us_dividend_withholding_pct": 0, "fx_spread_bps": 0}
    if not costs_zero:
        cc = {"commission_bps": 10, "slippage_bps": 5, "tw_transaction_tax_bps": 30,
              "us_dividend_withholding_pct": 0, "fx_spread_bps": 0}
    return {
        "start": "2020-01-31", "end": "2020-03-31", "rebalance": "monthly",
        "fill": "same_close", "mode": mode, "cost_config": cc,
        "seed": 0, "data_version": "toy",
        "walk_forward": {"train_window_months": 1, "test_window_months": 1, "step_months": 1},
    }


def _full_metric(result):
    fulls = [m for m in result["metrics"] if m["segment"] == "full"]
    assert fulls, "結果必須含 full segment 指標"
    return fulls[0]


# --- AC(玩具對拍):buy-and-hold X 的指標 = 已知解析解 ---

def test_toy_buyandhold_metrics_match_analytic():
    from quantlab.engine import VectorizedEngine
    from quantlab.strategies import BuyAndHold

    res = VectorizedEngine().run(BuyAndHold(["X"]), _toy_engine_data(), _base_config())
    m = _full_metric(res)
    assert m["cumulative_return"] == pytest.approx(0.21, abs=1e-9)   # 1.1*1.1-1
    assert m["max_drawdown"] == pytest.approx(0.0, abs=1e-12)        # 單調上升
    assert m["annualized_vol"] == pytest.approx(0.0, abs=1e-12)      # 兩期報酬相同
    assert m["turnover"] == pytest.approx(1.0, abs=1e-9)             # 僅初始建倉


# --- AC-A0-03 / PBT-1:cost=0 → net==gross;有成本+周轉 → net<gross ---

def test_cost_zero_net_equals_gross():
    from quantlab.engine import VectorizedEngine
    from quantlab.strategies import BuyAndHold

    data = _toy_engine_data()
    gross = _full_metric(VectorizedEngine().run(BuyAndHold(["X"]), data, _base_config(mode="gross")))
    net0 = _full_metric(VectorizedEngine().run(BuyAndHold(["X"]), data, _base_config(mode="net", costs_zero=True)))
    assert net0["cumulative_return"] == pytest.approx(gross["cumulative_return"], abs=1e-12)

    net = _full_metric(VectorizedEngine().run(BuyAndHold(["X"]), data, _base_config(mode="net", costs_zero=False)))
    assert net["cumulative_return"] < gross["cumulative_return"]      # 有成本+建倉周轉 → 較低


# 現實尺度(排除 subnormal 與浮點下溢角落):bps 不可能是 1e-311
_REAL = dict(allow_subnormal=False, allow_nan=False, allow_infinity=False)


@given(turnover=st.floats(min_value=0, max_value=5, **_REAL),
       commission=st.floats(min_value=0, max_value=100, **_REAL),
       tax=st.floats(min_value=0, max_value=100, **_REAL))
def test_pbt1_trading_cost_nonneg_and_zero_iff_no_params(turnover, commission, tax):
    from quantlab.costs import trading_cost

    zero = trading_cost(turnover, {"commission_bps": 0, "slippage_bps": 0,
                                   "tw_transaction_tax_bps": 0, "us_dividend_withholding_pct": 0,
                                   "fx_spread_bps": 0})
    assert zero == 0.0                                               # 全 0 參數 → 成本 0
    cost = trading_cost(turnover, {"commission_bps": commission, "slippage_bps": 0,
                                   "tw_transaction_tax_bps": tax, "us_dividend_withholding_pct": 0,
                                   "fx_spread_bps": 0})
    assert cost >= 0.0
    # 現實尺度(>= 1e-3 bp / 周轉)下,正輸入 → 嚴格正成本(避開浮點下溢角落)
    if turnover > 1e-3 and (commission > 1e-3 or tax > 1e-3):
        assert cost > 0.0


# --- PBT-5:指標健全性(任意報酬序列) ---

@settings(max_examples=50)
@given(rets=st.lists(st.floats(min_value=-0.5, max_value=0.5, allow_nan=False), min_size=2, max_size=40),
       turnover=st.floats(min_value=0, max_value=10))
def test_pbt5_metrics_sanity(rets, turnover):
    from quantlab.engine.metrics import compute_metrics

    m = compute_metrics(pd.Series(rets), turnover=turnover, periods_per_year=12,
                        basis="gross", segment="full")
    assert m["annualized_vol"] >= 0.0
    assert m["max_drawdown"] <= 0.0
    assert m["turnover"] >= 0.0


# --- PBT-6:walk-forward 訓練窗結束 < 測試窗開始(無重疊) ---

@settings(max_examples=50)
@given(train_m=st.integers(1, 24), test_m=st.integers(1, 24), step_m=st.integers(1, 24),
       n_months=st.integers(6, 60))
def test_pbt6_walkforward_no_overlap(train_m, test_m, step_m, n_months):
    from quantlab.engine.walkforward import walk_forward_splits

    dates = pd.date_range("2015-01-31", periods=n_months, freq="ME").tolist()
    for train, test in walk_forward_splits(dates, train_m, test_m, step_m):
        if train and test:
            assert max(train) < min(test)


# --- event_driven 引擎為預留 stub ---

def test_event_driven_not_implemented():
    from quantlab.engine import VectorizedEngine
    from quantlab.strategies import BuyAndHold

    cfg = _base_config()
    cfg["engine"] = "event_driven"
    with pytest.raises(NotImplementedError):
        VectorizedEngine().run(BuyAndHold(["X"]), _toy_engine_data(), cfg)
