# CR-B12 — scoped live write smoke

- **Status:** Implemented(repo-side + local live smoke)
- **Target baseline:** B daily snapshot append-only live write path
- **Type:** ops false-green reduction; no A0 contract change
- **Opened:** 2026-06-12
- **Closed:** 2026-06-12

## Context

`b-live-scheduled-snapshot-proof` proved GitHub Actions `workflow_dispatch` and autonomous `event=schedule` execution, but only through `--dry-run`. That left live append-only writes governed separately. Running the full default live snapshot is intentionally source-fragile because external sources can fail independently, so the next smallest high-value proof is a scoped live write smoke with a known public source and an isolated output root.

## Change

1. `scripts/daily_snapshot.py` now supports scoped execution:
   - `--out-root`
   - `--fred-series`
   - `--stooq-symbols`
   - `--yahoo-symbols`
   - `--no-noaa`
2. Machine-readable `source_health` now reflects the sources in the actual run scope instead of claiming every default source during a scoped smoke.
3. Tests cover:
   - scoped non-dry-run write into a caller-provided output root;
   - source-health scope precision;
   - second-run append-only skip behavior.
4. Mutation spot check `snapshot-scoped-source-health` kills a regression that would re-add unattempted Yahoo sources to a scoped report.

## Evidence

- `uv run pytest -q tests/test_daily_snapshot.py tests/test_mutation_spot_checks.py` -> 36 passed.
- `uv run python scripts/run_mutation_spot_checks.py` -> 36/36 configured mutations killed.
- `uv run python scripts/run_mutation_spot_checks.py --only snapshot-scoped-source-health --only governance-stale-post-merge-sync-promotion` -> both killed after retargeting the stale governance mutation.
- Live smoke:

```bash
uv run python scripts/daily_snapshot.py \
  --out-root /tmp/quantlab-live-write-smoke/vintage \
  --fred-series FEDFUNDS \
  --yahoo-symbols '' \
  --no-noaa \
  --report-json /tmp/quantlab-live-write-smoke/snapshot-report.json
```

Result: non-dry-run `ok=1 fail=0`, wrote `fred_FEDFUNDS.json`.

- Second live smoke against the same output root: `ok=0 skip=1 fail=0`, proving existing daily file was not overwritten.
- `uv run python scripts/snapshot_ops_gate.py /tmp/quantlab-live-write-smoke/snapshot-report.json` -> clean.
- `uv run python scripts/snapshot_ops_gate.py /tmp/quantlab-live-write-smoke/snapshot-report-second.json` -> clean.
- Committed summary: [../reports/live-write-smoke-2026-06-12.json](../reports/live-write-smoke-2026-06-12.json).

## Boundary

This proves the daily snapshot code can perform a scoped non-dry-run append-only write and can skip an existing daily file. It does not prove the broad default source set always succeeds, does not re-enable Stooq, and does not convert partial external source availability into production readiness.
