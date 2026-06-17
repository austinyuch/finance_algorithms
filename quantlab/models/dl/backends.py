"""FrameworkAdapterRegistry — honest, lazy resolution of DL backends (REQ-H-FWBACKEND-001).

Design intent (DDD anti-corruption boundary): the deep-learning research context speaks
about a *Backend* value object. Real PyTorch / JAX / TensorFlow are resolved only when
their framework imports successfully; when a framework is absent we **degrade honestly**
to the deterministic `reference` backend rather than raising, so the multi-framework
story is demonstrable in any environment and the framework-isolation rule is never
violated. Imports here are lazy; the backtest core never imports this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util


@dataclass(frozen=True)
class Backend:
    """Resolved numerical backend for a deep model.

    ``name`` is the backend actually used; ``requested`` is what the caller asked for
    (differs from ``name`` only on honest fallback); ``reason`` records why a fallback
    occurred (empty when the requested backend was available).
    """

    name: str
    requested: str
    available: bool
    reason: str = ""


# Known framework labels → the top-level module probed to decide availability.
_FRAMEWORK_MODULES = {
    "pytorch": "torch",
    "jax": "jax",
    "tensorflow": "tensorflow",
}
_REFERENCE = "reference"


def _framework_installed(module_name: str) -> bool:
    """True when the framework can be imported, without importing it (lazy probe)."""
    return importlib.util.find_spec(module_name) is not None


class FrameworkAdapterRegistry:
    """Resolves a :class:`Backend`, degrading honestly to ``reference``."""

    def available_backends(self) -> list[str]:
        """Backends usable in this environment (``reference`` plus installed frameworks)."""
        installed = [
            label for label, module in _FRAMEWORK_MODULES.items()
            if _framework_installed(module)
        ]
        return [_REFERENCE, *installed]

    def resolve(self, name: str) -> Backend:
        """Resolve ``name`` to a usable :class:`Backend`.

        - ``reference`` → always available.
        - a known framework label → that backend when its framework is installed,
          otherwise an honest fallback to ``reference`` (never raises).
        - any other label → :class:`ValueError` (fail closed).
        """
        requested = str(name).strip().lower()
        if requested == _REFERENCE:
            return Backend(name=_REFERENCE, requested=_REFERENCE, available=True)
        if requested not in _FRAMEWORK_MODULES:
            raise ValueError(
                f"unknown deep-learning backend {name!r}; "
                f"known: {[_REFERENCE, *_FRAMEWORK_MODULES]}"
            )
        module = _FRAMEWORK_MODULES[requested]
        if _framework_installed(module):
            return Backend(name=requested, requested=requested, available=True)
        return Backend(
            name=_REFERENCE,
            requested=requested,
            available=True,
            reason=f"{requested} backend unavailable ({module!r} not installed); "
                   f"degraded honestly to the framework-free reference backend",
        )
