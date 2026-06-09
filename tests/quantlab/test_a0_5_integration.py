"""A0-5 端到端整合 — RED 階段測試。

對應 tasks.md A0-5 / AC-A0-01..07 整合驗證。
全鏈:data(PIT)→ engine(向量化)→ tracking(LocalResultStore)→ leaderboard;
另含端到端 lookahead 防護、重現性、平行一致。
"""
from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from quantlab.data.provider import InMemoryPITDataProvider
from quantlab.strategies import BuyAndHold


def _toy(prices_path=(100.0, 110.0, 99.0, 121.0)):
    """非單調價格 → vol>0、Sharpe 有意義。"""
    ts = pd.Timestamp
    dates = [ts("2020-01-31"), ts("2020-02-29"), ts("2020-03-31"), ts("2020-04-30")]
    prices = pd.DataFrame([
        {"symbol": "X", "event_date": d, "available_date": d, "close": p}
        for d, p in zip(dates, prices_path)
    ])
    listings = pd.DataFrame([{"symbol": "X", "list_date": ts("2019-01-01"), "delist_date": pd.NaT}])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro)


def _cfg(mode="net", cost=5):
    return {"start": "2020-01-31", "end": "2020-04-30", "rebalance": "monthly",
            "fill": "same_close", "mode": mode,
            "cost_config": {"commission_bps": cost, "slippage_bps": 0, "tw_transaction_tax_bps": 0,
                            "us_dividend_withholding_pct": 0, "fx_spread_bps": 0},
            "seed": 7, "data_version": "toy",
            "walk_forward": {"train_window_months": 1, "test_window_months": 1, "step_months": 1}}


def _oos_net(result):
    for m in result["metrics"]:
        if m["segment"] == "out_of_sample" and m["basis"] == "net":
            return m["sharpe"]
    return None


class _Cash:
    """空持有策略(全現金):generate_signal 回 {}。"""
    def fit(self, train=None, **k): return None
    def generate_signal(self, asof, data=None): return {}
    @property
    def metadata(self): return {"name": "Cash", "framework": "none"}


# --- 全鏈 happy path:data→engine→tracking→leaderboard ---

def test_end_to_end_happy_path(tmp_path):
    from quantlab.runner import run_and_log
    from quantlab.tracking import LocalResultStore

    store = LocalResultStore(tmp_path / "s.db")
    data = _toy()
    rid_bh, res_bh = run_and_log(BuyAndHold(["X"]), data, _cfg(), store)
    rid_cash, res_cash = run_and_log(_Cash(), data, _cfg(), store)

    board = store.leaderboard()
    assert len(board) == 2
    # 依 oos_net_sharpe 由高到低(None 視為最低,排末)
    vals = [(-1e18 if r["oos_net_sharpe"] is None else r["oos_net_sharpe"]) for r in board]
    assert vals == sorted(vals, reverse=True)
    # 每列可追溯回完整 record
    for row in board:
        assert store.get(row["run_id"])["strategy_name"] == row["strategy_name"]


# --- 端到端 lookahead 防護:策略在 t 只看得到 available_date <= t ---

def test_end_to_end_no_lookahead():
    from quantlab.engine import VectorizedEngine

    seen: list = []

    class _Peek:
        def fit(self, train=None, **k): return None
        def generate_signal(self, asof, data):
            df = data.get(asof, ["close"], data.universe(asof))
            seen.extend([(asof, ad) for ad in df["available_date"]])
            u = data.universe(asof)
            w = 1.0 / len(u) if u else 0.0
            return {s: w for s in u}
        @property
        def metadata(self): return {"name": "Peek", "framework": "none"}

    VectorizedEngine().run(_Peek(), _toy(), _cfg())
    assert seen, "策略應在每個再平衡日查過資料"
    assert all(available <= asof for asof, available in seen)   # 永不看見未來資料


# --- 端到端重現性:全鏈跑兩次,指標一致 ---

def test_end_to_end_reproducible(tmp_path):
    from quantlab.runner import run_and_log
    from quantlab.tracking import LocalResultStore

    store = LocalResultStore(tmp_path / "s.db")
    data = _toy()
    rid1, _ = run_and_log(BuyAndHold(["X"]), data, _cfg(), store)
    rid2, _ = run_and_log(BuyAndHold(["X"]), data, _cfg(), store)
    assert store.get(rid1)["metrics"] == store.get(rid2)["metrics"]


# --- 端到端平行一致:sweep 平行 == 序列 ---

@settings(max_examples=10, deadline=None)
@given(costs=st.lists(st.integers(0, 50), min_size=1, max_size=4))
def test_end_to_end_parallel_equals_sequential(costs):
    from quantlab.parallel import JoblibExecutor, seed_jobs
    from quantlab.runner import run_backtest_job

    data = _toy()
    jobs = [{"strategy": BuyAndHold(["X"]), "data": data, "config": _cfg(cost=c)} for c in costs]
    par = JoblibExecutor(n_jobs=2).map(run_backtest_job, jobs, seed=0)
    seq = [run_backtest_job(j) for j in seed_jobs(jobs, 0)]
    assert [r["metrics"] for r in par] == [r["metrics"] for r in seq]
