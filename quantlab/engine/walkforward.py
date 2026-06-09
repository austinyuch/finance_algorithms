"""Walk-forward 切分(REQ-A0-BT-004 / FMEA-A0-06)。

不變量:每個 split 的訓練窗結束 < 測試窗開始(無重疊洩漏,PBT-6)。
⚠️ 框架隔離:不得 import torch/tensorflow/jax。
"""
from __future__ import annotations

from typing import Sequence

import pandas as pd


def walk_forward_splits(dates: Sequence, train_m: int, test_m: int, step_m: int):
    """回傳 [(train_dates, test_dates), ...]。train/test 以月窗切,test 緊接 train 之後(不重疊)。"""
    ds = sorted(pd.Timestamp(d) for d in dates)
    if not ds:
        return []
    end = ds[-1]
    splits: list[tuple[list, list]] = []
    cursor = ds[0]
    while True:
        train_end = cursor + pd.DateOffset(months=train_m)   # train: [cursor, train_end)
        test_start = train_end
        test_end = test_start + pd.DateOffset(months=test_m)  # test: [test_start, test_end)
        if test_start > end:
            break
        train = [d for d in ds if cursor <= d < train_end]
        test = [d for d in ds if test_start <= d < test_end]
        splits.append((train, test))
        cursor = cursor + pd.DateOffset(months=step_m)
        if cursor > end:
            break
    return splits
