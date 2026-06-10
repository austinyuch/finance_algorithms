"""A-1 共整合-反向篩選 — RED 階段測試。

對應 a-tsmc-hedge-slice/requirements.md / AC-A-01/02/03 / REQ-A-SCREEN-001/002 / REQ-A-DATA-001。
合成資料(strategy C:數字明知假、僅驗證管線):
  - TSMC:I(1) 隨機漫步
  - PLANT:= a - 0.5*TSMC + 平穩噪音 → 與 TSMC 共整合、hedge ratio<0(反向)
  - RAND :獨立隨機漫步 → 不共整合
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _synth():
    from quantlab.data.provider import InMemoryPITDataProvider

    rng = np.random.default_rng(42)
    n = 120
    dates = pd.date_range("2010-01-31", periods=n, freq="ME")
    tsmc = 100.0 + np.cumsum(rng.normal(0, 1, n))
    plant = 50.0 - 0.5 * tsmc + rng.normal(0, 0.5, n)     # 共整合 + 反向
    rand = 80.0 + np.cumsum(rng.normal(0, 1, n))          # 獨立隨機漫步
    rows = []
    for i, d in enumerate(dates):
        for sym, val in (("TSMC", tsmc[i]), ("PLANT", plant[i]), ("RAND", rand[i])):
            rows.append({"symbol": sym, "event_date": d, "available_date": d, "close": float(val)})
    prices = pd.DataFrame(rows)
    listings = pd.DataFrame([
        {"symbol": s, "list_date": pd.Timestamp("2009-01-01"), "delist_date": pd.NaT}
        for s in ("TSMC", "PLANT", "RAND")])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    return InMemoryPITDataProvider(prices, listings, macro), dates


# --- AC-A-01:找出 planted 共整合-反向候選,排除隨機 ---

def test_screen_finds_planted_cointegrated_reverse():
    from quantlab.research.screen import screen_cointegration_hedge

    data, dates = _synth()
    res = screen_cointegration_hedge(data, dates[-1], "TSMC", ["PLANT", "RAND"], adf_pmax=0.05)
    syms = [r["symbol"] for r in res]
    assert "PLANT" in syms                       # 共整合 + 反向 → 入選
    assert "RAND" not in syms                    # 獨立隨機漫步 → 不入選
    plant = next(r for r in res if r["symbol"] == "PLANT")
    assert plant["hedge_ratio"] < 0              # 反向
    assert plant["adf_p"] < 0.05                 # 共整合
    # 依 ADF p 升冪排名
    assert [r["adf_p"] for r in res] == sorted(r["adf_p"] for r in res)


# --- AC-A-02 / REQ-A-DATA-001:history() 為 point-in-time ---

def test_history_is_point_in_time():
    from quantlab.data.provider import InMemoryPITDataProvider

    ts = pd.Timestamp
    prices = pd.DataFrame([
        {"symbol": "A", "event_date": ts("2020-01-31"), "available_date": ts("2020-01-31"), "close": 10.0},
        {"symbol": "A", "event_date": ts("2020-02-29"), "available_date": ts("2020-02-29"), "close": 11.0},
        {"symbol": "A", "event_date": ts("2020-03-31"), "available_date": ts("2020-03-31"), "close": 12.0},
    ])
    listings = pd.DataFrame([{"symbol": "A", "list_date": ts("2019-01-01"), "delist_date": pd.NaT}])
    macro = pd.DataFrame(columns=["series", "event_date", "available_date", "value"])
    data = InMemoryPITDataProvider(prices, listings, macro)

    hist = data.history(ts("2020-02-29"), "close", ["A"])
    assert list(hist.index) == [ts("2020-01-31"), ts("2020-02-29")]   # 3 月未來資料被擋
    assert list(hist["A"]) == [10.0, 11.0]


# --- AC-A-03 / REQ-A-SCREEN-002:平行篩選 == 序列篩選 ---

def test_screen_parallel_equals_sequential():
    from quantlab.parallel import JoblibExecutor, seed_jobs
    from quantlab.research.screen import screen_one_candidate

    data, dates = _synth()
    cands = ["PLANT", "RAND"]
    jobs = [{"data": data, "asof": dates[-1], "target": "TSMC", "candidate": c, "adf_pmax": 0.05}
            for c in cands]
    par = JoblibExecutor(n_jobs=2).map(screen_one_candidate, jobs, seed=0)
    seq = [screen_one_candidate(j) for j in seed_jobs(jobs, 0)]
    assert par == seq
