# E Tier3 MLOps Readiness Reassessment

Date: 2026-06-11

## Verdict

**Planning-ready, implementation still deferred.**

The original E gate required at least 2-3 D model families before starting Tier3. That count is now satisfied:

1. `d-first-regime-model` — deterministic regime classifier/allocation.
2. `d-return-risk-forecast-model` — PIT-safe return/risk forecaster.
3. `d-robust-portfolio-optimization-model` — stress-adjusted robust optimizer.

However, full Tier3 implementation should still wait until the project has clearer operational pain from repeated model runs.

## Evidence Now Available

- All D families run through A0 OOS-net benchmark patterns.
- Claim boundary remains `no_alpha_claim`.
- Mutation checks cover D2/D3 claim-boundary drift.
- Local result tracking exists through `LocalResultStore`.
- F Next.js dashboard can display curated run evidence locally.

## Remaining Gaps Before E Implementation

1. **Experiment registry contract:** define model/run lineage beyond ad hoc local result records.
2. **Config promotion policy:** decide which run configs become reusable experiment definitions.
3. **Model artifact policy:** decide whether deterministic/statistical models need persisted artifacts or only config+code version.
4. **Retraining cadence:** not yet justified; current models are deterministic research slices.
5. **Drift monitoring:** no production serving path exists, so drift monitoring would be premature.
6. **Frontend dependency hygiene:** `npm audit` has moderate advisories before any public deployment.

## Recommended E Scope When Started

Open a new `e-mlops-tier3-lite` spec for a minimal registry-first E slice:

- experiment registry schema;
- reproducible run config catalog;
- model family metadata and lineage;
- dashboard-compatible registry read API;
- no serving, no auto-retraining, no drift monitoring yet.

## Routing Decision

- `e-mlops-tier3` lifecycle should move from **Deferred(R3)** to **Planning-ready / implementation deferred**.
- Next best lane remains either public/local demo hardening for F or E-lite requirements/design, depending on whether showcase or research operations is prioritized.
