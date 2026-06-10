"""共整合-反向篩選(REQ-A-SCREEN-001/002)。

「反台積電 / 反指標」定義(使用者選):候選須與 target **共整合**(Engle-Granger:
OLS hedge ratio + 殘差 ADF 平穩)**且 hedge ratio < 0**(反向 spread)。
全程 point-in-time:只用 data.history(asof) 的 available_date<=asof 歷史。

screen_one_candidate 為 module-level(可 joblib pickling),供 Tier1 平行 sweep。
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np
from statsmodels.tsa.stattools import adfuller


def _engle_granger(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """OLS y ~ a + b·x;回 (hedge_ratio=b, 殘差 ADF p-value)。"""
    b, a = np.polyfit(x, y, 1)
    resid = y - (b * x + a)
    adf_p = float(adfuller(resid, autolag="AIC")[1])
    return float(b), adf_p


def screen_one_candidate(job: Mapping[str, Any]) -> dict:
    """單一候選的共整合-反向檢定(供平行 executor 呼叫)。"""
    data = job["data"]
    asof = job["asof"]
    target = job["target"]
    cand = job["candidate"]
    pmax = job["adf_pmax"]

    hist = data.history(asof, "close", [target, cand]).dropna()
    x = hist[target].to_numpy(dtype="float64")
    y = hist[cand].to_numpy(dtype="float64")
    hedge_ratio, adf_p = _engle_granger(x, y)
    cointegrated = adf_p < pmax
    reverse = hedge_ratio < 0
    return {"symbol": cand, "hedge_ratio": hedge_ratio, "adf_p": adf_p,
            "cointegrated": bool(cointegrated), "reverse": bool(reverse),
            "selected": bool(cointegrated and reverse)}


def screen_cointegration_hedge(data: Any, asof: Any, target: str,
                               candidates: Sequence[str], adf_pmax: float = 0.05) -> list[dict]:
    """回傳通過(共整合 且 反向)的候選,依 ADF p 升冪排名。"""
    selected = []
    for c in candidates:
        r = screen_one_candidate({"data": data, "asof": asof, "target": target,
                                  "candidate": c, "adf_pmax": adf_pmax})
        if r["selected"]:
            selected.append({"symbol": r["symbol"], "hedge_ratio": r["hedge_ratio"],
                             "adf_p": r["adf_p"]})
    return sorted(selected, key=lambda r: r["adf_p"])
