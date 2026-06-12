# TESTS.md — Workspace Test Registry Rollup

> Derived summary only. Row-level authority lives in [quantlab/TESTS.md](../../quantlab/TESTS.md); final readiness verdicts live in each spec's `review.md`.

Last refreshed: 2026-06-12.

## Canonical Commands

```bash
uv run pytest -q
uv run mypy quantlab/ --ignore-missing-imports
uv run lint-imports
cd frontend && npm test -- --run
cd frontend && npm run coverage
cd frontend && npm run visual
cd frontend && npm run visual:browser
cd frontend && npm run probe:public-demo
cd frontend && npm run build
cd frontend && npm run mutation
cd frontend && npm run smoke
```

## Current Evidence Snapshot

| Subsystem / spec | Catalog | Summary | Latest evidence |
|---|---|---|---|
| `a0-backtest-foundation` | `quantlab/TESTS.md` | A0 tests + CR-A0 regime scheduling + mutation automation | `uv run pytest -q` included in 224 passed; mypy clean(53 files); import-linter KEPT |
| `a-tsmc-hedge-slice` / `a-torch-default-dependency-isolation` | `quantlab/TESTS.md` | Epic A hedge/baseline tests, optional PyTorch LSTM lane, default root dependency isolation, no-Torch TSMC demo smoke | `uv run pytest -q` included in 224 passed; `tests/test_dependency_security.py` 2 passed; `root-torch-default-dependency` mutation killed; LSTM module remains optional and root lock excludes Torch |
| `b-data-platform` / `b-snapshot-ops-gate` / `ops-visual-drift-artifacts` / `b-live-scheduled-snapshot-proof` / `b-scheduled-run-observer` | `quantlab/TESTS.md` | B/data tests including Yahoo fallback, Stooq opt-in, source-health registry, daily snapshot unit tests, CR-B11 run-report JSON, CR-B12 scoped live write smoke, ops report validation, schedule report/proof retention, workflow contract, workflow timestamp guard, Actions `workflow_dispatch` proof, autonomous `event=schedule` proof, scheduled run observer, and Stooq source-contract reopen evidence helper | `tests/test_daily_snapshot.py` 28 passed; CR-B12 live smoke wrote `fred_FEDFUNDS` then skipped on second run; Actions run `27392471359` succeeded with artifact `snapshot-schedule-proof`; observer live artifact records `status=proven`, `schedule_run_count=1`; Python mutations killed |
| `c-portfolio-core` | `quantlab/TESTS.md` | 17 C tests including C-2 multi-horizon and C-3 rebalance coverage | `uv run pytest -q` included in 224 passed |
| `d-first-regime-model` / `d-return-risk-forecast-model` | `quantlab/TESTS.md` | D tests for PIT signal, OOS-net baseline integration, D-3 real-source-format benchmark, and D2 return/risk forecast model | D2 targeted `uv run pytest -q tests/quantlab/test_d_4_return_risk_forecast.py` → 4 passed; D2 trace line coverage 87.1%; D2 mutation killed |
| `d-robust-portfolio-optimization-model` / `d-model-family-evaluation` / `next-gaps-1-6-tier3-public` / `ops-visual-drift-artifacts` | `quantlab/TESTS.md` | D3 robust optimizer plus D family OOS-net evaluator, `LocalResultStore` read wrapper, and checksumed evaluation artifact | D evaluator targeted 7 passed; ops-visual-drift fallback trace coverage 100% for `evaluation`; mutations killed |
| `e-mlops-tier3-lite` / `e-f-registry-dashboard-bridge` / `e-registry-durability-bridge` / `e-tier3-readiness-gate` / `e-tier3-serving-evidence` / `e-tier3-retraining-evidence` / `e-tier3-production-evidence-gate` / `e-tier3-production-probes` / `e-tier3-readiness-proof-cli` / `next-gaps-1-6-tier3-public` / `ops-visual-drift-artifacts` | `quantlab/TESTS.md` | E-lite experiment lineage/config registry tests, checksum snapshot, result-store bridge, non-serving Tier3 artifact manifest, drift skeleton/assessment, fail-closed Tier3 readiness gate, local serving/retraining smoke evidence, production-tier evidence gate, local automated drift monitoring smoke evidence, governed production evidence probes, strict readiness proof CLI, and F dashboard registry read bridge | E targeted 27 passed; CLI targeted 4 passed; `e-tier3-readiness-gate`, `e-serving-smoke-health-gate`, `e-retraining-smoke-status-gate`, `e-tier3-production-tier-gate`, `e-automated-drift-status-gate`, `e-production-serving-endpoint-gate`, `e-production-retraining-status-gate`, and `e-tier3-cli-serving-validator` mutations killed; focused `experiment_registry` line coverage 100% |
| `f-showcase-read-api-dashboard` / `f-nextjs-showcase-dashboard` / `f-demo-hardening` / `f-public-demo-readiness` / `f-public-static-showcase` / `next-gaps-1-6-tier3-public` / `ops-visual-drift-artifacts` / `f-browser-pixel-baseline` | `quantlab/TESTS.md`; `frontend/tests/dashboard.test.tsx`; `frontend/tests/public-demo.test.tsx` | F Python read API plus real Next.js dashboard route/component tests, static public showcase export, hosted public Pages proof, browser visual evidence/diff, visual contract baseline, repo-baseline pixel diff gate, integration, and production HTTP smoke | Python F 5 passed; Next.js F 23 passed, 91.42% line coverage, npm audit 0 vulnerabilities, 9 frontend mutations killed, visual/browser visual pixel diff/build/smoke/public probe passed |
| `g-alt-data-first-slice` / `g-alt-data-second-slice` | `quantlab/TESTS.md` | Optional alt-data source contracts, second default-disabled contract, bundle loader, and PIT-safe local CSV loader | G targeted tests 7 passed; changed pure-Python coverage 100%; mutation killed |
| legacy `invest_algorithms` | `quantlab/TESTS.md` | 33 pyramid calculator regression tests | `uv run pytest -q` included in 224 passed |
| governance guards | `quantlab/TESTS.md` | 11 import/drift/current-governance freshness guard tests, including CR-B12, CR-B13, CR-B14, CR-B15, and CR-B16 post-promotion resume state | `uv run pytest -q` included in 224 passed; targeted CR-B17 guard passed after memo sync; `scripts.run_mutation_spot_checks` focused coverage 90%; `uv run lint-imports` KEPT; `governance-stale-next-steps-alert`, `governance-stale-post-merge-sync-promotion`, `governance-stale-cron-proof-pending`, `governance-stale-live-write-promotion`, `governance-stale-cr-b13-promotion`, `governance-stale-cr-b14-promotion`, `governance-stale-cr-b15-promotion`, and `governance-stale-cr-b16-promotion` mutations killed |

## External / Blocked Evidence Register

| ID | Owner | Current posture | Evidence pointer | Next routing |
|---|---|---|---|---|
| `ISSUE-B3-001` / `CR-B7` / `CR-B8` / `CR-B9` / `CR-B10` | `b-data-platform` B-3 | invalid FRED gold proxy fixed; Yahoo fallback smoke-proven; Stooq default disabled and opt-in only; source health is explicit status-only evidence | `.agents/specs/ISSUE_LOG.md`; CR-B7/B8/B9/B10; `data/vintage/raw/2026-06-11/` | restore Stooq specifically only after selecting a verified source contract |
| `CR-B12` | `b-data-platform` B live-write ops | scoped source selection, caller-provided output root, source-health scope precision, and append-only live write/skip mechanics | `.agents/specs/b-data-platform/reports/live-write-smoke-2026-06-12.json`; `tests/test_daily_snapshot.py`; `scripts/run_mutation_spot_checks.py` | broad default source availability and Stooq readiness remain separate |

## Drift Notes

- `quantlab/TESTS.md` is the row-level source for current test inventory.
- `.agents/specs/TESTS.md`, `SPECS.md`, and `NEXT_STEPS.md` must not be used to backfill row-level test truth.
