"""C-4 金字塔進場整合 — RED 階段測試。

對應 c-portfolio-core REQ-C-PYRAMID-001。
組合最佳化決定各資產權重 → 預算 = 權重×總預算 → 各資產用既有 algo_pyramid 左側分批進場。
敘事閉環:單標的金字塔計算器 → 多資產組合系統。additive,不改既有金字塔。
"""
from __future__ import annotations

import pytest

WEIGHTS = {"A": 0.6, "B": 0.4}
TOTAL = 100_000.0
PLANS = {
    "A": {"price_init": 130.0, "price_final": 80.0, "times": 10, "min_increment": 1.0, "param": 2.0},
    "B": {"price_init": 50.0, "price_final": 30.0, "times": 8, "min_increment": 1.0, "param": 1.5},
}


def test_allocate_budget_by_weight_and_pyramid_entry():
    from quantlab.portfolio.pyramid import allocate_with_pyramid_entry

    out = allocate_with_pyramid_entry(WEIGHTS, TOTAL, PLANS, method="arithmetic")
    assert out["A"]["budget"] == pytest.approx(60_000.0)         # 權重×總預算
    assert out["B"]["budget"] == pytest.approx(40_000.0)
    # 各資產金字塔總投入金額 ≈ 該資產預算(金字塔依預算縮放;單位取整有小誤差)
    assert out["A"]["pyramid"]["總投入金額"] == pytest.approx(60_000.0, rel=0.05)
    assert out["B"]["pyramid"]["總投入金額"] == pytest.approx(40_000.0, rel=0.05)
    # 金字塔結構完整
    assert len(out["A"]["pyramid"]["各階資料"]) == 10
    assert out["A"]["pyramid"]["平均成本"] > 0


def test_geometric_method_and_zero_weight():
    from quantlab.portfolio.pyramid import allocate_with_pyramid_entry

    out = allocate_with_pyramid_entry({"A": 1.0, "B": 0.0}, TOTAL, PLANS, method="geometric")
    assert out["A"]["pyramid"]["總投入金額"] == pytest.approx(100_000.0, rel=0.05)
    assert out["B"]["pyramid"] is None                           # 0 權重 → 不進場
    assert out["B"]["budget"] == 0.0
