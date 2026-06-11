"""G-1 optional alt-data first slice tests.

RED/GREEN/REFACTOR trace:
- RED: define contract-first alt-data expectations before implementation.
- GREEN: implement a tiny CSV loader that is PIT-safe and default-disabled.
- REFACTOR: keep source-contract validation isolated from loader filtering.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st


def _write_csv(path: Path) -> None:
    path.write_text(
        "event_date,available_date,value,is_approximate\n"
        "2026-01-01,2026-01-03,10.5,false\n"
        "2026-01-02,2026-01-07,11.0,false\n",
        encoding="utf-8",
    )


def test_alt_data_contract_requires_explicit_authority_and_pin():
    from quantlab.data.alt_data import AltDataSourceContract

    contract = AltDataSourceContract(
        source="policy_uncertainty",
        dataset="news_index",
        authority_url="https://example.test/policy-index",
        pin="v2026-01",
        default_enabled=False,
        status="unknown",
    )

    assert contract.claim_boundary == "source_contract_status_only"
    assert contract.default_enabled is False
    assert contract.is_ready is False

    with pytest.raises(ValueError, match="authority_url"):
        AltDataSourceContract("bad", "dataset", "", "v1")


def test_alt_data_loader_filters_by_available_date_without_enabling_source(tmp_path):
    from quantlab.data.alt_data import AltDataSourceContract, load_alt_data_csv

    csv_path = tmp_path / "policy.csv"
    _write_csv(csv_path)
    contract = AltDataSourceContract(
        source="policy_uncertainty",
        dataset="news_index",
        authority_url="https://example.test/policy-index",
        pin="v2026-01",
        default_enabled=False,
        status="available",
    )

    rows = load_alt_data_csv(csv_path, contract, asof="2026-01-05")

    assert [row.event_date for row in rows] == ["2026-01-01"]
    assert rows[0].available_date == "2026-01-03"
    assert rows[0].value == 10.5
    assert rows[0].source == "policy_uncertainty"
    assert rows[0].dataset == "news_index"
    assert contract.default_enabled is False


@given(
    available_offsets=st.lists(st.integers(min_value=0, max_value=30), min_size=1, max_size=20),
    asof_offset=st.integers(min_value=0, max_value=30),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_pbt_alt_data_loader_never_returns_future_available_rows(
    tmp_path, available_offsets, asof_offset
):
    from datetime import date, timedelta

    from quantlab.data.alt_data import AltDataSourceContract, load_alt_data_csv

    base = date(2026, 1, 1)
    csv_path = tmp_path / "alt.csv"
    lines = ["event_date,available_date,value,is_approximate"]
    for idx, offset in enumerate(available_offsets):
        event_date = base + timedelta(days=idx)
        available_date = base + timedelta(days=offset)
        lines.append(f"{event_date.isoformat()},{available_date.isoformat()},{idx + 0.5},false")
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    contract = AltDataSourceContract(
        source="alt",
        dataset="demo",
        authority_url="https://example.test/alt",
        pin="v1",
        status="available",
    )
    asof = (base + timedelta(days=asof_offset)).isoformat()

    rows = load_alt_data_csv(csv_path, contract, asof=asof)

    assert all(row.available_date <= asof for row in rows)


def test_alt_data_loader_rejects_unready_source_contract(tmp_path):
    from quantlab.data.alt_data import AltDataSourceContract, load_alt_data_csv

    csv_path = tmp_path / "policy.csv"
    _write_csv(csv_path)
    contract = AltDataSourceContract(
        source="policy_uncertainty",
        dataset="news_index",
        authority_url="https://example.test/policy-index",
        pin="v2026-01",
        status="unknown",
    )

    with pytest.raises(ValueError, match="source contract is not ready"):
        load_alt_data_csv(csv_path, contract, asof="2026-01-05", strict=True)
