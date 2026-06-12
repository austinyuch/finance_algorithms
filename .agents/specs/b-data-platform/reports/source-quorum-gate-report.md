# Source Quorum Gate Report — CR-B18

## Summary

Added a fail-closed broad source-quorum gate for daily snapshot reports. The
existing ops gate still validates honest report structure and scoped live smoke;
the new quorum mode rejects scoped or dry-run evidence when the claim is broad
default-source readiness.

## Implementation

- Extended `scripts/snapshot_ops_gate.py` with `DEFAULT_SOURCE_QUORUM` and
  `validate_source_quorum_report(...)`.
- Added `--require-source-quorum` CLI mode.
- Added unit, CLI smoke, PBT, and chaos tests in `tests/test_daily_snapshot.py`.
- Added mutation `b-source-quorum-status-gate` to prevent dry/fail rows from
  satisfying quorum.

## Evidence

- RED: quorum tests failed with `ImportError` before implementation.
- `uv run pytest -q tests/test_daily_snapshot.py` -> 33 passed.
- `uv run python scripts/run_mutation_spot_checks.py --only b-source-quorum-status-gate` -> killed.
- `uv run pytest -q` -> 227 passed.
- `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py --ignore-missing-imports` -> clean over 53 files.
- `uv run lint-imports` -> KEPT.

## Residual

At CR-B18 closeout, no committed live report proved broad default-source
quorum. That conservative boundary was later narrowed by CR-B19, which added a
live proof wrapper and captured a passing FRED/Yahoo/NOAA quorum proof on
2026-06-12. Stooq remains separate source-contract work.
