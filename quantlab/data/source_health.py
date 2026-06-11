"""Source-contract health summaries for B data providers.

This module records explicit observed source status. It does not probe the
network or silently re-enable sources that were disabled by source-contract CRs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SourceStatus = Literal["available", "blocked", "degraded", "unknown"]


@dataclass(frozen=True)
class SourceHealthRecord:
    source: str
    symbol: str
    status: SourceStatus
    default_enabled: bool
    reason: str = ""


class SourceHealthRegistry:
    def __init__(self) -> None:
        self._records: list[SourceHealthRecord] = []

    def record(
        self,
        source: str,
        symbol: str,
        *,
        status: SourceStatus,
        default_enabled: bool,
        reason: str = "",
    ) -> SourceHealthRecord:
        clean_source = source.strip().lower()
        clean_symbol = symbol.strip()
        if not clean_source or not clean_symbol:
            raise ValueError("source and symbol are required")
        rec = SourceHealthRecord(clean_source, clean_symbol, status, bool(default_enabled), reason)
        self._records.append(rec)
        return rec

    def summary(self) -> dict[str, object]:
        out: dict[str, object] = {"claim_boundary": "source_contract_status_only"}
        grouped: dict[str, list[SourceHealthRecord]] = {}
        for rec in self._records:
            grouped.setdefault(rec.source, []).append(rec)
        for source, records in grouped.items():
            latest = records[-1]
            out[source] = {
                "status": latest.status,
                "default_enabled": latest.default_enabled,
                "symbols": [rec.symbol for rec in records],
                "reason": latest.reason,
            }
        return out


def decide_stooq_contract(source_health: dict[str, object]) -> dict[str, str]:
    stooq = source_health.get("stooq")
    if not isinstance(stooq, dict):
        raise ValueError("source health missing stooq status")
    if stooq.get("status") == "blocked" and stooq.get("default_enabled") is False:
        return {
            "decision": "keep_default_disabled",
            "claim_boundary": "source_contract_status_only",
            "required_evidence": "none_until_reopened",
        }
    return {
        "decision": "requires_live_close_rows",
        "claim_boundary": "source_contract_status_only",
        "required_evidence": "non_empty_close_rows_before_default_enable",
    }
