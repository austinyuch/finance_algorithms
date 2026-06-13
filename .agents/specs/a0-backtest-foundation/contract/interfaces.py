"""A0 行為介面契約 (SSOT) — 框架無感。

此檔是 Epic A0 所有行為介面的單一真實來源。實作(Phase 4)必須遵守這些
Protocol;回測核心**不得** import 任何 ML 框架(torch/tensorflow/jax)。
資料模型(BacktestConfig / CostConfig / PerformanceMetrics / ResultRecord)的
SSOT 在 contract/schemas/*.json,對應 Pydantic models 由 schema 生成。

關聯需求:REQ-A0-IFC-001/002/003、REQ-A0-PIT-*、REQ-A0-BT-*、REQ-A0-TRK-*
"""
from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    # 僅型別檢查期引用,避免在契約層綁定具體資料庫/陣列實作。
    import pandas as pd  # noqa: F401

# --- 標準化輸出型別(框架無感:純資料,帶時間索引) ---
# Signal/Weight 以「時間索引 -> {symbol: float}」表達。實作可用 pandas.DataFrame,
# 但契約只承諾「可迭代的 (timestamp, mapping[symbol,float])」語意。
Timestamp = Any          # 實作以 pandas.Timestamp / datetime 表達
Symbol = str
SignalFrame = Any        # 例:pandas.DataFrame[index=Timestamp, columns=Symbol]
WeightFrame = Any        # 同上;每列加總語意由 Allocator/Engine 定義


@runtime_checkable
class PointInTimeDataProvider(Protocol):
    """As-of 取數;絕不回傳 asof 之後才可得的資料(含修訂值)。REQ-A0-PIT-001/002/003。"""

    def get(self, asof: Timestamp, fields: Sequence[str],
            symbols: Sequence[Symbol] | None = None) -> "pd.DataFrame":
        """回傳在 asof 當下實際可得的行情/欄位資料(point-in-time)。"""
        ...

    def universe(self, asof: Timestamp) -> Sequence[Symbol]:
        """回傳該時點『實際存在』的標的(survivorship-safe,含當時尚未下市者)。"""
        ...

    def macro(self, asof: Timestamp, series: str) -> float | None:
        """回傳總經序列在 asof 之前『已公布(release date)』的最新值;未公布回 None。"""
        ...


@runtime_checkable
class Strategy(Protocol):
    """框架無感策略/模型介面。底層可為 PyTorch/TF/JAX/sklearn,但輸出純資料。

    REQ-A0-IFC-001/002。回測引擎只透過此介面互動,不得感知底層框架。
    """

    def fit(self, train: "pd.DataFrame", **kwargs: Any) -> None:
        """以訓練窗資料擬合(無狀態策略可為 no-op)。"""
        ...

    def generate_signal(self, asof: Timestamp,
                        data: PointInTimeDataProvider) -> Mapping[Symbol, float]:
        """於 asof 產生訊號;只能透過 point-in-time data 取數,不得偷看未來。"""
        ...

    @property
    def metadata(self) -> Mapping[str, Any]:
        """模型 metadata(框架名、超參數、版本),寫入 ResultRecord。"""
        ...


@runtime_checkable
class BacktestEngine(Protocol):
    """回測引擎。吃 Strategy + DataProvider + config,吐 ResultRecord(dict,符合 schema)。

    REQ-A0-BT-001..006。向量化先行,介面預留事件式(由實作類別切換)。
    """

    def run(self, strategy: Strategy, data: PointInTimeDataProvider,
            config: Mapping[str, Any]) -> Mapping[str, Any]:
        """執行回測。config 須符合 schemas/backtest_config.json;
        回傳符合 schemas/result_record.json 的紀錄(含 net/gross 指標)。"""
        ...


@runtime_checkable
class ResultStore(Protocol):
    """Tier2 追蹤:寫入/查詢 ResultRecord,提供 leaderboard。REQ-A0-TRK-001/002/003。

    A0 實作以 MLflow tracking(local backend)為主。
    """

    def log(self, record: Mapping[str, Any]) -> str:
        """寫入一筆 ResultRecord(符合 schema),回傳 run_id。"""
        ...

    def leaderboard(self, metric: str = "oos_net_sharpe",
                    descending: bool = True) -> Sequence[Mapping[str, Any]]:
        """回傳依指定指標排序的 run 清單(可含 baseline),每列可追溯回設定。"""
        ...

    def get(self, run_id: str) -> Mapping[str, Any]:
        """取回單筆 ResultRecord,供重現。"""
        ...


@runtime_checkable
class ParallelExecutor(Protocol):
    """Tier1 平行底座抽象。joblib-first,介面預留 Ray。REQ-A0-PAR-001/002。"""

    def map(self, fn: Any, jobs: Sequence[Mapping[str, Any]], *,
            seed: int) -> Sequence[Mapping[str, Any]]:
        """平行執行 N 個回測 job;給定 seed 下結果須與序列執行一致(determinism)。"""
        ...
