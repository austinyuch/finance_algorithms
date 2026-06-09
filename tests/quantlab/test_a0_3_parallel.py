"""A0-3 Tier1 平行底座 + 環境隔離 — RED 階段測試。

對應 tasks.md A0-3 / REQ-A0-PAR-001/002/003 / AC-A0-06 / PBT-4 / FMEA-A0-04。
"""
from __future__ import annotations

import importlib
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st


def _double(job: dict) -> dict:
    """module-level(可被 joblib pickling)的確定性函式。"""
    return {"r": job["x"] * 2 + job["_seed"]}


# --- PBT-4 / AC-A0-06:平行結果 == 序列結果(同母 seed) ---

@settings(max_examples=20, deadline=None)
@given(xs=st.lists(st.integers(-1000, 1000), min_size=0, max_size=6), seed=st.integers(0, 1000))
def test_pbt4_parallel_equals_sequential(xs, seed):
    from quantlab.parallel import JoblibExecutor, seed_jobs

    jobs = [{"x": x} for x in xs]
    par = list(JoblibExecutor(n_jobs=2).map(_double, jobs, seed=seed))
    seq = [_double(j) for j in seed_jobs(jobs, seed)]
    assert par == seq                      # 平行與序列逐筆一致、且保序


def test_seed_jobs_deterministic_child_seeds():
    from quantlab.parallel import seed_jobs

    jobs = [{"x": 1}, {"x": 2}, {"x": 3}]
    seeded = seed_jobs(jobs, 100)
    assert [j["_seed"] for j in seeded] == [100, 101, 102]   # 母 seed 衍生子 seed
    assert [j["x"] for j in seeded] == [1, 2, 3]             # 原 job 不被破壞


# --- REQ-A0-PAR-003:三框架環境隔離定義存在且互斥 ---

def test_env_isolation_definitions_exist_and_mutually_exclusive():
    envs = Path(importlib.import_module("quantlab").__file__).parent / "envs"
    framework = {"pytorch": "torch", "tensorflow": "tensorflow", "jax": "jax"}
    for key, fw in framework.items():
        path = envs / f"{key}.txt"
        assert path.exists(), f"缺少環境定義 {path}"
        text = path.read_text(encoding="utf-8").lower()
        assert fw in text, f"{key}.txt 須宣告自身框架 {fw}"
        for other_key, other_fw in framework.items():
            if other_key != key:
                assert other_fw not in text, f"{key}.txt 不應含他框架 {other_fw}(隔離)"
