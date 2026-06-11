# Requirements — Epic D:First Regime Model

> SDD Phase 1. Spec: `d-first-regime-model`.
> Upstream: `a0-backtest-foundation`, `b-data-platform`, `c-portfolio-core`.

## 0. Governance

- **Work classification:** `new spec`.
- **Depends On:** `a0-backtest-foundation`(Strategy/Engine/DataProvider/ResultStore), `b-data-platform`(PIT macro/price data), `c-portfolio-core`(future C-3 regime hook consumer).
- **Impacts:** `c-portfolio-core` C-3 may consume this spec's regime signal through an additive hook; no change to C baseline behavior in this first model spec.
- **First-slice boundary:** a deterministic, framework-light regime classifier that maps PIT macro/price features to a small regime label set and can be compared against simple baselines in A0 OOS-net reports.

## 1. Functional Requirements

### Requirement 1 [REQ-D-REGIME-001]

**User story:** As a quant research user, I want a point-in-time regime classifier so that portfolio experiments can condition rebalance decisions on market state without lookahead.

#### Acceptance Criteria

1. When the classifier builds features for `asof`, it must only use values available through the PIT provider at or before `asof`.
2. When required macro or price features are missing, it must return `unknown` or a documented fallback label instead of inventing data.
3. The label vocabulary must be stable and small enough for downstream C-3 rebalance hooks to consume deterministically.

### Requirement 2 [REQ-D-BASELINE-001]

**User story:** As a reviewer, I want regime experiments compared with simple baselines so that a model is not accepted just because it is more complex.

#### Acceptance Criteria

1. When the regime model is evaluated, the report must include at least one naive baseline such as static allocation or no-regime rebalance.
2. When leaderboard rows are produced, comparisons must use out-of-sample net metrics.
3. If the regime model does not beat the baseline, the writeup must say so explicitly and avoid alpha claims.

### Requirement 3 [REQ-D-HOOK-001]

**User story:** As a portfolio developer, I want the first regime model exposed behind a narrow signal interface so that C-3 can use it later without coupling portfolio code to a specific ML framework.

#### Acceptance Criteria

1. When downstream code requests a regime signal, it should receive a deterministic label plus metadata explaining feature availability.
2. The model implementation must not require `quantlab.engine` or `quantlab.data` to import ML frameworks.
3. The first slice may use a rules-based or sklearn-free classifier; heavier PyTorch/TensorFlow/JAX experiments remain later D lanes.

## 2. Out of Scope

- Full MLOps/Tier3 model registry, automated retraining, serving, or drift monitoring.
- NLP/event-driven models.
- Modifying C-3 rebalance behavior before the regime signal contract is proven.
