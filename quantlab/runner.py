"""整合膠層:把 strategy + data + config 串成回測,並可寫入 ResultStore。

run_backtest_job 為 module-level(可被 joblib pickling),供 Tier1 平行 sweep 使用。
⚠️ 框架隔離:本模組不得 import torch/tensorflow/jax。
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from quantlab.engine import VectorizedEngine


def run_backtest_job(job: Mapping[str, Any]) -> dict:
    """執行單一回測 job(含 strategy/data/config);供平行 executor 呼叫。"""
    return VectorizedEngine().run(job["strategy"], job["data"], job["config"])


def run_and_log(strategy: Any, data: Any, config: Mapping[str, Any], store: Any) -> tuple[str, dict]:
    """跑回測 → 寫入 store → 回 (run_id, result)。"""
    result = VectorizedEngine().run(strategy, data, config)
    run_id = store.log(result)
    return run_id, result


def run_hedge_slice(data: Any, config: Mapping[str, Any], store: Any, *,
                    target: str, candidates: Sequence[str], hedge_fraction: float = 0.3) -> list[dict]:
    """反台積電對衝 thin slice 編排:HedgeStrategy + 笨 baselines 全鏈 → leaderboard。

    baselines = buy&hold(target)、等權(target+candidates)、隨機(seeded)。
    回傳 store.leaderboard()(依 OOS-net Sharpe 排序)。
    """
    from quantlab.strategies import (
        BuyAndHold, HedgeStrategy, RandomStrategy, StaticWeights,
    )

    universe = [target] + list(candidates)
    seed = int(config.get("seed", 0))
    strategies = [
        HedgeStrategy(target, candidates, hedge_fraction),
        BuyAndHold([target]),
        StaticWeights({s: 1.0 for s in universe}),
        RandomStrategy(universe, seed=seed),
    ]
    for strat in strategies:
        run_and_log(strat, data, config, store)
    return store.leaderboard()
