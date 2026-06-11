"""Point-in-time DataProvider(bitemporal)。

⚠️ 框架隔離:本套件不得 import torch/tensorflow/jax(NFR-A0-FWAGN-001)。
"""
from quantlab.data.provider import InMemoryPITDataProvider
from quantlab.data.alt_data import AltDataObservation, AltDataSourceContract, load_alt_data_csv

__all__ = [
    "AltDataObservation",
    "AltDataSourceContract",
    "InMemoryPITDataProvider",
    "load_alt_data_csv",
]
