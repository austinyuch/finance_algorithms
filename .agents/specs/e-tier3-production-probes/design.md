# Design — E Tier3 Production Probes

## Overview

This slice adds governed constructors for production-tier E evidence. The existing Tier3 gate already requires `evidence_tier=production`; the new builders make that tier harder to spoof by requiring external identities, non-local endpoints/jobs, no-alpha claim boundaries, and deterministic request/result digests.

## Test Coverage Declaration

- Unit tests cover happy path and fail-closed rejection for serving, retraining, and drift monitoring evidence.
- PBT covers non-production serving endpoint rejection across localhost and non-HTTPS variants.
- Mutation tests cover the production endpoint gate, production retraining status gate,
  and traceable external proof URI gate.
- No live production endpoint is required for repo closure; live external execution remains a separate runtime proof.

## Repo-side Closure vs External Execution Boundary

- Repo-side closure is the evidence model, validator, tests, and governance update.
- External execution is the actual production serving endpoint, retraining orchestrator, and drift monitor.
- Review verdict must remain conditional unless external proof payloads are available.

## Components

| Component | Responsibility |
|---|---|
| `_is_production_uri` | Reject local, in-process, and non-HTTPS endpoint identities. |
| `_require_external_proof_id` | Require a traceable non-local external URI on production artifacts. |
| `build_production_serving_evidence` / validator | Normalize serving health/prediction proof and reject local endpoints or alpha claims. |
| `build_production_retraining_evidence` / validator | Normalize production retraining run proof and reject local runners, incomplete runs, alpha claims, or missing OOS-net metrics. |
| `build_production_automated_drift_monitoring_evidence` / validator | Normalize production drift monitor proof and reject local monitors, unsupported statuses, alpha claims, or missing deltas. |

## Failure Mode and Effects Analysis

| Risk ID | Failure Mode | Effect | Current Control | Planned Response | Task Trace |
|---|---|---|---|---|---|
| FMEA-E-PROD-001 | Localhost endpoint marked production | Tier3 false green | Current gate checks tier only | Reject localhost/in-process/non-HTTPS identities | Task 1 |
| FMEA-E-PROD-002 | Local retraining output marked production | Production retraining overclaim | Local smoke tier exists | Require external orchestrator, traceable proof URI, completed run, artifact URI, OOS-net metrics | Task 2 |
| FMEA-E-PROD-003 | Assessed/local drift report marked production monitor | Drift monitoring overclaim | Local automated smoke tier exists | Require external monitor identity, traceable proof URI, supported status, metric deltas | Task 3 |
| FMEA-E-PROD-004 | Hand-written map or plain ticket ID bypasses validation | Review consumes unchecked evidence | Gate accepts structural production maps | Add validators and tests for wrong kind/target/tier/proof URI | Task 4 |

## Risk Response and Mitigation Plan

- Prevent: production builders reject local identities, alpha claims, and plain
  proof IDs that are not traceable external URIs.
- Detect: validators reject malformed or hand-written artifacts.
- Contain: absence of external proof leaves Tier3 `not_ready`; local smoke remains local-smoke only.

## EDD

- `uv run pytest -q tests/quantlab/test_e_1_experiment_registry.py -k production`
- `uv run pytest --cov=quantlab.mlops.experiment_registry --cov-report=term-missing tests/quantlab/test_e_1_experiment_registry.py`
- `uv run python scripts/run_mutation_spot_checks.py --only e-production-serving-endpoint-gate`
- `uv run python scripts/run_mutation_spot_checks.py --only e-production-retraining-status-gate`
- `uv run python scripts/run_mutation_spot_checks.py --only e-production-external-proof-uri-gate`
- `uv run pytest -q`
- `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py --ignore-missing-imports`
- `uv run lint-imports`

## Traceability References

- `REQ-E-PRODPROBE-001` -> serving production evidence builder/validator.
- `REQ-E-PRODPROBE-002` -> retraining production evidence builder/validator.
- `REQ-E-PRODPROBE-003` -> automated drift monitoring production evidence builder/validator.
- `REQ-E-PRODPROBE-004` -> Tier3 gate integration and validation failure tests.
