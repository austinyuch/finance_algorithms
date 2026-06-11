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
| `a0-backtest-foundation` | `quantlab/TESTS.md` | A0 tests + CR-A0 regime scheduling + mutation automation | `uv run pytest -q` included in 145 passed; mypy clean(44 files); import-linter KEPT |
| `a-tsmc-hedge-slice` | `quantlab/TESTS.md` | 17 Epic A tests | `uv run pytest -q` included in 145 passed |
| `b-data-platform` | `quantlab/TESTS.md` | B/data tests including Yahoo fallback, Stooq opt-in, and daily snapshot unit tests | `uv run pytest -q` included in 145 passed |
| `c-portfolio-core` | `quantlab/TESTS.md` | 17 C tests including C-2 multi-horizon and C-3 rebalance coverage | `uv run pytest -q` included in 145 passed |
| `d-first-regime-model` / `d-return-risk-forecast-model` | `quantlab/TESTS.md` | D tests for PIT signal, OOS-net baseline integration, D-3 real-source-format benchmark, and D2 return/risk forecast model | D2 targeted `uv run pytest -q tests/quantlab/test_d_4_return_risk_forecast.py` → 4 passed; D2 trace line coverage 87.1%; D2 mutation killed |
| `f-showcase-read-api-dashboard` | `quantlab/TESTS.md` | F showcase read API/dashboard payload tests including PBT order, integration, and HTML smoke | `uv run pytest -q tests/quantlab/test_f_1_showcase_api.py` → 4 passed; line coverage 95%; mutation killed |
| legacy `invest_algorithms` | `quantlab/TESTS.md` | 33 pyramid calculator regression tests | `uv run pytest -q` included in 145 passed |
| governance guards | `quantlab/TESTS.md` | 2 import/drift guard tests | `uv run pytest -q` included in 145 passed; `uv run lint-imports` KEPT |

## External / Blocked Evidence Register

| ID | Owner | Current posture | Evidence pointer | Next routing |
|---|---|---|---|---|
| `ISSUE-B3-001` / `CR-B7` / `CR-B8` / `CR-B9` | `b-data-platform` B-3 | invalid FRED gold proxy fixed; Yahoo fallback smoke-proven; Stooq default disabled and opt-in only | `.agents/specs/ISSUE_LOG.md`; CR-B7/B8/B9; `data/vintage/raw/2026-06-11/` | restore Stooq specifically only after selecting a verified source contract |

## Drift Notes

- `quantlab/TESTS.md` is the row-level source for current test inventory.
- `.agents/specs/TESTS.md`, `SPECS.md`, and `NEXT_STEPS.md` must not be used to backfill row-level test truth.
