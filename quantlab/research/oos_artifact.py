"""Shared OOS artifact primitives (canonical JSON + SHA256 checksum).

Extracted (CR-RDO-005 refactor) so the single-window ``real_data_oos`` artifact
and the multi-cycle ``multi_cycle_oos`` artifact share one tamper-evident
checksum definition instead of duplicating it. Output is byte-identical to the
prior inline ``_canonical_json`` (sorted keys, compact separators), so existing
committed artifact checksums are unchanged.

⚠️ Framework isolation: research helper only — no torch/tensorflow/jax.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def canonical_json(value: Mapping[str, Any]) -> str:
    """Deterministic JSON encoding used for checksums (sorted, compact)."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def artifact_checksum(artifact_uri: Any, generated_at: Any, report: Mapping[str, Any]) -> str:
    """SHA256 over the canonical ``{artifact_uri, generated_at, report}`` payload."""
    payload = {"artifact_uri": artifact_uri, "generated_at": generated_at, "report": report}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
