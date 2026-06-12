# Requirements — E Tier3 Serving Evidence

## Introduction

This slice reduces E Tier3 false-green risk by adding a repo-side local serving smoke evidence artifact. It proves that a real health callable and predict callable were executed for a registered no-alpha experiment. It does not implement production serving, retraining, or automated drift monitoring, and it must not make the Tier3 gate ready by itself.

## Dependencies, Impacts & CRs

- [Depends On: e-mlops-tier3-lite, e-tier3-readiness-gate]
- [Impacts: e-mlops-tier3-lite, e-tier3-readiness-gate]
- [Open Change Requests: none]

## Repo-side Closure vs External Execution

- **Repo-side Closure**: add `serving_smoke_evidence` builder/validator, tests, mutation target, and registry/test rollup updates.
- **External Execution**: production serving deployment, retraining orchestration, and automated drift monitoring remain outside this slice.
- **External Blockers / Constraints**: Tier3 readiness remains `not_ready` until all required evidence keys are independently `status=proven`.

## Requirements

### Requirement 1 [REQ-E-SERVE-001]

**User story:** As a QuantLab maintainer, I want serving evidence to come from an executed health and predict path, so that arbitrary evidence maps do not create false-green readiness.

#### Acceptance Criteria

1. When a registered no-alpha experiment passes a healthy serving smoke and prediction call, then the system shall produce `artifact_kind=serving_smoke_evidence`, `status=proven`, and `readiness_evidence_for=serving_evidence`.
2. If the serving health payload is not healthy, then the system shall reject the evidence instead of creating a proven artifact.
3. If the prediction payload claims `alpha_claim`, then the system shall reject the evidence.

### Requirement 2 [REQ-E-SERVE-002]

**User story:** As a reviewer, I want serving evidence to remain scoped to local smoke proof, so that it cannot imply full Tier3 readiness.

#### Acceptance Criteria

1. When the Tier3 readiness gate receives only serving smoke evidence, then the gate shall remain `not_ready`.
2. When serving smoke evidence is produced, then it shall retain `claim_boundary=no_alpha_claim` and `serving_status=local_smoke`.
3. When repeated smoke runs use the same request and prediction output, then the request and prediction digests shall be deterministic.
