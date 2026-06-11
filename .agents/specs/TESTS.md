# TESTS.md — Workspace Test Registry Rollup

> Derived summary only. Row-level authority lives in [quantlab/TESTS.md](../../quantlab/TESTS.md); final readiness verdicts live in each spec's `review.md`.

Last refreshed: 2026-06-11.

## Canonical Commands

```bash
uv run pytest -q
uv run mypy quantlab/ --ignore-missing-imports
uv run lint-imports
cd frontend && npm test -- --run
cd frontend && npm run coverage
cd frontend && npm run visual
cd frontend && npm run build
cd frontend && npm run mutation
cd frontend && npm run smoke
```

## Current Evidence Snapshot

| Subsystem / spec | Catalog | Summary | Latest evidence |
|---|---|---|---|
| `a0-backtest-foundation` | `quantlab/TESTS.md` | A0 tests + CR-A0 regime scheduling + mutation automation | `uv run pytest -q` included in 176 passed; mypy clean(50 files); import-linter KEPT |
| `a-tsmc-hedge-slice` | `quantlab/TESTS.md` | 17 Epic A tests | `uv run pytest -q` included in 176 passed |
| `b-data-platform` / `b-snapshot-ops-gate` | `quantlab/TESTS.md` | B/data tests including Yahoo fallback, Stooq opt-in, source-health registry, daily snapshot unit tests, CR-B11 run-report JSON, and ops report validation | `uv run pytest -q` included in 176 passed; changed pure-Python fallback coverage 96% total; Python mutations killed |
| `c-portfolio-core` | `quantlab/TESTS.md` | 17 C tests including C-2 multi-horizon and C-3 rebalance coverage | `uv run pytest -q` included in 176 passed |
| `d-first-regime-model` / `d-return-risk-forecast-model` | `quantlab/TESTS.md` | D tests for PIT signal, OOS-net baseline integration, D-3 real-source-format benchmark, and D2 return/risk forecast model | D2 targeted `uv run pytest -q tests/quantlab/test_d_4_return_risk_forecast.py` → 4 passed; D2 trace line coverage 87.1%; D2 mutation killed |
| `d-robust-portfolio-optimization-model` / `d-model-family-evaluation` | `quantlab/TESTS.md` | D3 robust optimizer plus D family OOS-net evaluator | D evaluator targeted 4 passed; changed pure-Python coverage 100%; mutation killed |
| `e-mlops-tier3-lite` / `e-f-registry-dashboard-bridge` / `e-registry-durability-bridge` | `quantlab/TESTS.md` | E-lite experiment lineage/config registry tests, checksum snapshot, result-store bridge, and F dashboard registry read bridge | E targeted 7 passed; changed pure-Python coverage 99%; mutations killed |
| `f-showcase-read-api-dashboard` / `f-nextjs-showcase-dashboard` / `f-demo-hardening` / `f-public-demo-readiness` / `f-public-static-showcase` | `quantlab/TESTS.md`; `frontend/tests/dashboard.test.tsx`; `frontend/tests/public-demo.test.tsx` | F Python read API plus real Next.js dashboard route/component tests, static public showcase export, visual contract baseline, integration, and production HTTP smoke | Python F 5 passed; Next.js F 14 passed, 97.05% coverage, npm audit 0 vulnerabilities, 6 frontend mutations killed, visual/build/smoke passed |
| `g-alt-data-first-slice` / `g-alt-data-second-slice` | `quantlab/TESTS.md` | Optional alt-data source contracts, second default-disabled contract, bundle loader, and PIT-safe local CSV loader | G targeted tests 7 passed; changed pure-Python coverage 100%; mutation killed |
| legacy `invest_algorithms` | `quantlab/TESTS.md` | 33 pyramid calculator regression tests | `uv run pytest -q` included in 176 passed |
| governance guards | `quantlab/TESTS.md` | 2 import/drift guard tests | `uv run pytest -q` included in 176 passed; `uv run lint-imports` KEPT |

## External / Blocked Evidence Register

| ID | Owner | Current posture | Evidence pointer | Next routing |
|---|---|---|---|---|
| `ISSUE-B3-001` / `CR-B7` / `CR-B8` / `CR-B9` / `CR-B10` | `b-data-platform` B-3 | invalid FRED gold proxy fixed; Yahoo fallback smoke-proven; Stooq default disabled and opt-in only; source health is explicit status-only evidence | `.agents/specs/ISSUE_LOG.md`; CR-B7/B8/B9/B10; `data/vintage/raw/2026-06-11/` | restore Stooq specifically only after selecting a verified source contract |

## Drift Notes

- `quantlab/TESTS.md` is the row-level source for current test inventory.
- `.agents/specs/TESTS.md`, `SPECS.md`, and `NEXT_STEPS.md` must not be used to backfill row-level test truth.
