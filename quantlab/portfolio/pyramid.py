"""組合預算 → algo_pyramid 進場 adapter(REQ-C-PYRAMID-001)。

敘事閉環:組合最佳化(C-1)決定各資產權重 → 預算 = 權重×總預算 → 各資產用既有
invest_algorithms.algo_pyramid 的等差/等比金字塔做左側分批進場。

⚠️ **additive adapter,不改既有金字塔模組**;僅呼叫其 public 函式。
"""
from __future__ import annotations

from typing import Any, Mapping

from invest_algorithms import algo_pyramid


def allocate_with_pyramid_entry(weights: Mapping[str, float], total_budget: float,
                                asset_plans: Mapping[str, Mapping[str, Any]],
                                method: str = "arithmetic") -> dict:
    """回 {sym: {"budget": w×total, "pyramid": <金字塔下單資料 dict 或 None>}}。

    asset_plans[sym] 需含:price_init, price_final, times, min_increment, param,(可選)init_units。
    method: "arithmetic"(等差)或 "geometric"(等比)。權重 0 → pyramid=None(不進場)。
    """
    build = (algo_pyramid.get買入等差金字塔 if method == "arithmetic"
             else algo_pyramid.get買入等比金字塔)
    out: dict = {}
    for sym, w in weights.items():
        budget = float(w) * float(total_budget)
        if budget <= 0:
            out[sym] = {"budget": budget, "pyramid": None}
            continue
        ap = asset_plans[sym]
        plan = build(budget, ap["price_init"], ap["price_final"], ap["times"],
                     ap["min_increment"], ap["param"], ap.get("init_units", 1.0))
        out[sym] = {"budget": budget, "pyramid": plan}
    return out
