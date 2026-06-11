# Requirements — E/F Registry Dashboard Bridge

## Boundary

Expose E-lite experiment registry entries through F showcase read surfaces without upgrading the claim to Tier3 MLOps, production serving, drift monitoring, or retraining.

#### AC-EF-01 — Registry Read Surface
1. The Python showcase API can read an E-lite `ExperimentRegistry`.
2. Returned rows include experiment id, model family, strategy name, run ids, tags, status, readiness, and claim boundary.
3. Rows preserve `status=research_only`, `readiness=registry_only`, and `claim_boundary=no_alpha_claim`.

#### AC-EF-02 — Dashboard Display
1. The Next.js dashboard renders a compact experiment registry section.
2. The dashboard contract rejects registry rows that overclaim alpha or readiness.

#### AC-EF-03 — Verification
1. Unit/integration tests cover Python read API and dashboard payload.
2. PBT remains active for leaderboard ordering.
3. Mutation checks kill registry readiness/claim-boundary overclaims.
