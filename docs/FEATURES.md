# FEATURES.md — Finance Algorithms Feature Catalog

> Stable feature inventory consumed by `docs/manual/` and `docs/review/`
> generation. Readiness columns are **copied** from the owning
> `.agents/specs/**/review.md`; they are never derived from task counts or
> `NEXT_STEPS.md` hints. See [`SPECS.md`](../.agents/specs/SPECS.md) for the
> dependency map and [`EVIDENCE_METADATA_CONTRACT.md`](./EVIDENCE_METADATA_CONTRACT.md)
> for evidence semantics.

Product shape: **Backend / Tool / CLI-dominant Hybrid** — a personal,
paper-only quant research lab. Success is defined as *methodology honesty +
experimentation capability*, **not** alpha. Every model slice declares
`no_alpha_claim`.

## Feature inventory

| # | Feature | Epic | Surface | Live-Demo Readiness | Evidence Source | Key boundary |
|---|---|---|---|---|---|---|
| 1 | **Vectorized backtest foundation** (PIT data, engine, metrics, walk-forward, parallel run, local tracking) | A0 | CLI / library | PASSED | unit tests + mutation | Framework-agnostic; MLflow backend deferred |
| 2 | **TSMC hedge slice** (hedge strategy, LSTM adapter, baselines, leaderboard) | A | CLI demo | PASSED | `scripts/run_tsmc_hedge_slice.py`, 83 tests | Synthetic data only; no real alpha |
| 3 | **Data platform** (vintage PIT loader, FRED price proxies, as-of alignment, `pit_strictness`, source-health, snapshot run report + ops gate + source-quorum proof) | B | CLI / data | PASSED (repo-side) | `scripts/daily_snapshot.py`, `snapshot_ops_gate.py`, `source_quorum_proof.py` | Stooq opt-in/blocked (`ISSUE-B3-001`); FRED/Yahoo/NOAA quorum live-proven for 2026-06-12 |
| 4 | **Portfolio core** (optimizer, multi-period allocation, regime rebalance selector, pyramid-entry adapter) | C | library | PASSED | `test_c_1..5` | maxDD bound is ex-post; additive to legacy `algo_pyramid` |
| 5 | **Model families** (first-regime classifier, return/risk forecaster, robust optimizer, family evaluator) | D | library / CLI | PASSED | `test_d_*`, OOS-net baselines | Deterministic methodology slices; `no_alpha_claim` |
| 6 | **MLOps E-lite** (experiment registry, config catalog, checksum snapshot durability, registry→dashboard bridge, Tier3 readiness gate, local serving/retraining/automated drift monitoring smoke evidence, production-tier evidence gate, governed production evidence probes, strict readiness proof CLI) | E | library / read API / CLI | PASSED | `test_e_1`, registry JSONL, readiness gate, serving/retraining/drift smoke evidence, production validators, readiness proof CLI | Local smoke only; CLI blocks hand-written readiness maps and gate blocks Tier3 ready without externally proven production-tier serving, retraining, and automated drift monitoring evidence |
| 7 | **Showcase read API + dashboard** (ShowcaseReadAPI, dashboard summary, HTML render, Next.js app, `/api/showcase`, demo hardening, static showcase) | F | read API + Web UI | CONDITIONAL · `local_demo_only` | `frontend/` static export, `npm test` | Fixture-driven; see ops-visual-drift residuals below |
| 7b | **Ops visual drift artifacts** (chromium-headless browser screenshot, browser visual diff gate, public-hosting probe, schedule run proof, scheduled-run observer, E drift report) | F/B/E ops | Web UI + ops | PASSED | `browser-visual.png`, `browser-visual-diff.json`, probe HTTP 200 plus deployed manifest hash/contract metadata, Actions run `27392471359`, scheduled observer artifact | Visual diff is repo-baseline pixel-backed (`221 / 1,296,000` pixels mismatched at threshold `0.001`); public Pages now serves the committed `docs/` hash; autonomous `event=schedule` dry-run proof exists, observer records `status=proven` and `schedule_run_count=1` |
| 8 | **Alt-data slices** (source-contract-first local CSV loader, two optional slices) | G | library | PASSED | `test_g_1` | Optional, default-disabled, `available_date <= asof` |
| 9 | **Legacy pyramid calculator** (arithmetic + geometric order sizing) | — | FastAPI | stable legacy baseline | `tests/test_algo_pyramid.py` | Immutable; preserved unchanged |

## Latest authoritative gate evidence (2026-06-12)

- `uv run pytest -q` → **236 passed** (default env)
- `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py scripts/source_quorum_proof.py scripts/stooq_contract_proof.py --ignore-missing-imports` → clean, **55 source files**
- `uv run lint-imports` → engine/data framework-agnostic **KEPT** (73 files, 177 deps)
- `frontend` `npm test` → **27 passed**; `npm audit --omit=dev` → **0 vulnerabilities**
- E registry focused line coverage → **100%** for `quantlab.mlops.experiment_registry`
- Python mutation spot checks → **45/45 configured/killed**, including `snapshot-scoped-source-health`, `b-source-quorum-status-gate`, `b-source-quorum-proof-exit-gate`, `b-source-quorum-proof-file-gate`, `b-stooq-proof-exit-gate`, `b-stooq-proof-file-gate`, `root-torch-default-dependency`, `governance-stale-next-steps-alert`, `governance-stale-post-merge-sync-promotion`, `governance-stale-cron-proof-pending`, `governance-exhaustive-pr-ledger-regression`, `public-hosting-manifest-status-regression`, `public-hosting-manifest-hash-regression`, `public-hosting-manifest-contract-regression`, `e-tier3-readiness-gate`, `e-serving-smoke-health-gate`, `e-retraining-smoke-status-gate`, `e-tier3-production-tier-gate`, `e-automated-drift-status-gate`, `e-production-serving-endpoint-gate`, `e-production-retraining-status-gate`, `e-tier3-cli-serving-validator`, and `b-scheduled-observer-manual-pending`; frontend coverage **91.81%**, mutation 12/12 killed
- `npm run visual:browser` → chromium-headless screenshot `proven`
  (`frontend/out/browser-visual.png`); `npm run probe:public-demo` → HTTP 200,
  deployed manifest HTTP 200, matching deployed `dataHash`, and matching
  manifest contract metadata. The dashboard readiness panel remains
  conservative because it is fixture-backed local demo evidence.
- GitHub Actions `daily-snapshot.yml` autonomous `event=schedule` run
  `27392471359` succeeded and uploaded `snapshot-schedule-proof`; the
  scheduled-run observer records `status=proven` and `schedule_run_count=1`
- Root `pyproject.toml` / `uv.lock` no longer includes unpatched `torch`; default
  TSMC hedge demo skips the optional PyTorch LSTM lane explicitly.

These counts are the basis for the "gaps resolved since last check" sections of
the manual and review. Visual diff is now repo-baseline pixel-backed; autonomous
cron dry-run proof is observed, CR-B12 proves scoped live append-only write/skip
mechanics, and CR-B19 proves FRED/Yahoo/NOAA broad source quorum for
2026-06-12. Stooq source availability remains governed separately.
