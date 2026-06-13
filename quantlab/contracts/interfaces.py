"""A0 行為介面(框架無感 Protocol)。

⚠️ SSOT:.agents/specs/a0-backtest-foundation/contract/interfaces.py
此檔為可 import 的同步版本;兩者須一致(drift guard 由測試把關)。
回測核心(engine/data)**不得** import 任何 ML 框架(torch/tensorflow/jax)。
"""
from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    import pandas as pd  # noqa: F401

Timestamp = Any
Symbol = str


@runtime_checkable
class PointInTimeDataProvider(Protocol):
    """As-of 取數;絕不回傳 asof 之後才可得的資料。REQ-A0-PIT-001/002/003。"""

    def get(self, asof: Timestamp, fields: Sequence[str],
            symbols: Sequence[Symbol] | None = None) -> "pd.DataFrame": ...

    def universe(self, asof: Timestamp) -> Sequence[Symbol]: ...

    def macro(self, asof: Timestamp, series: str) -> float | None: ...


@runtime_checkable
class Strategy(Protocol):
    """框架無感策略/模型介面。REQ-A0-IFC-001/002。"""

    def fit(self, train: "pd.DataFrame", **kwargs: Any) -> None: ...

    def generate_signal(self, asof: Timestamp,
                        data: PointInTimeDataProvider) -> Mapping[Symbol, float]: ...

    @property
    def metadata(self) -> Mapping[str, Any]: ...


@runtime_checkable
class BacktestEngine(Protocol):
    """回測引擎。REQ-A0-BT-001..006。"""

    def run(self, strategy: Strategy, data: PointInTimeDataProvider,
            config: Mapping[str, Any]) -> Mapping[str, Any]: ...


@runtime_checkable
class ResultStore(Protocol):
    """Tier2 追蹤。REQ-A0-TRK-001/002/003。"""

    def log(self, record: Mapping[str, Any]) -> str: ...

    def leaderboard(self, metric: str = "oos_net_sharpe",
                    descending: bool = True) -> Sequence[Mapping[str, Any]]: ...

    def get(self, run_id: str) -> Mapping[str, Any]: ...


@runtime_checkable
class ParallelExecutor(Protocol):
    """Tier1 平行底座抽象。REQ-A0-PAR-001/002。"""

    def map(self, fn: Any, jobs: Sequence[Mapping[str, Any]], *,
            seed: int) -> Sequence[Mapping[str, Any]]: ...
