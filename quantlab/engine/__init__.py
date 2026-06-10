"""回測引擎(向量化先行)。

⚠️ 框架隔離:本套件不得 import torch/tensorflow/jax(NFR-A0-FWAGN-001)。
"""
from quantlab.engine.vectorized import VectorizedEngine

__all__ = ["VectorizedEngine"]
