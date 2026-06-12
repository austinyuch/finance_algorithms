# CR-B19 — source quorum live proof wrapper

- **CR ID:** CR-B19
- **Status:** Implemented(repo-side + live proof)
- **Owner spec:** `b-data-platform`
- **Target baseline:** B-3 external source contract / CR-B18 source quorum gate
- **Type:** false-green reduction; live broad-source proof artifact

## Motivation

CR-B18 added the broad source-quorum gate, but the repo still lacked a
repeatable command that ran the broad source scope and wrote a machine-readable
proof. That left too much room for ad-hoc shell sequences or replayed reports
to be mistaken for live source readiness.

## Change

1. Added `scripts/source_quorum_proof.py`.
2. The command runs `scripts/daily_snapshot.py` over the CR-B18 quorum source
   set:
   - FRED: `FEDFUNDS`, `SP500`, `PCOPPUSDM`
   - Yahoo: `2330.TW`, `^TWII`
   - NOAA: `oni`
3. It writes a proof artifact and exits nonzero unless:
   - the snapshot command exits `0`;
   - the report passes `validate_source_quorum_report(...)`;
   - every quorum `ok` / `skip` row has a corresponding snapshot file under
     the report `out_dir`.
4. Added unit, CLI smoke, negative replay, and mutation coverage for the proof
   wrapper.

## Evidence

- Real live attempt on 2026-06-12:

```bash
uv run python scripts/source_quorum_proof.py \
  --out-root data/vintage/raw \
  --report-json .agents/specs/b-data-platform/reports/source-quorum-attempt-2026-06-12-report.json \
  --proof-json .agents/specs/b-data-platform/reports/source-quorum-attempt-2026-06-12-proof.json
```

- First attempt failed closed after transient `fred:SP500` timeout: 5 source
  files were written, but proof status remained `not_proven`.
- Retry preserved append-only data and passed with `skip=6`, `fail=0`,
  `status=proven`, `evidence_tier=live_source_quorum`.
- `uv run pytest -q tests/test_daily_snapshot.py` -> 37 passed.
- `uv run pytest -q` -> 231 passed.
- `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py scripts/source_quorum_proof.py --ignore-missing-imports` -> clean over 54 files.
- `uv run lint-imports` -> KEPT.
- Mutation checks killed:
  - `b-source-quorum-proof-exit-gate`
  - `b-source-quorum-proof-file-gate`

## Boundary

This proves broad source quorum for the selected default source groups on
2026-06-12. It does **not** re-enable Stooq and does **not** prove every
possible default daily snapshot source. Stooq remains blocked/default-disabled
until a working source contract and live close rows are proven separately.
