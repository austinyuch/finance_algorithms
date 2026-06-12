# Design — E Tier3 Serving Evidence

## Overview

The current E Tier3 gate correctly fails closed, but the serving evidence slot previously accepted only a caller-provided mapping. This slice adds a local, executable smoke-evidence builder that calls a real health function and prediction function before emitting a `serving_smoke_evidence` artifact.

## Architecture

- `quantlab.mlops.experiment_registry.build_serving_smoke_evidence(...)`
  - validates the registered experiment remains `no_alpha_claim`
  - executes `health_check()`
  - executes `predict(sample_request)`
  - emits deterministic request/prediction digests
  - returns a `status=proven` artifact targeted only at `serving_evidence`
- `validate_serving_smoke_evidence(...)`
  - rejects malformed, unhealthy, overclaimed, or unscoped artifacts
- `build_tier3_readiness_gate(...)`
  - unchanged fail-closed gate; serving evidence alone still leaves retraining and automated drift evidence missing

## Test Coverage Declaration

- Unit/smoke: healthy local callable evidence generation and validation.
- Negative: unhealthy health payload and `alpha_claim` prediction rejection.
- PBT: deterministic digest stability for repeated equivalent smoke calls.
- Mutation: invert the health gate; the serving proof test must kill the mutant.

## Repo-side Closure vs External Execution Boundary

- **Repo-side closure**: local in-process serving smoke proof artifact and fail-closed gate integration.
- **External execution**: production service deployment, live network serving, retraining jobs, and automated drift monitoring are not implemented here.
- **Readiness boundary**: this slice can prove only `serving_evidence`; it must not set Tier3 `readiness=tier3_ready`.

## Contracts

No external contract is introduced. The local artifact shape is a repo-owned dictionary contract validated by `validate_serving_smoke_evidence`.

## Components

| Component | Responsibility |
|---|---|
| `build_serving_smoke_evidence` | Execute health and predict callables and emit evidence |
| `validate_serving_smoke_evidence` | Enforce local-smoke/no-alpha/proven artifact shape |
| E tests | Cover happy path, fail-closed path, PBT digest stability |
| Mutation runner | Guard against health-gate weakening |

## Failure Mode and Effects Analysis

| Risk ID | Failure Mode | Effect | Cause | Current Control | Planned Response | Task Trace |
|---|---|---|---|---|---|---|
| FMEA-ESERVE-1 | Unhealthy endpoint still produces proven evidence | False-green serving readiness | Health status ignored | Existing Tier3 gate is fail-closed but evidence maps were caller supplied | Health gate, negative test, mutation target | T1/T2 |
| FMEA-ESERVE-2 | Local smoke is mistaken for production serving | Overstated UAT/production readiness | Evidence naming too broad | Tier3 gate requires three evidence keys | `serving_status=local_smoke`, review boundary, gate remains `not_ready` | T1/T3 |
| FMEA-ESERVE-3 | Prediction alpha claim leaks into evidence | Stakeholder overclaim | Prediction payload not checked | Registry rejects alpha entries | Prediction claim-boundary rejection test | T1/T2 |

## Risk Response and Mitigation Plan

- Prevent: reject unhealthy health payloads and alpha-claim predictions.
- Detect: mutation target `e-serving-smoke-health-gate`.
- Contain: evidence is scoped to `serving_evidence` and `local_smoke`; the readiness gate still requires retraining and automated drift evidence.

## Error Handling

The builder raises `ValueError` for missing `observed_at`, empty sample requests, unhealthy health payloads, empty predictions, and alpha-claim prediction payloads.

## Evaluation Criteria

- `uv run pytest -q tests/quantlab/test_e_1_experiment_registry.py -k serving_smoke`
- `uv run python scripts/run_mutation_spot_checks.py --only e-serving-smoke-health-gate`
- `uv run pytest -q`
- `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py --ignore-missing-imports`
- `uv run lint-imports`

## Traceability References

- REQ-E-SERVE-001 -> `build_serving_smoke_evidence`, serving smoke tests, mutation target.
- REQ-E-SERVE-002 -> `build_tier3_readiness_gate` integration assertion, PBT digest test, review boundary.
