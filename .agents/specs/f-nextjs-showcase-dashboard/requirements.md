# Requirements — F Next.js Showcase Dashboard

## Introduction

This spec upgrades the F showcase from repo-side Python payload/HTML smoke to a real Next.js dashboard runtime. It consumes a stable dashboard data contract, renders leaderboard, allocation/regime, rebalance, and evidence panels, and proves the page through component tests plus a real local Next.js HTTP smoke path.

## Dependencies, Impacts & CRs

- [Depends On: f-showcase-read-api-dashboard] dashboard payload shape and claim-boundary posture.
- [Depends On: a0-backtest-foundation] leaderboard/result-store semantics.
- [Depends On: d-first-regime-model, d-return-risk-forecast-model] strategy metadata and `no_alpha_claim` model evidence.
- [Impacts: none] Additive `frontend/` app; no change to legacy `invest_algorithms` API.
- [Open Change Requests: none]

## Repo-side Closure vs External Execution

- **Repo-side Closure:** Next.js scaffold, dashboard component/page/API route, deterministic fixture, unit/PBT/integration tests, coverage, mutation evidence, build, and local HTTP smoke.
- **External Execution:** Public hosting and production deployment are not included.
- **External Blockers / Constraints:** Browser screenshot testing is optional for this slice; local HTTP smoke is required.

## Requirements

### Requirement 1 [REQ-FNX-DASH-001]

**User Story:** As a showcase viewer, I want a real dashboard page, so that I can inspect QuantLab results in a browser-rendered Next.js app.

#### Acceptance Criteria

1. When the dashboard page renders, it shall show leaderboard, allocation/regime, rebalance, and evidence sections.
2. If the dashboard data includes warnings, the page shall display them visibly rather than hiding them.
3. When the dashboard renders model evidence, it shall preserve `no_alpha_claim`.

### Requirement 2 [REQ-FNX-API-001]

**User Story:** As a maintainer, I want a stable dashboard data API route, so that the frontend does not depend on Python internals.

#### Acceptance Criteria

1. When `/api/showcase` is requested, it shall return the canonical dashboard payload as JSON.
2. If the fixture contract is malformed, tests shall fail before the page can be marked ready.
3. When leaderboard rows are served, their order shall remain sorted by OOS-net Sharpe.

### Requirement 3 [REQ-FNX-SMOKE-001]

**User Story:** As a reviewer, I want local runtime proof, so that the dashboard is not just a static component claim.

#### Acceptance Criteria

1. When `npm run build` runs in `frontend/`, the Next.js app shall build successfully.
2. When `next start` serves the app locally, an HTTP smoke request to `/` shall return the dashboard page.
3. The review shall not claim public production deployment unless a hosted URL is separately proven.
