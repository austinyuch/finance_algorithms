"""A0-4 Tier2 追蹤(LocalResultStore)— RED 階段測試。

對應 tasks.md A0-4 / REQ-A0-TRK-001/002/003 / AC-A0-07 / FMEA-A0-05 / PBT-3。
後端為 stdlib sqlite3(MLflow 因 Py3.13 依賴衝突延後,同 ResultStore Protocol 可插拔)。
"""
from __future__ import annotations

import pandas as pd
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


def _metric(segment, basis, sharpe):
    return {"cumulative_return": 0.0, "annualized_return": 0.0, "annualized_vol": 0.1,
            "max_drawdown": -0.1, "sharpe": sharpe, "turnover": 1.0,
            "basis": basis, "segment": segment}


def _record(name, oos_net_sharpe, run_id="", is_baseline=False, extra=None):
    metrics = [_metric("out_of_sample", "net", oos_net_sharpe)]
    if extra:
        metrics += extra
    return {"run_id": run_id, "strategy_name": name,
            "config": {"seed": 1, "data_version": "toy"},
            "metrics": metrics, "is_baseline": is_baseline}


def _store(tmp_path):
    from quantlab.tracking import LocalResultStore
    return LocalResultStore(tmp_path / "store.db")


# --- REQ-A0-TRK-001/003:log → get 往返(可重現設定) ---

def test_log_get_roundtrip(tmp_path):
    store = _store(tmp_path)
    rec = _record("BuyAndHold", 0.5)
    rid = store.log(rec)
    assert rid                                   # 回傳 run_id
    got = store.get(rid)
    assert got == {**rec, "run_id": rid}         # 完整往返(run_id 已填)


# --- REQ-A0-TRK-002 / AC-A0-07:leaderboard 依 OOS-net 排序、可追溯 ---

def test_leaderboard_sorted_by_oos_net_and_traceable(tmp_path):
    store = _store(tmp_path)
    rid_low = store.log(_record("low", 0.1))
    rid_high = store.log(_record("high", 0.9))
    rid_mid = store.log(_record("mid", 0.5))

    board = store.leaderboard()
    assert [r["run_id"] for r in board] == [rid_high, rid_mid, rid_low]   # 由高到低
    assert board[0]["strategy_name"] == "high"
    assert board[0]["oos_net_sharpe"] == pytest.approx(0.9)
    # 可追溯:每列 run_id 可 get 回完整 record
    assert store.get(board[0]["run_id"])["strategy_name"] == "high"


# --- FMEA-A0-05:leaderboard 只認 OOS+net,不被高 IS/full 灌水 ---

def test_leaderboard_ignores_non_oos_net_metrics(tmp_path):
    store = _store(tmp_path)
    # A:OOS-net 低(0.1)但 full-net Sharpe 灌到 9.9
    rid_a = store.log(_record("A_inflated", 0.1, extra=[_metric("full", "net", 9.9)]))
    # B:OOS-net 高(0.8)
    rid_b = store.log(_record("B_honest", 0.8))
    board = store.leaderboard()
    assert board[0]["run_id"] == rid_b          # 誠實的 B 勝出,A 的高 full 被忽略
    assert board[1]["run_id"] == rid_a


def test_leaderboard_rejects_unsupported_metric_instead_of_silent_fallback(tmp_path):
    store = _store(tmp_path)
    store.log(_record("honest", 0.8))

    with pytest.raises(ValueError, match="unsupported leaderboard metric"):
        store.leaderboard(metric="in_sample_sharpe")


def test_result_store_rejects_non_finite_oos_net_sharpe(tmp_path):
    store = _store(tmp_path)

    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError, match="finite oos_net_sharpe"):
            store.log(_record("bad", bad))


@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(sharpe=st.one_of(
    st.none(),
    st.text(min_size=0, max_size=6),
    st.floats(allow_nan=True, allow_infinity=True),
))
def test_pbt_result_store_only_accepts_finite_oos_net_sharpe(tmp_path, sharpe):
    store = _store(tmp_path)
    record = _record("maybe-bad", 0.1)
    record["metrics"][0]["sharpe"] = sharpe

    try:
        value = float(sharpe)  # type: ignore[arg-type]
        should_accept = value == value and value not in (float("inf"), float("-inf"))
    except (TypeError, ValueError):
        should_accept = False

    if should_accept:
        rid = store.log(record)
        assert store.get(rid)["metrics"][0]["sharpe"] == sharpe
    else:
        with pytest.raises(ValueError, match="finite oos_net_sharpe"):
            store.log(record)


# --- PBT-3:任意 seed → 引擎兩次 run 指標完全一致(可重現) ---

def _toy_data():
    from quantlab.data.provider import InMemoryPITDataProvider
    ts = pd.Timestamp
    prices = pd.DataFrame([
        {"symbol": "X", "event_date": ts("2020-01-31"), "available_date": ts("2020-01-31"), "close": 100.0},
        {"symbol": "X", "event_date": ts("2020-02-29"), "available_date": ts("2020-02-29"), "close": 110.0},
        {"symbol": "X", "event_date": ts("2020-03-31"), "available_date": ts("2020-03-31"), "close": 121.0},
    ])
    listings = pd.DataFrame([{"symbol": "X", "list_date": ts("2019-01-01"), "delist_date": pd.NaT}])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro)


@settings(max_examples=25, deadline=None)
@given(seed=st.integers(0, 100000))
def test_pbt3_engine_reproducible(seed):
    from quantlab.engine import VectorizedEngine
    from quantlab.strategies import BuyAndHold

    cfg = {"start": "2020-01-31", "end": "2020-03-31", "rebalance": "monthly",
           "fill": "same_close", "mode": "net",
           "cost_config": {"commission_bps": 5, "slippage_bps": 0, "tw_transaction_tax_bps": 30,
                           "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
           "seed": seed, "data_version": "toy",
           "walk_forward": {"train_window_months": 1, "test_window_months": 1, "step_months": 1}}
    data = _toy_data()
    r1 = VectorizedEngine().run(BuyAndHold(["X"]), data, cfg)
    r2 = VectorizedEngine().run(BuyAndHold(["X"]), data, cfg)
    assert r1["metrics"] == r2["metrics"]        # 同 config+seed → 指標 bit 一致
