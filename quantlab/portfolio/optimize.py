"""組合最佳化(REQ-C-OPT-001)。

max wᵀμ s.t. sqrt(wᵀΣw) ≤ vol_cap、long-only、Σw=1(SLSQP)。
不可行(連最小波動都 > vol_cap)→ 回退最小波動組合(best-effort,不丟例外)。
maxDD 約束為 ex-post(路徑相依),不在此最佳化內(誠實,見 design FMEA-C-03)。

⚠️ 不得 import torch/tensorflow/jax(沿用 lab 慣例)。
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize


def _port_var(w: np.ndarray, cov: np.ndarray) -> float:
    return float(w @ cov @ w)


def _normalize(w: np.ndarray) -> np.ndarray:
    w = np.clip(np.asarray(w, dtype=float), 0.0, None)
    total = w.sum()
    return w / total if total > 0 else np.ones_like(w) / len(w)


def optimize_max_return_under_vol(mu, cov, vol_cap: float, w_max: float = 1.0) -> np.ndarray:
    mu = np.asarray(mu, dtype=float)
    cov = np.asarray(cov, dtype=float)
    n = len(mu)
    w0 = np.ones(n) / n
    bounds = [(0.0, w_max)] * n
    sum1 = {"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)}

    # 最小波動組合(不可行時的回退)
    minvol = minimize(lambda w: _port_var(w, cov), w0, method="SLSQP",
                      bounds=bounds, constraints=[sum1])
    w_minvol = _normalize(minvol.x)
    if np.sqrt(_port_var(w_minvol, cov)) > vol_cap:
        return w_minvol

    # 主問題:max wᵀμ s.t. 變異 ≤ vol_cap²(用變異避免 sqrt 在 0 不可微)
    var_con = {"type": "ineq", "fun": lambda w: float(vol_cap ** 2 - _port_var(w, cov))}
    res = minimize(lambda w: float(-(w @ mu)), w0, method="SLSQP",
                   bounds=bounds, constraints=[sum1, var_con])
    return _normalize(res.x)
