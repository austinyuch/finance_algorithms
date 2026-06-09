"""交易成本模型(REQ-A0-BT-003)。

第一切片:以「周轉率 × 交易型成本(手續費 + 滑價 + 台股證交稅)」計算單次再平衡成本
(以總組合比例計)。不變量:所有成本參數為 0 → 成本為 0(AC-A0-03 / PBT-1)。

說明(誠實標註的 first-slice 限制):
  - 美股股息預扣(us_dividend_withholding_pct)與換匯點差(fx_spread_bps)屬「配息 / 跨幣事件」
    型成本,非周轉型;toy 資料未含配息/跨幣,故此版本不在 trading_cost 內計入,
    待 Epic B 接真實配息/匯率事件時補上。
"""
from __future__ import annotations

from typing import Mapping


def trading_cost(turnover: float, cost_config: Mapping[str, float]) -> float:
    """單次再平衡的交易成本(以組合比例表示)。

    turnover:該次再平衡的周轉率(Σ|Δweight|,1.0 = 100% 換手)。
    """
    bps = (
        float(cost_config.get("commission_bps", 0))
        + float(cost_config.get("slippage_bps", 0))
        + float(cost_config.get("tw_transaction_tax_bps", 0))
    )
    return max(0.0, float(turnover)) * bps / 10_000.0
