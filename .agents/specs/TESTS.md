# TESTS.md — Workspace Test Registry Rollup

> Derived summary only. Row-level authority lives in [quantlab/TESTS.md](../../quantlab/TESTS.md); final readiness verdicts live in each spec's `review.md`.

Last refreshed: 2026-06-11.

## Canonical Commands

```bash
uv run pytest -q
uv run mypy quantlab/ --ignore-missing-imports
uv run lint-imports
```

## Current Evidence Snapshot

| Subsystem / spec | Catalog | Summary | Latest evidence |
|---|---|---|---|
| `a0-backtest-foundation` | `quantlab/TESTS.md` | 24 A0 tests + manual mutation spot-check 5/5 killed | `uv run pytest -q` included in 123 passed; mypy clean; import-linter KEPT |
| `a-tsmc-hedge-slice` | `quantlab/TESTS.md` | 17 Epic A tests | `uv run pytest -q` included in 123 passed |
| `b-data-platform` | `quantlab/TESTS.md` | 24 B/data tests including Yahoo fallback and daily snapshot unit tests | `uv run pytest -q` included in 123 passed; targeted B continuation 19 passed |
| `c-portfolio-core` | `quantlab/TESTS.md` | 17 C tests including C-2 multi-horizon and C-3 rebalance coverage | `uv run pytest -q` included in 123 passed; targeted C-3 5 passed |
| `d-first-regime-model` | `quantlab/TESTS.md` | 6 D tests for PIT regime signal and OOS-net baseline integration | `uv run pytest -q` included in 123 passed; mypy clean; import-linter KEPT |
| legacy `invest_algorithms` | `quantlab/TESTS.md` | 33 pyramid calculator regression tests | `uv run pytest -q` included in 123 passed |
| governance guards | `quantlab/TESTS.md` | 2 import/drift guard tests | `uv run pytest -q` included in 123 passed; `uv run lint-imports` KEPT |

## External / Blocked Evidence Register

| ID | Owner | Current posture | Evidence pointer | Next routing |
|---|---|---|---|---|
| `ISSUE-B3-001` / `CR-B7` / `CR-B8` | `b-data-platform` B-3 | invalid FRED gold proxy fixed; Yahoo fallback for TSMC/TWSE smoke-proven; Stooq itself still external/source-contract blocked | `.agents/specs/ISSUE_LOG.md`; `cr-b7-source-health.md`; `cr-b8-yahoo-chart-fallback.md`; `data/vintage/raw/2026-06-11/` | restore/remove Stooq specifically only after selecting a verified source contract |

## Drift Notes

- `quantlab/TESTS.md` is the row-level source for current test inventory.
- `.agents/specs/TESTS.md`, `SPECS.md`, and `NEXT_STEPS.md` must not be used to backfill row-level test truth.
