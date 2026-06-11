"""Optional alt-data source contracts and PIT-safe CSV loading.

G alt-data starts as an explicit, default-disabled source-contract surface. The
loader only reads local captured files and filters by ``available_date <= asof``.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

SourceContractStatus = Literal["available", "blocked", "degraded", "unknown"]


@dataclass(frozen=True)
class AltDataSourceContract:
    source: str
    dataset: str
    authority_url: str
    pin: str
    default_enabled: bool = False
    status: SourceContractStatus = "unknown"
    claim_boundary: str = "source_contract_status_only"

    def __post_init__(self) -> None:
        required = {
            "source": self.source,
            "dataset": self.dataset,
            "authority_url": self.authority_url,
            "pin": self.pin,
        }
        for field, value in required.items():
            if not str(value).strip():
                raise ValueError(f"{field} is required")
        if self.claim_boundary != "source_contract_status_only":
            raise ValueError("alt-data contracts must remain source_contract_status_only")

    @property
    def is_ready(self) -> bool:
        return self.status == "available"


@dataclass(frozen=True)
class AltDataObservation:
    source: str
    dataset: str
    event_date: str
    available_date: str
    value: float
    is_approximate: bool
    claim_boundary: str


def _parse_bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "y"}


def load_alt_data_csv(
    path: str | Path,
    contract: AltDataSourceContract,
    *,
    asof: str,
    strict: bool = True,
) -> list[AltDataObservation]:
    if strict and not contract.is_ready:
        raise ValueError("source contract is not ready")

    rows: list[AltDataObservation] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            available_date = str(row["available_date"]).strip()
            if available_date > asof:
                continue
            rows.append(AltDataObservation(
                source=contract.source,
                dataset=contract.dataset,
                event_date=str(row["event_date"]).strip(),
                available_date=available_date,
                value=float(row["value"]),
                is_approximate=_parse_bool(str(row.get("is_approximate", ""))),
                claim_boundary=contract.claim_boundary,
            ))
    return rows
