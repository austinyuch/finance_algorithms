# Design — E Tier3 Retraining Evidence

## Overview

The E Tier3 readiness gate now has fail-closed evidence slots, and the serving slot has an executable local smoke artifact. This slice adds the same executable proof boundary for retraining: a local retrain callable must execute, return `status=completed`, preserve `no_alpha_claim`, and include OOS-net metrics before the artifact can be marked `status=proven`.

## Architecture

- `quantlab.mlops.experiment_registry.build_retraining_smoke_evidence(...)`
  - validates the registered experiment remains `no_alpha_claim`
  - executes `retrain(training_request)`
  - requires `status=completed`, a non-empty `run_id`, and out-of-sample net metrics
  - emits deterministic request/result digests
  - returns a `status=proven` artifact targeted only at `retraining_evidence`
- `validate_retraining_smoke_evidence(...)`
  - rejects malformed, overclaimed, unscoped, or non-local-smoke artifacts
- `build_tier3_readiness_gate(...)`
  - unchanged fail-closed gate; serving + retraining evidence still leaves automated drift monitoring evidence missing

## Test Coverage Declaration

- Unit/smoke: completed local retrain callable evidence generation and validation.
- Negative: failed result status, `alpha_claim`, missing OOS-net metrics, and defensive validator branches.
- PBT: deterministic digest stability for repeated equivalent retraining calls.
- Mutation: invert the retraining completion gate; the retraining proof test must kill the mutant.
- Line coverage: focused `pytest-cov` for `quantlab.mlops.experiment_registry`.

## Repo-side Closure vs External Execution Boundary

- **Repo-side closure**: local in-process retraining smoke proof artifact and fail-closed gate integration.
- **External execution**: production retraining scheduler, model registry promotion, serving endpoint deployment, and automated drift monitoring are not implemented here.
- **Readiness boundary**: this slice can prove only `retraining_evidence`; it must not set Tier3 `readiness=tier3_ready` without automated drift monitoring evidence.

## Contracts

No external contract is introduced. The local artifact shape is a repo-owned dictionary contract validated by `validate_retraining_smoke_evidence`.

## Components

| Component | Responsibility |
|---|---|
| `build_retraining_smoke_evidence` | Execute retrain callable and emit local smoke retraining evidence |
| `validate_retraining_smoke_evidence` | Enforce local-smoke/no-alpha/proven artifact shape |
| E tests | Cover happy path, fail-closed paths, PBT digest stability, and defensive branches |
| Mutation runner | Guard against completion-gate weakening |

## Failure Mode and Effects Analysis

| Risk ID | Failure Mode | Effect | Cause | Current Control | Planned Response | Task Trace |
|---|---|---|---|---|---|---|
| FMEA-ERETRAIN-1 | Failed retraining run still produces proven evidence | False-green retraining readiness | Status ignored | Tier3 gate requires evidence but evidence maps could overclaim | Completion gate, negative test, mutation target | T1/T2 |
| FMEA-ERETRAIN-2 | In-sample or gross metrics used as retraining proof | Backtest correctness regression | Metric extractor too permissive | Existing `_oos_net_metrics` rejects missing OOS-net metrics | Reuse `_oos_net_metrics`, negative test, coverage branch | T1/T2 |
| FMEA-ERETRAIN-3 | Local smoke is mistaken for production retraining orchestration | Overstated UAT/production readiness | Evidence naming too broad | Tier3 gate remains fail-closed | `retraining_status=local_smoke`, review boundary, gate remains `not_ready` | T1/T3 |

## Risk Response and Mitigation Plan

- Prevent: reject failed retraining status, alpha-claim results, missing run IDs, and missing OOS-net metrics.
- Detect: mutation target `e-retraining-smoke-status-gate` plus focused line coverage.
- Contain: evidence is scoped to `retraining_evidence` and `local_smoke`; the readiness gate still requires automated drift monitoring evidence.

## Error Handling

The builder raises `ValueError` for missing `observed_at`, empty training requests, empty results, non-completed retraining status, alpha-claim result payloads, missing run IDs, and missing out-of-sample net metrics.

## Evaluation Criteria

- `uv run pytest -q tests/quantlab/test_e_1_experiment_registry.py -k retraining_smoke`
- `uv run pytest --cov=quantlab.mlops.experiment_registry --cov-report=term-missing tests/quantlab/test_e_1_experiment_registry.py`
- `uv run python scripts/run_mutation_spot_checks.py --only e-retraining-smoke-status-gate`
- `uv run pytest -q`
- `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py --ignore-missing-imports`
- `uv run lint-imports`

## Traceability References

- REQ-E-RETRAIN-001 -> `build_retraining_smoke_evidence`, retraining smoke tests, mutation target.
- REQ-E-RETRAIN-002 -> `build_tier3_readiness_gate` integration assertion, PBT digest test, review boundary.
