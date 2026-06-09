"""JoblibExecutor — 平行 sweep 執行器(REQ-A0-PAR-001/002)。

母 seed 衍生確定性子 seed,確保平行與序列結果逐筆一致(determinism,PBT-4 / AC-A0-06)。
joblib 的 Parallel 保序回傳。介面對齊 quantlab.contracts.ParallelExecutor;Ray 預留不實作。
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from joblib import Parallel, delayed


def seed_jobs(jobs: Sequence[Mapping[str, Any]], seed: int) -> list[dict]:
    """為每個 job 注入確定性子 seed(母 seed + index);不破壞原 job。"""
    return [{**dict(job), "_seed": int(seed) + i} for i, job in enumerate(jobs)]


class JoblibExecutor:
    def __init__(self, n_jobs: int = -1, backend: str = "loky") -> None:
        self._n_jobs = n_jobs
        self._backend = backend

    def map(self, fn: Callable[[Mapping[str, Any]], Any],
            jobs: Sequence[Mapping[str, Any]], *, seed: int) -> list:
        seeded = seed_jobs(jobs, seed)
        if not seeded:
            return []
        return list(Parallel(n_jobs=self._n_jobs, backend=self._backend)(
            delayed(fn)(job) for job in seeded))
