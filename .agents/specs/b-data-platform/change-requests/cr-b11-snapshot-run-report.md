# CR-B11 — Daily Snapshot Run Report

## Status

Implemented(repo-side) · Review PASSED

## Problem

The daily snapshot routine degraded per source, but its authoritative evidence was mostly console text. That made B operational readiness harder to audit and left source-health posture separate from actual run output.

## Scope

- Add `--report-json` to `scripts/daily_snapshot.py`.
- Preserve append-only snapshot behavior.
- Emit deterministic counts for `ok`, `skip`, `fail`, and `dry`.
- Emit per-job failure records without blocking successful source writes.
- Include explicit `source_contract_status_only` source-health summary.
- Keep Stooq default-disabled unless explicitly opted in.

## Verification

- RED: `tests/test_daily_snapshot.py` added report-json expectations before implementation.
- GREEN: `uv run pytest -q tests/test_daily_snapshot.py` -> 16 passed.
- PBT: Yahoo latest-close PBT remains active in `tests/test_daily_snapshot.py`.
- Mutation: `uv run python scripts/run_mutation_spot_checks.py --only snapshot-report-stooq-default` -> killed.

## Residual Risk

The report is repo-side/local evidence only. It does not prove external source availability beyond the configured run outcome.
