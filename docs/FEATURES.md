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
| 3 | **Data platform** (vintage PIT loader, FRED price proxies, as-of alignment, `pit_strictness`, source-health, snapshot run report + ops gate + source-quorum proof, deep 1990+ approximate backfill) | B | CLI / data | PASSED (repo-side) | `scripts/daily_snapshot.py`, `snapshot_ops_gate.py`, `source_quorum_proof.py`, `backfill_history.py` | Stooq opt-in/blocked (`ISSUE-B3-001`); FRED/Yahoo/NOAA quorum live-proven for 2026-06-12; CR-B21 deep history backfill 1990→2026 (`is_approximate=true`, strict-excluded, 24/24 sources, fail=0 — residual 6 FRED rate/FX series incl. `T10Y2Y` captured by idempotent re-run → regime family full-feature) |
| 4 | **Portfolio core** (optimizer, multi-period allocation, regime rebalance selector, pyramid-entry adapter) | C | library | PASSED | `test_c_1..5` | maxDD bound is ex-post; additive to legacy `algo_pyramid` |
| 5 | **Model families** (first-regime classifier, return/risk forecaster, robust optimizer, family evaluator) | D | library / CLI | PASSED | `test_d_*`, OOS-net baselines | Deterministic methodology slices; `no_alpha_claim` |
| 6 | **MLOps E-lite** (experiment registry, config catalog, checksum snapshot durability, registry→dashboard bridge, Tier3 readiness gate, local serving/retraining/automated drift monitoring smoke evidence, production-tier evidence gate, governed production evidence probes, strict readiness proof CLI) | E | library / read API / CLI | PASSED | `test_e_1`, registry JSONL, readiness gate, serving/retraining/drift smoke evidence, production validators, readiness proof CLI | Local smoke only; CLI blocks hand-written readiness maps and gate blocks Tier3 ready without externally proven production-tier serving, retraining, and automated drift monitoring evidence with traceable HTTPS proof URLs plus allowlisted production identity URI schemes |
| 7 | **Showcase read API + dashboard** (ShowcaseReadAPI, dashboard summary, HTML render, Next.js app, `/api/showcase`, demo hardening, static showcase) | F | read API + Web UI | CONDITIONAL · `local_demo_only` | `canonical_local_result_store`, generated `frontend/lib/showcase-payload.json`, `frontend/` static export, `npm test` | Generated from a canonical local `LocalResultStore` / `ExperimentRegistry` scenario; not a live backend service |
| 7b | **Ops visual drift artifacts** (chromium-headless browser screenshot, browser visual diff gate, public-hosting probe, schedule run proof, scheduled-run observer, E drift report) | F/B/E ops | PASSED | `browser-visual.png`, `browser-visual-diff.json`, probe HTTP 200 plus deployed manifest contract metadata, Actions run `27392471359`, scheduled observer artifact | Visual diff is repo-baseline pixel-backed (`0 / 1,296,000` pixels mismatched at threshold `0.001`); after CR-FPS-006 branch-local Pages parity and the standalone probe are `configured_not_observed` for the refreshed `docs/` hash until Pages catches up; autonomous `event=schedule` dry-run proof exists, observer records `status=proven` and `schedule_run_count=1` |
| 8 | **Alt-data slices** (source-contract-first local CSV loader, two optional slices) | G | library | PASSED | `test_g_1` | Optional, default-disabled, `available_date <= asof` |
| 10 | **Deep-learning research lab** (framework-free reference MLP forecaster + A0 adapter, multi-framework backend registry (torch/jax/tf) with honest reference fallback, statistical performance report — distribution/rolling-Sharpe/drawdown/learning-curve, self-contained SVG/HTML viz, parameterized experiment CLI with ExperimentRegistry MLOps lineage) | H | library / CLI | PASSED (slice H-1) | `test_h_dl_forecaster`/`test_h_model_performance_report`/`test_h_dl_experiment_cli` (22 tests), 95.7% focused coverage, 3 mutations killed, import-linter DL-backend-boundary contract | OOS-net authority; `no_alpha_claim`; reference backend proves the mechanism; real torch/jax/tf GPU training, live interactive UI, and production Tier3 deferred |
| 9 | **Legacy pyramid calculator** (arithmetic + geometric order sizing) | — | FastAPI | stable legacy baseline | `tests/test_algo_pyramid.py` | Immutable; preserved unchanged |

## Latest authoritative gate evidence (2026-06-18)

- `uv run pytest -q` → **432 passed, 2 skipped** (default root env; H-2 torch-enabled UAT remains **430 passed** with optional torch lane running)
- `uv run mypy quantlab/ scripts/build_showcase_payload.py scripts/run_tsmc_hedge_slice.py scripts/run_vintage_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py scripts/source_quorum_proof.py scripts/stooq_contract_proof.py scripts/run_real_data_oos_backtest.py --ignore-missing-imports` → clean, **69 source files**
- `uv run lint-imports` → engine/data framework-agnostic **KEPT** (88 files, 242 deps)
- `frontend` `npm test` → **46 passed**; `npm audit --omit=dev` → **0 vulnerabilities**
- E registry focused line coverage → **99%** for `quantlab.mlops.experiment_registry`
- Python mutation spot checks → **118/118 configured/killed**, including `real-data-oos-sampling-frequency-guard`, `engine-event-driven-date-gate`, `result-store-finite-oos-net-sharpe`, `snapshot-scoped-source-health`, `b-source-quorum-status-gate`, `b-source-quorum-proof-exit-gate`, `b-source-quorum-proof-file-gate`, `b-stooq-proof-exit-gate`, `b-stooq-proof-file-gate`, `root-torch-default-dependency`, `demo-tsmc-store-close-gate`, `demo-vintage-store-close-gate`, `demo-showcase-payload-tempdir-gate`, `governance-stale-next-steps-alert`, `governance-stale-post-merge-sync-promotion`, `governance-stale-cron-proof-pending`, `governance-exhaustive-pr-ledger-regression`, `governance-stale-mutation-count-regression`, `governance-stale-import-linter-count-regression`, `governance-stale-import-linter-formalization-regression`, `governance-local-first-ci-default-regression`, `governance-local-first-ci-skill-default-regression`, `governance-refresh-review-stale-evidence-regression`, `governance-stale-dashboard-source-wording`, `governance-stale-f-nextjs-requirements-fixture`, `governance-stale-f-nextjs-fixture-review`, `governance-stale-visual-evidence-regression`, `browser-visual-doc-sync-gate-regression`, `public-hosting-manifest-status-overclaim`, `public-hosting-probe-status-overclaim`, `review-public-hosting-probe-status-overclaim`, `public-hosting-manifest-hash-overclaim`, `public-hosting-probe-hash-overclaim`, `public-hosting-manifest-contract-regression`, `public-hosting-taxonomy-authority-regression`, `manual-showcase-payload-sync-regression`, `frontend-showcase-payload-sync-regression`, `review-pytest-gate-transcript-regression`, `review-frontend-count-shorthand-regression`, `review-frontend-coverage-artifact-drift`, `review-audit-gate-transcript-regression`, `governance-test-registry-count-drift`, `mutation-test-registry-count-drift`, `e-tier3-readiness-gate`, `e-tier3-gate-proof-digest`, `e-tier3-manifest-artifact-uri-gate`, `e-production-retraining-artifact-uri-gate`, `e-production-artifact-scheme-allowlist-gate`, `e-production-observed-at-utc-gate`, `e-production-drift-threshold-gate`, `e-evidence-explicit-claim-boundary`, `e-production-external-proof-uri-gate`, `e-production-external-identity-uri-gate`, `showcase-frontend-transcript-failure-gate`, `e-serving-smoke-health-gate`, `e-retraining-smoke-status-gate`, `e-tier3-production-tier-gate`, `e-automated-drift-status-gate`, `e-production-serving-endpoint-gate`, `e-production-retraining-status-gate`, `e-tier3-cli-serving-validator`, `f-showcase-retired-fixture-marker`, `f-showcase-visual-diff-contract-gate`, `f-showcase-public-probe-freshness-gate`, `f-showcase-public-probe-observed-at-gate`, `f-showcase-public-probe-observed-at-age-gate`, and `b-scheduled-observer-manual-pending`; frontend coverage **90.00%**, frontend mutation 26/26 killed including `frontend-public-demo-probe-freshness-status-gate`, `frontend-public-demo-probe-absolute-output-path`, `frontend-public-demo-export-absolute-output-dir`, `frontend-public-demo-export-stale-evidence-gate`, `frontend-public-demo-expected-manifest-gate`, `frontend-public-demo-probe-manifest-colocation`, `frontend-public-demo-probe-incomplete-manifest-failclosed`, `frontend-static-export-showcase-sync`, `frontend-coverage-artifact-drift`, `frontend-visual-regression-underclaim`, `frontend-smoke-port-hardcode-regression`, and `frontend-smoke-html-api-parity-regression`
- `npm run visual:browser` → chromium-headless screenshot `proven`
  (`frontend/out/browser-visual.png`); `npm run probe:public-demo` → HTTP 200,
  deployed manifest HTTP 200. After CR-FPS-006, the branch-local generated
  dashboard payload has a refreshed `dataHash`, so deployment parity is
  intentionally `configured_not_observed` until Pages serves the new artifact.
  The dashboard readiness panel remains `local_demo_only`; visual regression is repo-side browser-proven while public hosting remains conservative.
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
