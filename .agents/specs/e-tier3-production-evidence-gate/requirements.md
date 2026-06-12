# Requirements — E Tier3 Production Evidence Gate

## Introduction

This slice hardens E Tier3 readiness against local-smoke and arbitrary-map false greens. Tier3 readiness can be satisfied only by correctly targeted production-tier evidence. The slice also adds local automated drift monitoring smoke evidence, but that evidence is explicitly scoped to repo-side automation proof and must not make Tier3 production-ready.

## Dependencies, Impacts & CRs

- [Depends On: e-mlops-tier3-lite, e-tier3-readiness-gate, e-tier3-serving-evidence, e-tier3-retraining-evidence]
- [Impacts: e-mlops-tier3-lite, e-tier3-readiness-gate]
- [Open Change Requests: none]

## Repo-side Closure vs External Execution

- **Repo-side Closure**: require `evidence_tier=production` plus correct readiness target for Tier3 readiness, mark local serving/retraining evidence as `local_smoke`, add local automated drift monitoring evidence builder/validator, tests, mutation targets, and governance updates.
- **External Execution**: production serving endpoint, production retraining orchestration, and production automated drift monitoring remain outside this slice.
- **External Blockers / Constraints**: Tier3 readiness remains `not_ready` unless all three production evidence keys are present with `status=proven`, correct `readiness_evidence_for`, and `evidence_tier=production`.

## Requirements

### Requirement 1 [REQ-E-PRODGATE-001]

**User story:** As a QuantLab reviewer, I want Tier3 readiness to require production-tier evidence, so arbitrary proven maps or local smoke artifacts cannot imply production readiness.

#### Acceptance Criteria

1. When evidence lacks `evidence_tier=production`, then the Tier3 gate shall keep the corresponding evidence key in `missing_evidence`.
2. When evidence has `status=proven` but the wrong `readiness_evidence_for`, then the Tier3 gate shall keep the corresponding evidence key in `missing_evidence`.
3. When all required evidence maps have `status=proven`, correct `readiness_evidence_for`, and `evidence_tier=production`, then the gate may return `tier3_ready`.

### Requirement 2 [REQ-E-PRODGATE-002]

**User story:** As a maintainer, I want local serving and retraining smoke evidence to be explicitly tiered, so governance cannot confuse smoke proof with production proof.

#### Acceptance Criteria

1. When local serving smoke evidence is produced, then it shall include `evidence_tier=local_smoke`.
2. When local retraining smoke evidence is produced, then it shall include `evidence_tier=local_smoke`.
3. When local serving and retraining smoke evidence are supplied to the Tier3 gate, then the gate shall remain `not_ready` without production-tier evidence.

### Requirement 3 [REQ-E-PRODGATE-003]

**User story:** As a QuantLab maintainer, I want automated drift monitoring evidence to come from an executed monitor path, so drift automation has repo-side smoke proof without overclaiming production readiness.

#### Acceptance Criteria

1. When a monitor callable returns `stable` or `drift_detected` with metric deltas, then the system shall produce `artifact_kind=automated_drift_monitoring_evidence`, `status=proven`, `monitoring_status=local_automated_smoke`, and `evidence_tier=local_smoke`.
2. If the monitor result has an unsupported status, then the system shall reject the evidence.
3. If the monitor result claims `alpha_claim`, then the system shall reject the evidence.
4. If the monitor result lacks metric deltas, then the system shall reject the evidence.
5. When the same monitor request and result are used repeatedly, then request and result digests shall be deterministic.
