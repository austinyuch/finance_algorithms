# Requirements — D Return/Risk Forecast Model

## Introduction

This spec adds the second Epic D model slice after the first deterministic regime model. It introduces a framework-light return/risk forecaster that estimates expected returns and risk from PIT price history, converts forecasts into portfolio weights through the existing C optimizer, and logs OOS-net comparisons against a static baseline.

## Dependencies, Impacts & CRs

- [Depends On: a0-backtest-foundation] PIT provider, vectorized engine, OOS-net result store.
- [Depends On: b-data-platform] vintage/PIT data semantics.
- [Depends On: c-portfolio-core] `optimize_max_return_under_vol` and strategy adapter patterns.
- [Depends On: d-first-regime-model] Epic D claim-boundary and no-alpha writeup posture.
- [Impacts: none] This slice is additive and does not change completed A0/B/C/D first-slice behavior.
- [Open Change Requests: none]

## Repo-side Closure vs External Execution

- **Repo-side Closure:** deterministic forecast model, allocation strategy, integration benchmark helper, tests, mutation check, and governance refresh.
- **External Execution:** GPU framework training, TensorFlow/JAX/PyTorch model variants, and Tier3 MLOps are not included.
- **External Blockers / Constraints:** None.

## Requirements

### Requirement 1 [REQ-D-FORECAST-001]

**User Story:** As a QuantLab maintainer, I want a PIT-safe return/risk forecast, so that D can add a second model family without using future prices.

#### Acceptance Criteria

1. When the forecaster receives sufficient as-of price history, it shall return one forecast per configured symbol using only rows available at or before `asof`.
2. If history is insufficient or invalid, the forecaster shall mark the forecast status conservatively and avoid non-finite expected return or volatility values.
3. When generated repeatedly from the same data and configuration, forecasts shall be deterministic.

### Requirement 2 [REQ-D-ALLOC-001]

**User Story:** As a strategy researcher, I want forecast-driven allocation weights, so that return/risk forecasts can be evaluated in the same A0 OOS-net harness as baselines.

#### Acceptance Criteria

1. When forecasts are available, the strategy shall produce long-only weights that sum to one.
2. If forecasts are degraded, the strategy shall fall back to equal weights and expose fallback metadata.
3. The strategy metadata shall include `claim_boundary = no_alpha_claim` and the latest forecast status.

### Requirement 3 [REQ-D-BENCH-001]

**User Story:** As a reviewer, I want an OOS-net benchmark report for the return/risk model, so that model output is compared honestly against a simple baseline.

#### Acceptance Criteria

1. When the benchmark runs, it shall log both the forecast strategy and static baseline to the result store.
2. The benchmark shall return leaderboard rows with non-null OOS-net Sharpe values where the configured date range supports walk-forward evaluation.
3. The benchmark report shall keep `claim_boundary = no_alpha_claim`.
