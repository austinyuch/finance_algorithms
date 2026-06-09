"""Tier2 實驗追蹤(REQ-A0-TRK-001/002/003)。

預設後端:stdlib sqlite3 的 LocalResultStore(零重依賴)。
MLflow backend 因 Python 3.13 依賴衝突延後,將以同 ResultStore Protocol 接入。
"""
from quantlab.tracking.local_store import LocalResultStore

__all__ = ["LocalResultStore"]
