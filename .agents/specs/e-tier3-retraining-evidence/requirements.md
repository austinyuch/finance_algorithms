# Requirements — E Tier3 Retraining Evidence

## Introduction

This slice reduces E Tier3 false-green risk by adding a repo-side local retraining smoke evidence artifact. It proves that a real retrain callable executed for a registered no-alpha experiment and returned a completed run with out-of-sample net metrics. It does not implement production retraining orchestration or automated drift monitoring, and it must not make the Tier3 gate ready by itself.

## Dependencies, Impacts & CRs

- [Depends On: e-mlops-tier3-lite, e-tier3-readiness-gate, e-tier3-serving-evidence]
- [Impacts: e-mlops-tier3-lite, e-tier3-readiness-gate]
- [Open Change Requests: none]

## Repo-side Closure vs External Execution

- **Repo-side Closure**: add `retraining_smoke_evidence` builder/validator, tests, mutation target, focused line coverage, and registry/test rollup updates.
- **External Execution**: production retraining scheduler/orchestrator and automated drift monitoring remain outside this slice.
- **External Blockers / Constraints**: Tier3 readiness remains `not_ready` until serving, retraining, and automated drift monitoring evidence keys are independently `status=proven`; current serving/retraining evidence are local-smoke only.

## Requirements

### Requirement 1 [REQ-E-RETRAIN-001]

**User story:** As a QuantLab maintainer, I want retraining evidence to come from an executed retrain path, so that arbitrary maps or failed jobs do not create false-green readiness.

#### Acceptance Criteria

1. When a registered no-alpha experiment completes a local retraining smoke run, then the system shall produce `artifact_kind=retraining_smoke_evidence`, `status=proven`, and `readiness_evidence_for=retraining_evidence`.
2. If the retraining result status is not `completed`, then the system shall reject the evidence instead of creating a proven artifact.
3. If the retraining result claims `alpha_claim`, then the system shall reject the evidence.
4. If the retraining result lacks out-of-sample net metrics, then the system shall reject the evidence.

### Requirement 2 [REQ-E-RETRAIN-002]

**User story:** As a reviewer, I want retraining evidence to remain scoped to local smoke proof, so that it cannot imply full Tier3 readiness.

#### Acceptance Criteria

1. When the Tier3 readiness gate receives serving and retraining local smoke evidence but no automated drift monitoring evidence, then the gate shall remain `not_ready`.
2. When retraining smoke evidence is produced, then it shall retain `claim_boundary=no_alpha_claim` and `retraining_status=local_smoke`.
3. When repeated smoke runs use the same request and retraining output, then the request and result digests shall be deterministic.
