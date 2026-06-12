"""Point-in-time DataProvider(bitemporal)。

⚠️ 框架隔離:本套件不得 import torch/tensorflow/jax(NFR-A0-FWAGN-001)。
"""
from typing import Any

__all__ = [
    "AltDataObservation",
    "AltDataSourceContract",
    "InMemoryPITDataProvider",
    "load_alt_data_csv",
]


def __getattr__(name: str) -> Any:
    if name == "InMemoryPITDataProvider":
        from quantlab.data.provider import InMemoryPITDataProvider

        return InMemoryPITDataProvider
    if name in {"AltDataObservation", "AltDataSourceContract", "load_alt_data_csv"}:
        from quantlab.data.alt_data import AltDataObservation, AltDataSourceContract, load_alt_data_csv

        return {
            "AltDataObservation": AltDataObservation,
            "AltDataSourceContract": AltDataSourceContract,
            "load_alt_data_csv": load_alt_data_csv,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
