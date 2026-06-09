"""Tier1 平行運算底座(joblib-first,介面預留 Ray)。REQ-A0-PAR-001/002。"""
from quantlab.parallel.executor import JoblibExecutor, seed_jobs

__all__ = ["JoblibExecutor", "seed_jobs"]
