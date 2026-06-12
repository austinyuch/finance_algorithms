# CR-B20 — Stooq contract proof wrapper

- **CR ID:** CR-B20
- **Status:** Implemented(repo-side + live fail-closed proof)
- **Owner spec:** `b-data-platform`
- **Target baseline:** B-3 external source contract / CR-B9 opt-in policy
- **Type:** source-contract proof hardening

## Motivation

CR-B9 correctly default-disabled Stooq after repeated HTTP 404s, and later
lanes added decision helpers requiring live positive close rows before any
opt-in review. The remaining operational gap was that a maintainer still had to
compose the opt-in probe manually, leaving room for a false-green report where
an `ok`/`skip` row is treated as proof without checking the underlying snapshot
file and positive close row.

## Change

1. Added `scripts/stooq_contract_proof.py`.
2. The wrapper requires explicit `--stooq-symbols`, runs `daily_snapshot.py`
   with FRED/Yahoo/NOAA disabled, and writes a proof JSON.
3. The proof exits 0 only when the Stooq-only snapshot command succeeds and the
   corresponding append-only snapshot file contains a positive finite close row.
4. Successful proof status is limited to `eligible_for_opt_in_review` with
   `claim_boundary=source_contract_status_only` and `default_enabled=false`.
5. Failed exits, missing snapshot files, invalid CSV, empty rows, zero/negative
   close, and non-finite close values remain `not_proven`.

## Evidence

- RED: focused tests failed before `scripts/stooq_contract_proof.py` existed.
- GREEN: `uv run pytest -q tests/test_daily_snapshot.py -k 'stooq_contract_proof or stooq_reopen_evidence or stooq_source_contract_decision'` -> **6 passed**.
- PBT: invalid Stooq proof close encodings (`0`, `-1`, empty, `nan`, non-numeric) remain `not_proven`; shared reopen evidence rejects missing/non-positive close values.
- Mutation:
  - `uv run python scripts/run_mutation_spot_checks.py --only b-stooq-proof-exit-gate` -> killed.
  - `uv run python scripts/run_mutation_spot_checks.py --only b-stooq-proof-file-gate` -> killed.
  - `uv run python scripts/run_mutation_spot_checks.py --only b-stooq-live-close-positive` -> killed after adding non-finite close rejection.
- Live smoke: `uv run python scripts/stooq_contract_proof.py --stooq-symbols spy.us --out-root data/vintage/raw --report-json .agents/specs/b-data-platform/reports/stooq-contract-proof-2026-06-12-report.json --proof-json .agents/specs/b-data-platform/reports/stooq-contract-proof-2026-06-12-proof.json` exited 1 because Stooq returned HTTP 404; proof artifact is `status=not_proven`, `evidence_tier=not_proven`, `rows=[]`, and `decision=requires_live_close_rows`.

## Residual

Stooq remains blocked/default-disabled. This CR reduces false-green risk around
future restoration attempts, but it does not restore Stooq, change defaults, or
replace the Yahoo/FRED/NOAA proven quorum path.
