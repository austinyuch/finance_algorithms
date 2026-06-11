# Requirements — G Alt-Data First Slice

## Boundary

Introduce optional alt-data ingestion as default-disabled, source-contract-first local CSV loading. No alpha claim and no external source is enabled by default.

#### AC-G-01 — Source Contract
1. Each alt-data source requires source, dataset, authority URL, and pin.
2. Contracts default to disabled.
3. Claim boundary is `source_contract_status_only`.

#### AC-G-02 — PIT Loader
1. Loader reads local CSV rows with `event_date`, `available_date`, `value`, and `is_approximate`.
2. Loader returns only rows with `available_date <= asof`.
3. Strict mode rejects unready contracts.

#### AC-G-03 — Verification
1. Unit tests cover contract validation and strict rejection.
2. PBT proves no future-available rows are returned.
3. Mutation checks kill PIT gate regressions.
