"""Point-in-time DataProvider(bitemporal)。

⚠️ 框架隔離:本套件不得 import torch/tensorflow/jax(NFR-A0-FWAGN-001)。
"""
from quantlab.data.provider import InMemoryPITDataProvider

__all__ = ["InMemoryPITDataProvider"]
