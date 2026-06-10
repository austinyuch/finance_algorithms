"""LSTMStrategy — PyTorch LSTM 市場擇時訊號(REQ-A-LSTM-001)。

相容 A0 Strategy Protocol。PIT 懶訓練:首次取得足夠 PIT 歷史時於 CPU 訓練一個小 LSTM
(回歸下一期報酬),之後以最新視窗預測;預測為正 → 持有 target,否則轉現金({})。
給定 seed 完全可重現(CPU + manual_seed + 不洗牌)。

⚠️ torch 僅存在於本策略層;回測核心(engine/data)不得 import torch(NFR-A0-FWAGN-001)。
第一切片:單次訓練於首個足量視窗,週期性重訓為後續精修。
"""
from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import torch
import torch.nn as nn

_DEVICE = torch.device("cpu")   # 強制 CPU:確定性、避免 GPU 非確定性


class _Net(nn.Module):
    def __init__(self, hidden: int) -> None:
        super().__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=hidden, batch_first=True)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :])


class LSTMStrategy:
    def __init__(self, target: str, seed: int = 0, window: int = 12,
                 hidden: int = 8, epochs: int = 40, min_train: int = 48) -> None:
        self._target = target
        self._seed = int(seed)
        self._window = int(window)
        self._hidden = int(hidden)
        self._epochs = int(epochs)
        self._min_train = int(min_train)
        self._model: _Net | None = None

    def fit(self, train: Any = None, **kwargs: Any) -> None:
        return None   # 懶訓練於 generate_signal

    def _build_xy(self, prices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        rets = np.diff(prices) / prices[:-1]
        xs, ys = [], []
        for i in range(len(rets) - self._window):
            xs.append(rets[i:i + self._window])
            ys.append(rets[i + self._window])
        x = np.asarray(xs, dtype="float32")[:, :, None]
        y = np.asarray(ys, dtype="float32")[:, None]
        return x, y

    def _train(self, prices: np.ndarray) -> _Net | None:
        torch.manual_seed(self._seed)                    # 確定性:init + 訓練
        x, y = self._build_xy(prices)
        if len(x) < 5:
            return None
        xt = torch.tensor(x, device=_DEVICE)
        yt = torch.tensor(y, device=_DEVICE)
        net = _Net(self._hidden).to(_DEVICE)
        opt = torch.optim.Adam(net.parameters(), lr=0.01)
        loss_fn = nn.MSELoss()
        net.train()
        for _ in range(self._epochs):
            opt.zero_grad()
            loss_fn(net(xt), yt).backward()
            opt.step()
        net.eval()
        return net

    def generate_signal(self, asof: Any, data: Any) -> Mapping[str, float]:
        hist = data.history(asof, "close", [self._target]).dropna()
        prices = hist[self._target].to_numpy(dtype="float64")
        if len(prices) < self._min_train:
            return {self._target: 1.0}                   # 資料不足 → 預設持有
        if self._model is None:
            self._model = self._train(prices)
        if self._model is None:
            return {self._target: 1.0}
        rets = np.diff(prices) / prices[:-1]
        window = rets[-self._window:].astype("float32")
        with torch.no_grad():
            x = torch.tensor(window, device=_DEVICE)[None, :, None]
            pred = float(self._model(x).item())
        return {self._target: 1.0} if pred > 0 else {}   # 預測漲→持有,否則現金

    @property
    def metadata(self) -> Mapping[str, Any]:
        return {"name": "LSTMStrategy", "framework": "pytorch",
                "seed": self._seed, "window": self._window, "hidden": self._hidden}
