# CR-B9 — Stooq opt-in source policy

- **CR ID:** CR-B9
- **Status:** Open → Implemented(repo-side)
- **Owner spec:** `b-data-platform`
- **Target baseline:** B-3 external source contract
- **Type:** source default policy correction

## Motivation

`ISSUE-B3-001` recorded repeated Stooq HTTP 404 responses from this environment. After CR-B8 added Yahoo chart fallback for TSMC/TWSE and broad-market proxy capture, keeping Stooq enabled by default caused avoidable daily snapshot failures.

## Change

1. `STOOQ_SYMBOLS` now defaults to an empty list.
2. Stooq remains available as an explicit opt-in through:

```bash
QUANTLAB_STOOQ_SYMBOLS="spy.us,2330.tw,^twse" uv run python scripts/daily_snapshot.py
```

3. Yahoo fallback remains the default live-smoke-proven path for `2330.TW` and `^TWII`.

## Evidence

- RED: tests failed while the legacy Stooq defaults remained enabled.
- GREEN: `uv run pytest -q tests/test_daily_snapshot.py` → **14 passed**.
- Line coverage: `scripts/daily_snapshot.py` → **95%**.
- Mutation: changing the default-empty behavior to `["spy.us"]` was killed by `test_stooq_defaults_disabled_after_source_contract_block`.
- Smoke: `uv run python scripts/daily_snapshot.py --dry-run` listed 22 jobs, no Stooq jobs, and `fail=0` without writing snapshots.

## Residual

Stooq itself remains external/source-contract blocked. This CR intentionally stops treating Stooq as a default source until a working contract is selected.
