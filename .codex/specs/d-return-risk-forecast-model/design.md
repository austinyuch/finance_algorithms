# Design — D Return/Risk Forecast Model

References: [requirements.md](./requirements.md), [SPECS.md](../SPECS.md), [d-first-regime-model review](../d-first-regime-model/review.md), [c-portfolio-core design](../c-portfolio-core/design.md).

## Overview

The second D model slice adds a deterministic return/risk forecast layer. It is intentionally framework-light and uses rolling PIT price history so that the model family can be evaluated before heavier PyTorch/TensorFlow/JAX lanes.

## Architecture

```mermaid
flowchart LR
  PIT[PointInTimeDataProvider.history(asof)] --> Forecast[ReturnRiskForecaster]
  Forecast --> Strategy[ForecastAllocationStrategy]
  Strategy --> Optimizer[C optimize_max_return_under_vol]
  Strategy --> Engine[A0 VectorizedEngine]
  Engine --> Store[LocalResultStore]
  Store --> Report[run_return_risk_forecast_benchmark]
```

## Test Coverage Declaration

- Unit: forecast status, non-finite fallback, metadata, and weight normalization.
- Property-Based: generated positive price paths produce finite forecasts and long-only weights summing to one.
- Integration: strategy + A0 runner + result store + static baseline produce OOS-net leaderboard rows.
- Smoke: benchmark helper returns a report with run IDs, leaderboard, and `no_alpha_claim`.
- Mutation: configured mutation that flips fallback status/claim boundary must be killed.
- Coverage: `pytest --cov=quantlab.models.return_risk --cov-report=term-missing` must exceed 80% line coverage.

## Repo-side Closure vs External Execution Boundary

Repo-side closure is the deterministic model and benchmark helper. Full ML framework variants and Tier3 MLOps remain future D/E lanes.

## Contracts

No generated contract is introduced. The model uses A0 `Strategy` protocol and existing C optimizer contracts.

## Components and Interfaces

- `ReturnRiskForecast`: immutable forecast data for a symbol.
- `ReturnRiskForecaster`: computes rolling annualized mean return and volatility from PIT history.
- `ForecastAllocationStrategy`: A0-compatible adapter that maps forecasts to optimized weights or equal-weight fallback.
- `run_return_risk_forecast_benchmark`: OOS-net benchmark against `StaticWeights`.

## Failure Mode and Effects Analysis

| Risk ID | Failure Mode | Effect | Cause | Current Control | Sev | Occ | Det | Planned Response | Task Trace |
|---|---|---|---|---|---:|---:|---:|---|---|
| FMEA-D2-01 | Forecast uses prices after `asof` | Lookahead bias | Incorrect history window | PIT provider and tests compare as-of gated paths | 10 | 3 | 3 | PBT and explicit asof mutation test | D2-1/D2-4 |
| FMEA-D2-02 | Degraded forecast still shown as alpha-capable | Overclaim | Missing status/claim metadata | `no_alpha_claim` default | 8 | 4 | 2 | Metadata and mutation tests | D2-2/D2-4 |
| FMEA-D2-03 | Optimizer receives NaN/zero risk | Runtime failure or false green | Flat or malformed prices | Conservative fallback | 7 | 4 | 3 | Unit tests for degraded forecasts | D2-1 |

## Risk Response and Mitigation Plan

- Prevent: compute only from `data.history(asof, ...)` and validate finite inputs.
- Detect: PBT, integration, and mutation tests.
- Contain: equal-weight fallback with explicit metadata when forecasts degrade.

## Error Handling

Invalid or insufficient price history produces degraded forecast status and equal-weight fallback. The benchmark raises only for too-short date ranges that cannot support A0 walk-forward evidence.

## Evaluation Standards

- Targeted D2 tests pass.
- D2 line coverage is at least 80%.
- D2 mutation spot check is killed.
- Full project `pytest`, `mypy`, and `lint-imports` pass before closeout.

## Traceability References

- `REQ-D-FORECAST-001` -> `ReturnRiskForecaster.forecast`
- `REQ-D-ALLOC-001` -> `ForecastAllocationStrategy.generate_signal`
- `REQ-D-BENCH-001` -> `run_return_risk_forecast_benchmark`
