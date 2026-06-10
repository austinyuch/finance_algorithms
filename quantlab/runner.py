"""整合膠層:把 strategy + data + config 串成回測,並可寫入 ResultStore。

run_backtest_job 為 module-level(可被 joblib pickling),供 Tier1 平行 sweep 使用。
⚠️ 框架隔離:本模組不得 import torch/tensorflow/jax。
"""
from __future__ import annotations

from typing import Any, Mapping

from quantlab.engine import VectorizedEngine


def run_backtest_job(job: Mapping[str, Any]) -> dict:
    """執行單一回測 job(含 strategy/data/config);供平行 executor 呼叫。"""
    return VectorizedEngine().run(job["strategy"], job["data"], job["config"])


def run_and_log(strategy: Any, data: Any, config: Mapping[str, Any], store: Any) -> tuple[str, dict]:
    """跑回測 → 寫入 store → 回 (run_id, result)。"""
    result = VectorizedEngine().run(strategy, data, config)
    run_id = store.log(result)
    return run_id, result
