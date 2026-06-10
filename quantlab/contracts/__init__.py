"""Contracts:行為 Protocol(interfaces)+ 由 JSON Schema codegen 的資料 models。

資料 models 的 SSOT = .agents/specs/a0-backtest-foundation/contract/schemas/*.json
(經 datamodel-codegen 生成於 _generated/,**禁手寫基礎型別**)。
"""
from quantlab.contracts._generated.backtest_config import BacktestConfig, WalkForward
from quantlab.contracts._generated.cost_config import CostConfig
from quantlab.contracts._generated.performance_metrics import PerformanceMetrics
from quantlab.contracts._generated.result_record import ResultRecord
from quantlab.contracts.interfaces import (
    BacktestEngine,
    ParallelExecutor,
    PointInTimeDataProvider,
    ResultStore,
    Strategy,
)

__all__ = [
    "Strategy",
    "PointInTimeDataProvider",
    "BacktestEngine",
    "ResultStore",
    "ParallelExecutor",
    "BacktestConfig",
    "WalkForward",
    "CostConfig",
    "PerformanceMetrics",
    "ResultRecord",
]
