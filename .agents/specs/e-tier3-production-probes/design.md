# Design — E Tier3 Production Probes

## Overview

This slice adds governed constructors for production-tier E evidence. The existing Tier3 gate already requires `evidence_tier=production`; the new builders make that tier harder to spoof by requiring allowlisted external identity URI schemes, UTC observation timestamps, non-local endpoints/jobs, no-alpha claim boundaries, and deterministic request/result digests.

## Test Coverage Declaration

- Unit tests cover happy path and fail-closed rejection for serving, retraining, and drift monitoring evidence.
- PBT covers non-production serving endpoint rejection across localhost and non-HTTPS variants.
- Mutation tests cover the production endpoint gate, production retraining status
  gate, traceable external HTTPS proof URL gate, UTC `observed_at` gate,
  identity-scheme gate, artifact URI gates, binding gate, and drift threshold
  gate.
- No live production endpoint is required for repo closure; live external execution remains a separate runtime proof.

## Repo-side Closure vs External Execution Boundary

- Repo-side closure is the evidence model, validator, tests, and governance update.
- External execution is the actual production serving endpoint, retraining orchestrator, and drift monitor.
- Review verdict must remain conditional unless external proof payloads are available.

## Components

| Component | Responsibility |
|---|---|
| `_is_production_uri` | Reject local, in-process, and non-HTTPS endpoint identities. |
| `_require_external_proof_id` | Require a traceable external HTTPS URL on production artifacts. |
| `_require_utc_observed_at` | Require production evidence timestamps to be parseable UTC timestamps instead of free-form labels or timezone-less dates. |
| `build_production_serving_evidence` / validator | Normalize serving health/prediction proof and reject local endpoints or alpha claims. |
| `_is_external_artifact_uri` | Allow only governed remote artifact URI schemes (`https`, `s3`, `gs`, `az`, `abfs`, `abfss`) and reject local, bare, non-TLS HTTP, or control-plane URI schemes. |
| `_require_external_identity` | Allow only governed production identity URI schemes (`https`, `github-actions`) and reject local, bare, non-TLS HTTP, shell, or file-transfer URI schemes. |
| `build_production_retraining_evidence` / validator | Normalize production retraining run proof and reject local runners, unsupported identity schemes, incomplete runs, alpha claims, unsupported artifact URI schemes, or missing OOS-net metrics. |
| `build_production_automated_drift_monitoring_evidence` / validator | Normalize production drift monitor proof and reject local monitors, unsupported identity schemes, unsupported statuses, alpha claims, or missing deltas. |

## Failure Mode and Effects Analysis

| Risk ID | Failure Mode | Effect | Current Control | Planned Response | Task Trace |
|---|---|---|---|---|---|
| FMEA-E-PROD-001 | Localhost endpoint marked production | Tier3 false green | Current gate checks tier only | Reject localhost/in-process/non-HTTPS identities | Task 1 |
| FMEA-E-PROD-002 | Local retraining output marked production | Production retraining overclaim | Local smoke tier exists | Require allowlisted external orchestrator URI, traceable HTTPS proof URL, completed run, allowlisted remote artifact URI, OOS-net metrics | Task 2 |
| FMEA-E-PROD-003 | Assessed/local drift report marked production monitor | Drift monitoring overclaim | Local automated smoke tier exists | Require allowlisted external monitor URI, traceable HTTPS proof URL, supported status, metric deltas | Task 3 |
| FMEA-E-PROD-004 | Hand-written map or plain ticket ID bypasses validation | Review consumes unchecked evidence | Gate accepts structural production maps | Add validators and tests for wrong kind/target/tier/proof URI | Task 4 |
| FMEA-E-PROD-005 | Valid production evidence for a different experiment is paired with a manifest | Tier3 ready is claimed for the wrong model/run lineage | Evidence artifacts carry experiment ids but gate did not compare them to the manifest | Require all production evidence artifacts to share one experiment id that appears in `manifest.experiment_ids` | Task 4 |
| FMEA-E-PROD-006 | Non-artifact external-looking URI accepted as production artifact | A hand-written `http://`, `ftp://`, `ssh://`, or control-plane URI can masquerade as durable production artifact storage | Earlier gate required only scheme and authority | Restrict manifest/retraining artifacts to allowlisted remote artifact schemes | Task 4 |
| FMEA-E-PROD-007 | Non-governed external-looking orchestrator or monitor URI accepted as production identity | A hand-written `http://`, `ftp://`, or `ssh://` identity can masquerade as governed production orchestration or monitoring | Earlier identity gate required only scheme and authority | Restrict production orchestrator/monitor identities to allowlisted identity schemes | Task 4 |
| FMEA-E-PROD-008 | Free-form observed timestamp accepted as production evidence time | `today`, date-only, local-time, or timezone-less strings can make stale or unverifiable proof look current | Earlier builders required only non-empty `observed_at` | Require UTC timestamps in production builders and validators | Task 4 |

## Risk Response and Mitigation Plan

- Prevent: production builders reject local identities, unsupported identity
  URI schemes, alpha claims, and plain proof IDs that are not traceable external
  HTTPS URLs.
- Prevent: final manifest and retraining artifact URIs are restricted to
  allowlisted remote artifact schemes rather than any URI with authority.
- Prevent: production evidence `observed_at` values must be UTC timestamps, not
  free-form labels or local-time strings.
- Detect: validators reject malformed or hand-written artifacts.
- Detect: the Tier3 gate rejects otherwise-valid production evidence when experiment ids are not bound to the manifest.
- Contain: absence of external proof leaves Tier3 `not_ready`; local smoke remains local-smoke only.

## EDD

- `uv run pytest -q tests/quantlab/test_e_1_experiment_registry.py -k production`
- `uv run pytest --cov=quantlab.mlops.experiment_registry --cov-report=term-missing tests/quantlab/test_e_1_experiment_registry.py`
- `uv run python scripts/run_mutation_spot_checks.py --only e-production-serving-endpoint-gate`
- `uv run python scripts/run_mutation_spot_checks.py --only e-production-retraining-status-gate`
- `uv run python scripts/run_mutation_spot_checks.py --only e-production-external-proof-uri-gate`
- `uv run python scripts/run_mutation_spot_checks.py --only e-tier3-experiment-binding-gate`
- `uv run pytest -q`
- `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py --ignore-missing-imports`
- `uv run lint-imports`

## Traceability References

- `REQ-E-PRODPROBE-001` -> serving production evidence builder/validator.
- `REQ-E-PRODPROBE-002` -> retraining production evidence builder/validator.
- `REQ-E-PRODPROBE-003` -> automated drift monitoring production evidence builder/validator.
- `REQ-E-PRODPROBE-004` -> Tier3 gate integration and validation failure tests.
