"""Source-contract health summaries for B data providers.

This module records explicit observed source status. It does not probe the
network or silently re-enable sources that were disabled by source-contract CRs.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Literal, Mapping, Sequence

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


def _normalize_live_close_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for row in rows:
        symbol = str(row.get("symbol") or "").strip()
        event_date = str(row.get("event_date") or "").strip()
        close = row.get("close")
        if not symbol:
            raise ValueError("live close row requires symbol")
        if not event_date:
            raise ValueError("live close row requires event_date")
        if not isinstance(close, (int, float)) or not math.isfinite(float(close)) or close <= 0:
            raise ValueError("live close row requires positive close")
        normalized.append({"symbol": symbol, "event_date": event_date, "close": float(close)})
    if not normalized:
        raise ValueError("live close rows are required")
    return normalized


def build_source_contract_reopen_evidence(
    source: str,
    *,
    rows: Sequence[Mapping[str, Any]],
    observed_at: str,
) -> dict[str, object]:
    clean_source = source.strip().lower()
    if clean_source != "stooq":
        raise ValueError("only Stooq reopen evidence is supported")
    if not observed_at.strip():
        raise ValueError("source reopen evidence requires observed_at")
    return {
        "artifact_kind": "source_contract_reopen_evidence",
        "claim_boundary": "source_contract_status_only",
        "source": clean_source,
        "status": "live_close_rows_observed",
        "observed_at": observed_at,
        "rows": _normalize_live_close_rows(rows),
        "decision_scope": "opt_in_review_only",
    }


def decide_stooq_contract(
    source_health: dict[str, object],
    *,
    live_close_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, str]:
    stooq = source_health.get("stooq")
    if not isinstance(stooq, dict):
        raise ValueError("source health missing stooq status")
    if stooq.get("status") == "blocked" and stooq.get("default_enabled") is False:
        return {
            "decision": "keep_default_disabled",
            "claim_boundary": "source_contract_status_only",
            "required_evidence": "none_until_reopened",
            "default_enabled": "false",
        }
    if live_close_rows is not None:
        _normalize_live_close_rows(live_close_rows)
        return {
            "decision": "eligible_for_opt_in_review",
            "claim_boundary": "source_contract_status_only",
            "required_evidence": "live_close_rows_observed",
            "default_enabled": "false",
        }
    return {
        "decision": "requires_live_close_rows",
        "claim_boundary": "source_contract_status_only",
        "required_evidence": "non_empty_close_rows_before_default_enable",
        "default_enabled": "false",
    }
