# NEXT_STEPS.md — Rolling Operational Memo

> 高階、滾動、可覆寫。跨 spec 當前狀態與恢復點。詳細真相見各 spec artifact。

## Current State (2026-06-12)

- **Current branch lane:** none. Next implementation work should branch from `origin/main`.
- **Dependency security:** Dependabot alert #7 fixed (`fixed_at=2026-06-12T01:19:57Z`) for `uv.lock` / `torch`; the default root environment still excludes the optional PyTorch lane.
- **Stakeholder docs published (2026-06-12):** bilingual user manual `docs/manual/{en,zh-tw}/index.{md,html}` and executive review `docs/review/index.html`, plus generation guides (`docs/MANUAL_GENERATION_GUIDE.md`, `docs/REVIEW_GENERATION_GUIDE.md`), shared evidence/warning contracts (`docs/{FEATURES,EVIDENCE_METADATA_CONTRACT,DEMO_RISK_WARNING_TAXONOMY}.md`), and traceability bridge `.agents/specs/RTM.md`. Live CLI demos captured under `docs/manual/assets/`; gate transcripts under `docs/review/assets/`; the chromium-headless `browser-visual.png`, `browser-visual-diff.json`, `public-hosting-probe.json` (HTTP 200), and autonomous schedule proof run `27392471359` are tracked as current evidence.
- **Latest evidence:** `uv run pytest -q` → **222 passed** (default env, after consolidating exact PR-pair memo guards into a non-self-staling promotion-boundary guard); `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py --ignore-missing-imports` → clean over 53 files; `uv run lint-imports` → KEPT; `uv run pytest --cov=quantlab.mlops.experiment_registry --cov-report=term-missing tests/quantlab/test_e_1_experiment_registry.py` → 27 passed, 100% line coverage; `uv run pytest --cov=scripts.run_mutation_spot_checks --cov-report=term-missing tests/test_mutation_spot_checks.py` → 8 passed, 90% line coverage; Python mutation spot checks **38/38 configured/killed**, including `governance-exhaustive-pr-ledger-regression` and `public-hosting-manifest-status-regression`; default `uv sync` removes `torch`/CUDA packages from the root env; F Next.js tests 23 passed, line coverage 91.42%, `npm audit --json` 0 vulnerabilities, 9/9 frontend mutations killed, static export/browser visual pixel diff/build/smoke/public probe passed.
- **Promotion proof boundary:** do not append every squash PR to this rolling memo. Authoritative promotion state lives in GitHub PR state and spec-local reports; `NEXT_STEPS.md` only records current resume state, durable evidence boundaries, and links to owning specs/reports so future squash promotions do not create another stale memo loop.
- **Latest external Actions proof:** `daily-snapshot.yml` failed before fix as run `27386918387` because `github.run_started_at` expanded empty. Fixed branch run `27387041974` on `spec/b-live-scheduled-snapshot-proof` succeeded via `workflow_dispatch`. Autonomous cron run `27392471359` on `main` later succeeded with `event=schedule` and uploaded `snapshot-schedule-proof`; proof JSON records `dry=22`, `exit_code=0`, `evidence_tier=smoke`, `retention=append_only`, `trigger=schedule`, and artifact digest `a2699a2ae7b24175364ce448633f789a03cd5557da2470b091ad7652409ffe61`.
- **ISSUE-B3-001 handled in advance:**
  - Promoted/folded into [CR-B7 source health](./b-data-platform/change-requests/cr-b7-source-health.md) for invalid FRED gold proxy defaults.
  - Repo-side fix: default FRED price proxy list now uses reachable `PCOPPUSDM` commodity proxy instead of invalid London gold IDs.
  - Promoted/folded into [CR-B8 Yahoo chart fallback](./b-data-platform/change-requests/cr-b8-yahoo-chart-fallback.md) for TSMC/TWSE fallback capture and PIT loading.
  - Promoted/folded into [CR-B9 Stooq opt-in](./b-data-platform/change-requests/cr-b9-stooq-opt-in.md); Stooq is no longer a default daily snapshot source.
  - Residual: Stooq itself remains external/source-contract blocked; TSMC/TWSE fallback is live-smoke proven through Yahoo chart from this environment.
- **Epic D first slice:** [d-first-regime-model](./d-first-regime-model/) is **Implemented(first slice) · Review PASSED**.
  - Added `RegimeSignal`, `RegimeFeatureBuilder`, `FirstRegimeClassifier`, and `RegimeAllocationStrategy`.
  - Targeted D evidence: 6 tests for PIT-safe signal and OOS-net baseline integration.
  - Conservative writeup: synthetic data proves pipeline correctness only; no alpha claim.
- **Epic C C-3:** time/regime rebalance selector implemented additively in `quantlab/portfolio/rebalance.py`; A0 engine scheduling now consumes it through CR-A0.
- **A0/C regime scheduling:** [CR-A0](./a0-backtest-foundation/change-requests/cr-a0-regime-rebalance-scheduling.md) lets the vectorized engine execute C-3 regime-selected dates through serializable `rebalance_policy` labels.
- **Mutation automation:** [mutation automation report](./a0-backtest-foundation/reports/mutation-automation-report.md) adds `scripts/run_mutation_spot_checks.py`; current suite kills 6/6 configured mutations.
- **D-3 real-source-format benchmark:** [real-data regime benchmark report](./d-first-regime-model/reports/real-data-regime-benchmark-report.md) adds vintage-loader-based OOS-net baseline comparison with explicit `no_alpha_claim`.
- **F showcase first slice:** [f-showcase-read-api-dashboard](./f-showcase-read-api-dashboard/) is **Implemented(repo-side read API/dashboard payload) · Review PASSED**.
  - Added `ShowcaseReadAPI`, dashboard summary builder, and deterministic HTML smoke renderer.
  - Live-demo readiness is **CONDITIONAL / hybrid** until a real Next.js runtime and browser evidence exist.
- **D return/risk second model slice:** [d-return-risk-forecast-model](./d-return-risk-forecast-model/) is **Implemented · Review PASSED**.
  - Added deterministic PIT-safe `ReturnRiskForecaster`, `ForecastAllocationStrategy`, and OOS-net benchmark helper.
  - Conservative writeup: no alpha claim; Tier3 MLOps remains deferred.
- **F real Next.js dashboard:** [f-nextjs-showcase-dashboard](./f-nextjs-showcase-dashboard/) is **Implemented · Review PASSED** for local runtime proof.
  - Added contained `frontend/` Next.js app, `/api/showcase`, component tests, mutation check, build, and local HTTP smoke.
  - Public hosting and visual regression remain deferred.
- **D robust optimizer third model family:** [d-robust-portfolio-optimization-model](./d-robust-portfolio-optimization-model/) is **Implemented · Review PASSED**.
  - Added downside-penalized robust optimizer strategy and OOS-net benchmark helper.
- **E Tier3 readiness / E-lite:** [e-mlops-tier3-readiness.md](./e-mlops-tier3-readiness.md) moved E to planning-ready; [e-mlops-tier3-lite](./e-mlops-tier3-lite/) is **Implemented · Review PASSED** for registry-only experiment lineage.
- **E Tier3 readiness gate:** [e-tier3-readiness-gate](./e-tier3-readiness-gate/) is **Implemented · Review PASSED** for repo-side false-green prevention; `tier3_ready` is impossible unless serving, retraining, and automated drift monitoring evidence are all `status=proven`.
- **E Tier3 serving evidence:** [e-tier3-serving-evidence](./e-tier3-serving-evidence/) is **Implemented · Review PASSED** for repo-side local serving smoke evidence; it is explicitly `evidence_tier=local_smoke` and cannot satisfy production Tier3 readiness.
- **E Tier3 retraining evidence:** [e-tier3-retraining-evidence](./e-tier3-retraining-evidence/) is **Implemented · Review PASSED** for repo-side local retraining smoke evidence; it is explicitly `evidence_tier=local_smoke` and cannot satisfy production Tier3 readiness.
- **E Tier3 production evidence gate:** [e-tier3-production-evidence-gate](./e-tier3-production-evidence-gate/) is **Implemented · Review PASSED** for repo-side production-tier evidence gating and local automated drift monitoring smoke evidence; Tier3 readiness now requires `status=proven`, correct `readiness_evidence_for`, and `evidence_tier=production` for serving, retraining, and automated drift monitoring.
- **E Tier3 production probes:** [e-tier3-production-probes](./e-tier3-production-probes/) is **Implemented · Review PASSED** for governed production evidence builders/validators; production serving rejects localhost/non-HTTPS identities, production retraining rejects local/incomplete runs, and production drift monitoring rejects local/unsupported monitor payloads. This prepares external proof ingestion but does not itself execute production services.
- **E Tier3 readiness proof CLI:** [e-tier3-readiness-proof-cli](./e-tier3-readiness-proof-cli/) is **Implemented · Review PASSED** for strict file-based production proof validation; it emits a Tier3 readiness gate artifact only after manifest, serving, retraining, and drift evidence JSON all pass governed validators; anything short of that remains `not_ready`.
- **B source-health follow-up:** [CR-B10](./b-data-platform/change-requests/cr-b10-source-health-registry.md) is **Implemented(repo-side)**; source status summaries are explicit and do not re-enable blocked Stooq defaults.
- **F demo hardening:** [f-demo-hardening](./f-demo-hardening/) is **Implemented · Review PASSED**; dashboard now exposes `local_demo_only`, `not_proven` public hosting/visual regression, and dependency audit posture.
- **B snapshot reliability / CR-B11:** [CR-B11](./b-data-platform/change-requests/cr-b11-snapshot-run-report.md) is **Implemented(repo-side) · Review PASSED**; `scripts/daily_snapshot.py --report-json` emits machine-readable counts, per-source failures, and source-health posture while keeping Stooq blocked/default-disabled.
- **B scoped live write smoke / CR-B12:** [CR-B12](./b-data-platform/change-requests/cr-b12-live-write-smoke.md) is **Implemented(repo-side + local live smoke)**.
  - `scripts/daily_snapshot.py` now supports scoped source selection and `--out-root`, so live-write smoke can prove append-only writes without broad source fragility or repo data pollution.
  - Live smoke on 2026-06-12 wrote `fred_FEDFUNDS.json` with `ok=1 fail=0`; a second run produced `skip=1`, proving immutable same-day behavior. `snapshot_ops_gate.py` accepted both non-dry-run reports as `clean`.
  - Boundary: proves scoped live append-only write mechanics, not broad default source availability and not Stooq readiness.
- **E/F registry dashboard bridge:** [e-f-registry-dashboard-bridge](./e-f-registry-dashboard-bridge/) is **Implemented · Review PASSED**; F read API and Next.js dashboard display E-lite registry entries as `research_only` / `registry_only` / `no_alpha_claim`.
- **F public demo readiness:** [f-public-demo-readiness](./f-public-demo-readiness/) is **Implemented · Review PASSED** for local production-demo readiness; PostCSS advisory is remediated through npm override, audit is clean, and `npm run smoke` validates `/` plus `/api/showcase`. Public hosting and visual regression remain `not_proven`.
- **G alt-data first slice:** [g-alt-data-first-slice](./g-alt-data-first-slice/) is **Implemented · Review PASSED**; optional local CSV loader requires source authority/pin, is default-disabled, and enforces `available_date <= asof`.
- **F public static showcase:** [f-public-static-showcase](./f-public-static-showcase/) is **Implemented · Review PASSED**; GitHub Pages static `docs/` artifact path is configured, `frontend/out` export is reproducible, visual contract baseline is pinned, and [CR-FPS-001](./f-public-static-showcase/change-requests/cr-fps-001-hosting-manifest-proof-sync.md) keeps the committed `docs/deployment-manifest.json` aligned with tracked HTTP 200 public-hosting proof.
- **B snapshot ops gate:** [b-snapshot-ops-gate](./b-snapshot-ops-gate/) is **Implemented · Review PASSED**; machine-readable reports are validated for count consistency, Stooq blocked/default-disabled posture, and explicit partial-failure handling.
- **G alt-data second slice:** [g-alt-data-second-slice](./g-alt-data-second-slice/) is **Implemented · Review PASSED**; second optional default-disabled source contract and bundle PIT loader are in place.
- **E registry durability bridge:** [e-registry-durability-bridge](./e-registry-durability-bridge/) is **Implemented · Review PASSED**; registry snapshots have checksums and `LocalResultStore` bridge consumes real OOS-net run records.
- **D model-family evaluation:** [d-model-family-evaluation](./d-model-family-evaluation/) is **Implemented · Review PASSED**; D family comparison ranks OOS-net only, keeps baseline visible, and rejects alpha-claim records.
- **Next gaps 1-6 Tier3/Public/Ops:** [next-gaps-1-6-tier3-public](./next-gaps-1-6-tier3-public/) is **Implemented · Review PASSED** in the working tree.
  - F public hosting proof: GitHub Pages is configured for `main` `/docs`; `https://austinyuch.github.io/finance_algorithms/` returned HTTP 200 and `docs/deployment-manifest.json` records `hostingEvidence.status=proven`.
  - F browser visual proof: `docs/browser-visual.json` records Chromium screenshot hash `63e86b6d0eabbc90d669496f3ebd7dd2a5f202fee8a9c7577d7ed571d382cee9`.
  - E Tier3 first slice: non-serving run manifest and drift skeleton only; no serving, retraining, or automated drift monitoring claim.
  - B scheduled ops: append-only schedule report helper and latest pointer are unit-tested.
  - D evaluation: family evaluator can consume real `LocalResultStore` records.
  - B Stooq: source-contract decision helper keeps blocked/default-disabled posture until live close rows are proven.
- **Ops/visual/drift artifacts lane:** [ops-visual-drift-artifacts](./ops-visual-drift-artifacts/) is **Implemented · Review PASSED**.
  - B scheduled ops proof: workflow config and proof builder record workflow/trigger/command/exit status, smoke/live tier, and append-only retention.
  - F visual diff: browser visual evidence now emits thresholded diff status while preserving screenshot hash proof.
  - E drift assessment: metric-delta drift report is assessed-not-automated, with `serving_status=not_serving` and `retraining_status=not_configured`.
  - B source-contract reopen: Stooq remains default-disabled; live close rows only allow `eligible_for_opt_in_review`.
  - D artifact expansion: model-family evaluation can be wrapped in checksumed JSON with row-count and OOS-net authority validation.
- **F browser pixel baseline lane:** [f-browser-pixel-baseline](./f-browser-pixel-baseline/) is **Implemented · Review PASSED**.
  - Replaced hash-derived visual mismatch with a committed PNG baseline and real pixel mismatch ratio.
  - Latest browser visual diff: `234 / 1,296,000` mismatched pixels, `mismatchRatio=0.00018055555555555555`, threshold `0.001`.
  - Dashboard remains fixture-driven / `local_demo_only`; this closes the visual-diff false-green residual only.
- **B live scheduled snapshot proof lane:** [b-live-scheduled-snapshot-proof](./b-live-scheduled-snapshot-proof/) is **Implemented · Review PASSED**.
  - Fixed the GitHub Actions workflow timestamp bug exposed by failed run `27386918387`.
  - Real Actions runs `27387041974` (`workflow_dispatch`) and `27392471359` (`schedule`) succeeded with artifact `snapshot-schedule-proof`.
  - Boundary: proves autonomous cron dry-run smoke execution. CR-B12 separately proves scoped local live append-only write mechanics.
- **B scheduled run observer lane:** [b-scheduled-run-observer](./b-scheduled-run-observer/) is **Implemented · Review PASSED** and merged to `dev`/`main`.
  - Added `scripts/scheduled_run_observer.py` to classify GitHub Actions run-list evidence without overclaiming manual dispatches.
  - Live observation artifact: `reports/scheduled-run-observation-2026-06-12-cron.json` records `status=proven`, `schedule_run_count=1`, and latest schedule success `27392471359`.
  - Boundary: observer proves cron trigger classification only; CR-B12 separately proves scoped local live-write mechanics, while broad source availability remains governed separately.
- **A Torch default dependency isolation lane:** [a-torch-default-dependency-isolation](./a-torch-default-dependency-isolation/) is **Implemented · Review PASSED** and merged to `dev`/`main`.
  - Removed unpatched `torch<=2.12.0` from default root `pyproject.toml` / `uv.lock` after Dependabot alert #7 reported no patched version.
  - `scripts/run_tsmc_hedge_slice.py` now degrades honestly without Torch and emits an optional PyTorch-lane notice.
  - Boundary: root default dependency reachability is closed; GitHub Dependabot alert #7 is fixed as of `2026-06-12T01:19:57Z`.

## Recommended Next Action

1. Keep `daily-snapshot.yml` observer evidence current after future cron runs; do not regress autonomous schedule proof from run `27392471359` back to pending without fresher contradictory Actions evidence.
2. Use `scripts/tier3_readiness_gate.py` for any external E production proof handoff; local smoke artifacts, invalid JSON, and hand-written production-looking maps must remain nonzero failures.
3. Keep stakeholder docs copied from `review.md` verdicts and avoid deriving readiness from test counts.

## Scheduled Ops

- Daily vintage snapshot routine is expected to continue writing append-only files under `data/vintage/raw/<date>/`.
- Current live proof says routine/source health is partial: Yahoo fallback is proven for `2330.TW` and `^TWII` on 2026-06-11; CR-B12 proves scoped live append-only write/skip mechanics for `fred:FEDFUNDS` on 2026-06-12; Stooq remains opt-in/blocked.

## Resume Hints

- For D closure truth, read [d-first-regime-model/review.md](./d-first-regime-model/review.md), [writeup.md](./d-first-regime-model/writeup.md), and [reports/implementation-report.md](./d-first-regime-model/reports/implementation-report.md).
- For D2 closure truth, read [d-return-risk-forecast-model/review.md](./d-return-risk-forecast-model/review.md) and [reports/implementation-report.md](./d-return-risk-forecast-model/reports/implementation-report.md).
- For F closure truth, read [f-showcase-read-api-dashboard/review.md](./f-showcase-read-api-dashboard/review.md) and [reports/implementation-report.md](./f-showcase-read-api-dashboard/reports/implementation-report.md).
- For B-3 source status, read [ISSUE_LOG.md](./ISSUE_LOG.md), [b-data-platform/change-requests/cr-b7-source-health.md](./b-data-platform/change-requests/cr-b7-source-health.md), [b-data-platform/change-requests/cr-b8-yahoo-chart-fallback.md](./b-data-platform/change-requests/cr-b8-yahoo-chart-fallback.md), and [b-data-platform/change-requests/cr-b9-stooq-opt-in.md](./b-data-platform/change-requests/cr-b9-stooq-opt-in.md).
- For C-3 closure truth, read [c-portfolio-core/reports/c3-rebalance-report.md](./c-portfolio-core/reports/c3-rebalance-report.md).
- For A0 regime scheduling, read [a0-backtest-foundation/change-requests/cr-a0-regime-rebalance-scheduling.md](./a0-backtest-foundation/change-requests/cr-a0-regime-rebalance-scheduling.md).
- For mutation automation, read [a0-backtest-foundation/reports/mutation-automation-report.md](./a0-backtest-foundation/reports/mutation-automation-report.md).
- For D-3 benchmark truth, read [d-first-regime-model/reports/real-data-regime-benchmark-report.md](./d-first-regime-model/reports/real-data-regime-benchmark-report.md).
- For B CR-B11, read [b-data-platform/change-requests/cr-b11-snapshot-run-report.md](./b-data-platform/change-requests/cr-b11-snapshot-run-report.md).
- For E/F bridge, read [e-f-registry-dashboard-bridge/review.md](./e-f-registry-dashboard-bridge/review.md).
- For F public-demo local readiness, read [f-public-demo-readiness/review.md](./f-public-demo-readiness/review.md).
- For G alt-data, read [g-alt-data-first-slice/review.md](./g-alt-data-first-slice/review.md).
- For test truth, read [quantlab/TESTS.md](../../quantlab/TESTS.md) then [.agents/specs/TESTS.md](./TESTS.md).

## Key Locked Decisions

- 個人自用純紙上;成功=方法論誠實度 + 實驗能力,非 alpha;雙目的(作品集 + lab)→ 兩速結構。
- 每模型 DoD:A0 產出「可與笨 baseline 並排比較的 OOS 報告」。
- 三框架(PyTorch/TF/JAX)harness 無感;Tier1+2 進 A0,Tier3(完整 MLOps)延後。
