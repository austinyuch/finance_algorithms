# NEXT_STEPS.md — Rolling Operational Memo

> 高階、滾動、可覆寫。跨 spec 當前狀態與恢復點。詳細真相見各 spec artifact。

## Current State (2026-06-11)

- **Current branch lane:** `spec/next-gaps-4-3-1-2-5`, branched from `dev`.
- **Latest evidence:** `uv run pytest -q` → **163 passed**; `uv run mypy quantlab/ --ignore-missing-imports` → clean(49 files); `uv run lint-imports` → KEPT; Python mutation spot checks **11/11 killed**; F showcase/E bridge trace coverage 95%; G alt-data trace coverage 100.0%; B daily snapshot trace coverage 100.0%; F Next.js tests 7 passed, line coverage 82.5%, `npm audit --json` 0 vulnerabilities, 4/4 frontend mutations killed, build and production smoke passed.
- **Merged:** PR #7 squash-merged to `main` as `6e2af71`; PR #8 squash-merged to `dev` as `1f46725`; PR #9 squash-merged to `dev` as `0eaeaf0`; PR #10 squash-merged to `dev` as `1cec276`.
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
- **B source-health follow-up:** [CR-B10](./b-data-platform/change-requests/cr-b10-source-health-registry.md) is **Implemented(repo-side)**; source status summaries are explicit and do not re-enable blocked Stooq defaults.
- **F demo hardening:** [f-demo-hardening](./f-demo-hardening/) is **Implemented · Review PASSED**; dashboard now exposes `local_demo_only`, `not_proven` public hosting/visual regression, and dependency audit posture.
- **B snapshot reliability / CR-B11:** [CR-B11](./b-data-platform/change-requests/cr-b11-snapshot-run-report.md) is **Implemented(repo-side) · Review PASSED**; `scripts/daily_snapshot.py --report-json` emits machine-readable counts, per-source failures, and source-health posture while keeping Stooq blocked/default-disabled.
- **E/F registry dashboard bridge:** [e-f-registry-dashboard-bridge](./e-f-registry-dashboard-bridge/) is **Implemented · Review PASSED**; F read API and Next.js dashboard display E-lite registry entries as `research_only` / `registry_only` / `no_alpha_claim`.
- **F public demo readiness:** [f-public-demo-readiness](./f-public-demo-readiness/) is **Implemented · Review PASSED** for local production-demo readiness; PostCSS advisory is remediated through npm override, audit is clean, and `npm run smoke` validates `/` plus `/api/showcase`. Public hosting and visual regression remain `not_proven`.
- **G alt-data first slice:** [g-alt-data-first-slice](./g-alt-data-first-slice/) is **Implemented · Review PASSED**; optional local CSV loader requires source authority/pin, is default-disabled, and enforces `available_date <= asof`.

## Recommended Next Action

1. Commit/push `spec/next-gaps-4-3-1-2-5`.
2. Open PR from `spec/next-gaps-4-3-1-2-5` into `dev`.
3. After merge to `dev`, open the requested squash PR from `dev` into `main`.

## Scheduled Ops

- Daily vintage snapshot routine is expected to continue writing append-only files under `data/vintage/raw/<date>/`.
- Current live proof says routine/source health is partial: Yahoo fallback is proven for `2330.TW` and `^TWII` on 2026-06-11; Stooq remains opt-in/blocked.

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
