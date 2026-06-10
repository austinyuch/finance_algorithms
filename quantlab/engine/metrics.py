"""績效指標(REQ-A0-BT-005)。明確標示 basis(gross/net)與 segment(IS/OOS/full)。

⚠️ 框架隔離:不得 import torch/tensorflow/jax。
"""
from __future__ import annotations

import pandas as pd


def compute_metrics(returns: pd.Series, turnover: float, periods_per_year: float,
                    basis: str, segment: str) -> dict:
    r = pd.Series(list(returns), dtype="float64")
    n = int(r.shape[0])

    if n == 0:
        return {"cumulative_return": 0.0, "annualized_return": 0.0, "annualized_vol": 0.0,
                "max_drawdown": 0.0, "sharpe": 0.0, "turnover": float(turnover),
                "basis": basis, "segment": segment}

    wealth = (1.0 + r).cumprod()
    final = float(wealth.iloc[-1])
    cumulative = final - 1.0
    # 防護:總資產歸零/翻負(極端虧損或無效資料)→ 視為 -100%,避免負底分數冪變複數
    annualized_return = -1.0 if final <= 0 else float(final ** (periods_per_year / n) - 1.0)

    std = float(r.std(ddof=1)) if n >= 2 else 0.0
    annualized_vol = std * (periods_per_year ** 0.5)

    dd = wealth / wealth.cummax() - 1.0
    max_drawdown = float(dd.min())
    if max_drawdown > 0.0:           # 數值保險(理論上 dd <= 0)
        max_drawdown = 0.0

    sharpe = float(r.mean() / std * (periods_per_year ** 0.5)) if std > 0 else 0.0

    return {"cumulative_return": cumulative, "annualized_return": annualized_return,
            "annualized_vol": annualized_vol, "max_drawdown": max_drawdown,
            "sharpe": sharpe, "turnover": float(turnover), "basis": basis, "segment": segment}
