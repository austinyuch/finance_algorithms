# CR-B18 — source quorum gate

- **CR ID:** CR-B18
- **Status:** Implemented(repo-side)
- **Owner spec:** `b-data-platform`
- **Target baseline:** B-3 external source contract / daily snapshot ops gate
- **Type:** false-green reduction; broad source-readiness boundary

## Motivation

CR-B12 proved scoped live append-only writes with a single known-good FRED
source. That is valuable smoke evidence, but it must not be reused as broad
default-source readiness. A separate fail-closed gate is needed for release
checks that require coverage across macro, price-proxy, equity, market, and
NOAA source groups.

## Change

1. `scripts/snapshot_ops_gate.py` now exposes
   `validate_source_quorum_report(...)`.
2. CLI usage adds:

```bash
uv run python scripts/snapshot_ops_gate.py report.json --require-source-quorum
```

3. The quorum gate requires a non-dry-run report, zero failed sources, blocked
   default-disabled Stooq posture, and at least one live `ok`/`skip` job in each
   default source group:
   - `fred_macro`
   - `fred_price_proxy`
   - `yahoo_equity`
   - `yahoo_market`
   - `noaa_macro`
4. Scoped smoke, dry-run-only reports, replayed dry rows, and failed critical
   source rows are rejected as broad readiness evidence.

## Evidence

- RED: new quorum tests failed before `validate_source_quorum_report` existed.
- GREEN: `uv run pytest -q tests/test_daily_snapshot.py` -> 33 passed.
- Full suite: `uv run pytest -q` -> 227 passed.
- Type/import gates: mypy clean over 53 files; import-linter KEPT.
- Mutation: `b-source-quorum-status-gate` killed.

## Boundary

This CR does not make broad default source availability proven. It adds the
gate that future live reports must pass before they can be described as broad
daily snapshot source readiness. Stooq remains blocked/default-disabled until
a working source contract is proven separately.
