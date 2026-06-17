"""Deep-learning backend boundary (Epic H).

Framework realizations (PyTorch / JAX / TensorFlow) are resolved lazily here so the
backtest core (`quantlab.engine` / `quantlab.data`) never imports an ML framework
(NFR-A0-FWAGN-001). The `reference` backend is framework-free and always available.
"""
from quantlab.models.dl.backends import Backend, FrameworkAdapterRegistry

__all__ = ["Backend", "FrameworkAdapterRegistry"]
