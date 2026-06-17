"""Real PyTorch realization of the reference MLP training (REQ-H2-TORCHTRAIN-001).

This is the `pytorch` backend for the deep forecaster (Epic H slice H-2). It trains the
*same* one-hidden-`tanh`-layer MLP as the framework-free reference
(`quantlab.models.dl_forecaster.NumpyMLPForecaster`), but the forward pass, the gradient,
and the parameter update are computed with **PyTorch autograd** rather than hand-written
numpy. To keep the real run reproducible and comparable, the weights are seed-initialised
from the *same* ``np.random.default_rng(seed)`` draw order as the reference and the math is
done in float64 — so the torch forecasts agree with the reference within the documented
``1e-3`` tolerance (see `design.md` §3) while the training itself is genuinely PyTorch.

Framework isolation: ``import torch`` is **lazy** (inside :func:`train_mlp_torch`), so
importing this module — or `quantlab.models.dl_forecaster` — never imports torch. The
backtest core (`quantlab.engine` / `quantlab.data`) never imports this module
(import-linter "DL backend boundary" contract). Output is `no_alpha_claim`.
"""
from __future__ import annotations

from typing import Any

import numpy as np


def train_mlp_torch(
    xs: np.ndarray,
    ys: np.ndarray,
    *,
    lookback: int,
    hidden: int,
    epochs: int,
    seed: int,
    lr: float,
) -> tuple[dict[str, np.ndarray], list[float]]:
    """Train the reference MLP with real PyTorch; return numpy weights + per-epoch loss.

    ``xs`` is the standardised lookback-window matrix ``(n, lookback)`` and ``ys`` the
    standardised next-return target ``(n, 1)`` — identical to what the reference trainer
    receives, so the returned weights drop into the shared numpy forward pass unchanged.

    The weights are initialised from ``np.random.default_rng(seed)`` in the exact draw
    order of the reference (``w1`` then ``w2``; biases zero), then trained by full-batch
    gradient descent in torch (``loss = mean(err**2)``, learning rate ``lr``). This keeps
    the torch run reproducible and within tolerance of the reference (parity, not a second
    model), while every forward/backward/update is computed by PyTorch.
    """
    import torch  # lazy: keeps the framework-isolation boundary intact

    # Identical seed-init to the reference (same rng, same draw order) → tight parity.
    rng = np.random.default_rng(seed)
    w1_0 = rng.standard_normal((lookback, hidden)) * 0.1
    w2_0 = rng.standard_normal((hidden, 1)) * 0.1

    dtype = torch.float64
    xs_t = torch.as_tensor(np.asarray(xs, dtype="float64"), dtype=dtype)
    ys_t = torch.as_tensor(np.asarray(ys, dtype="float64"), dtype=dtype)

    torch.manual_seed(int(seed))  # belt-and-braces; init is already deterministic above
    w1 = torch.tensor(w1_0, dtype=dtype, requires_grad=True)
    b1 = torch.zeros((1, hidden), dtype=dtype, requires_grad=True)
    w2 = torch.tensor(w2_0, dtype=dtype, requires_grad=True)
    b2 = torch.zeros((1, 1), dtype=dtype, requires_grad=True)
    params = [w1, b1, w2, b2]

    trace: list[float] = []
    for _ in range(int(epochs)):
        hidden_act = torch.tanh(xs_t @ w1 + b1)
        out = hidden_act @ w2 + b2
        loss = torch.mean((out - ys_t) ** 2)
        # Record the loss BEFORE the update, matching the reference trace semantics.
        trace.append(float(loss.item()))
        for p in params:
            if p.grad is not None:
                p.grad = None
        loss.backward()
        with torch.no_grad():
            for p in params:
                assert p.grad is not None  # full-batch loss depends on every param
                p -= lr * p.grad

    weights: dict[str, np.ndarray] = {
        "w1": w1.detach().cpu().numpy(),
        "b1": b1.detach().cpu().numpy(),
        "w2": w2.detach().cpu().numpy(),
        "b2": b2.detach().cpu().numpy(),
    }
    return weights, trace


__all__ = ["train_mlp_torch"]
