# Requirements — E Tier3 Production Probes

## Introduction

The previous E production-evidence gate requires `evidence_tier=production`, but production evidence still has no governed construction path. This slice adds production-tier evidence builders and validators that reject local, in-process, localhost, alpha-claim, incomplete, or unsupported proof payloads before those payloads can satisfy Tier3 readiness.

## Dependencies, Impacts & CRs

- [Depends On: e-mlops-tier3-lite, e-tier3-readiness-gate, e-tier3-serving-evidence, e-tier3-retraining-evidence, e-tier3-production-evidence-gate]
- [Impacts: e-tier3-production-evidence-gate]
- [Open Change Requests: none]

## Repo-side Closure vs External Execution

- **Repo-side Closure**: add production evidence builders/validators, tests, mutation checks, and governance evidence updates.
- **External Execution**: real production serving endpoint, production retraining orchestration, and production automated drift monitoring service must execute outside this repo and provide non-local proof payloads.
- **External Blockers / Constraints**: without external proof payloads, Tier3 readiness remains `not_ready`; local smoke artifacts remain `evidence_tier=local_smoke`.

## Requirements

### Requirement 1 [REQ-E-PRODPROBE-001]

**User story:** As a QuantLab reviewer, I want serving production evidence to reject local endpoints, so localhost smoke tests cannot satisfy production readiness.

#### Acceptance Criteria

1. When a serving evidence payload uses `localhost`, `127.0.0.1`, `in_process`, or a non-HTTPS endpoint, then the system shall reject it as non-production.
2. When a serving evidence payload contains a healthy production HTTPS endpoint, no-alpha prediction payload, non-empty request, UTC `observed_at`, and external proof id, then the system shall emit `readiness_evidence_for=serving_evidence` and `evidence_tier=production`.
3. If a serving prediction payload claims `alpha_claim`, then the system shall reject the evidence.

### Requirement 2 [REQ-E-PRODPROBE-002]

**User story:** As a maintainer, I want production retraining evidence to prove external orchestration, so local runner output cannot masquerade as production retraining readiness.

#### Acceptance Criteria

1. When retraining evidence is produced from `in_process`, `local_smoke`, or a blank orchestrator, then the system shall reject it.
2. When retraining evidence includes an allowlisted external orchestrator URI (`https` or `github-actions`), completed run status, run id, UTC `observed_at`, allowlisted remote artifact URI (`https`, `s3`, `gs`, `az`, `abfs`, or `abfss`), external proof id, and out-of-sample net metrics, then the system shall emit `readiness_evidence_for=retraining_evidence` and `evidence_tier=production`.
3. If retraining evidence lacks out-of-sample net metrics or claims `alpha_claim`, then the system shall reject it.

### Requirement 3 [REQ-E-PRODPROBE-003]

**User story:** As a reviewer, I want automated drift monitoring production evidence to prove external monitor operation, so assessed/local drift checks cannot satisfy production readiness.

#### Acceptance Criteria

1. When drift monitoring evidence uses a local monitor identity, then the system shall reject it.
2. When drift monitoring evidence includes an allowlisted external monitor URI (`https` or `github-actions`), UTC `observed_at`, stable or drift-detected status, metric deltas, explicit positive threshold, external proof id, and no-alpha claim boundary, then the system shall emit `readiness_evidence_for=automated_drift_monitoring_evidence` and `evidence_tier=production`.
3. If drift monitoring evidence has an unsupported status, empty metric deltas, or `alpha_claim`, then the system shall reject it.

### Requirement 4 [REQ-E-PRODPROBE-004]

**User story:** As a release reviewer, I want only governed production evidence to make Tier3 ready, so arbitrary production-looking maps do not bypass validators.

#### Acceptance Criteria

1. When all three governed production evidence artifacts are valid, then the Tier3 gate may return `tier3_ready`.
2. If any artifact has a wrong artifact kind, wrong readiness target, wrong tier, missing proof id, non-production identity, non-allowlisted identity scheme, or non-UTC `observed_at`, then its validator shall fail before review can use it.
3. If otherwise-valid production evidence artifacts do not all reference the same experiment id from the Tier3 manifest, then the Tier3 gate shall remain `not_ready`.
4. If the Tier3 manifest or retraining artifact URI uses a local, bare, non-TLS HTTP, shell/control-plane, or otherwise non-allowlisted scheme, then final readiness shall remain `not_ready` or the production artifact validator shall reject it.
