# Requirements — F Showcase Read API Dashboard

## Introduction

This spec creates the first showcase-facing read surface for QuantLab results. It exposes leaderboard, run detail, regime, rebalance, and dashboard summary data from existing A0/D/C outputs without changing the legacy `invest_algorithms` pyramid API behavior.

## Dependencies, Impacts & CRs

- [Depends On: a0-backtest-foundation] `ResultStore` / leaderboard / run detail contracts.
- [Depends On: c-portfolio-core] rebalance date semantics.
- [Depends On: d-first-regime-model] regime metadata and no-alpha claim boundary.
- [Impacts: none] This first slice is additive and does not modify completed baseline contracts.
- [Open Change Requests: none]

## Repo-side Closure vs External Execution

- **Repo-side Closure:** Python read API helpers, dashboard view-model generation, deterministic smoke rendering, tests, reports, and governance updates.
- **External Execution:** Full Next.js runtime, browser screenshots, and production hosting are not part of this first slice.
- **External Blockers / Constraints:** None. Live-demo readiness is capped to repo-side API/payload smoke until a frontend scaffold exists.

## Requirements

### Requirement 1 [REQ-F-SHOWCASE-001]

**User Story:** As a portfolio reviewer, I want a read-only leaderboard API, so that I can inspect OOS-net results without opening SQLite or Python internals.

#### Acceptance Criteria

1. When a result store contains runs, the API shall return leaderboard rows ordered by OOS-net Sharpe and include traceable `run_id` values.
2. If a requested run id does not exist, the API shall return a conservative not-found error instead of an empty success payload.
3. When leaderboard rows are serialized, the API shall preserve baseline flags and shall not invent alpha claims.

### Requirement 2 [REQ-F-SHOWCASE-002]

**User Story:** As a QuantLab maintainer, I want a dashboard summary payload, so that F can display current allocation, regime, rebalance, and evidence status from existing run records.

#### Acceptance Criteria

1. When a run record includes strategy metadata and rebalance dates, the dashboard summary shall expose them without mutating the source record.
2. If a run record lacks optional regime metadata, the dashboard summary shall mark the regime as `unknown` rather than failing.
3. When claim boundary metadata is absent, the dashboard summary shall default to `no_alpha_claim`.

### Requirement 3 [REQ-F-SHOWCASE-003]

**User Story:** As a showcase viewer, I want a deterministic dashboard render artifact, so that the repo has a smoke-testable first frontend boundary before a full Next.js app exists.

#### Acceptance Criteria

1. When given a dashboard summary, the renderer shall produce stable HTML containing leaderboard, allocation/regime, rebalance, and evidence sections.
2. If the summary contains missing optional data, the renderer shall still produce a conservative warning instead of hiding the gap.
3. While no Next.js runtime exists, the review shall label live-demo readiness as `CONDITIONAL` or `hybrid`, not production/demo ready.
