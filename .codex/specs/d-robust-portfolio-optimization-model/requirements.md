# Requirements — D Robust Portfolio Optimization Model

## Introduction

This spec adds the third Epic D model family: a robust portfolio optimization model. It estimates stress-adjusted expected returns from PIT historical returns by penalizing downside semideviation, then allocates through the existing C optimizer and evaluates against a static baseline in the A0 OOS-net harness.

## Dependencies, Impacts & CRs

- [Depends On: a0-backtest-foundation] PIT provider, backtest engine, OOS-net result store.
- [Depends On: c-portfolio-core] max-return-under-vol optimizer.
- [Depends On: d-return-risk-forecast-model] D claim-boundary pattern and benchmark wiring style.
- [Impacts: none] Additive model module only.
- [Open Change Requests: none]

## Repo-side Closure vs External Execution

- **Repo-side Closure:** deterministic robust optimizer model, strategy adapter, benchmark helper, tests, mutation, coverage, and governance update.
- **External Execution:** GPU training, live production deployment, and Tier3 MLOps are excluded.
- **External Blockers / Constraints:** None.

## Requirements

### Requirement 1 [REQ-D3-ROBUST-001]

**User Story:** As a strategy researcher, I want stress-adjusted return estimates, so that the model does not blindly chase high average returns with high downside risk.

#### Acceptance Criteria

1. When sufficient PIT history exists, the model shall compute finite stress-adjusted expected returns for each symbol.
2. If a symbol has insufficient or invalid history, the model shall mark the estimate degraded and avoid non-finite values.
3. When downside penalty increases, a high-downside asset's adjusted return shall not increase.

### Requirement 2 [REQ-D3-ALLOC-001]

**User Story:** As a QuantLab maintainer, I want robust optimized weights, so that D has a portfolio-optimization model family evaluated through the same A0 harness.

#### Acceptance Criteria

1. When model estimates are valid, the strategy shall produce long-only weights summing to one.
2. If estimates degrade, the strategy shall fall back to equal weights and expose degraded metadata.
3. Strategy metadata shall preserve `claim_boundary = no_alpha_claim`.

### Requirement 3 [REQ-D3-BENCH-001]

**User Story:** As a reviewer, I want OOS-net benchmark evidence, so that the robust optimizer is compared honestly with a simple baseline.

#### Acceptance Criteria

1. When benchmarked, the model and static baseline shall both be logged to the result store.
2. The benchmark shall return non-null OOS-net Sharpe rows when the date range supports walk-forward evaluation.
3. The benchmark report shall retain `claim_boundary = no_alpha_claim`.
