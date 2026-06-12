# Requirements — E Tier3 Readiness Gate

## Context

E has registry snapshots, artifact manifests, and assessed drift reports, but the project still intentionally lacks serving, retraining, and automated drift monitoring. This continuation adds a fail-closed readiness gate so artifact-only evidence cannot be promoted to Tier3 readiness by wording drift or downstream aggregation.

## Scope

- [Depends On: e-mlops-tier3-lite, next-gaps-1-6-tier3-public, ops-visual-drift-artifacts]
- [Impacts: quantlab.mlops, TESTS.md, NEXT_STEPS.md, SPECS.md, RTM.md]
- Repo-side closure only. No serving runtime, retraining scheduler, or automated drift monitor is implemented in this slice.

## REQ-ETRG-001 — Fail-Closed Tier3 Readiness

**User Story:** As a reviewer, I want a single readiness gate that stays `not_ready` unless all Tier3 evidence classes are proven, so that artifact manifests cannot be overclaimed as production MLOps readiness.

#### Acceptance Criteria

1. Given an artifact-only Tier3 manifest, when the readiness gate is built without extra evidence, then it shall return `readiness=not_ready`.
2. Given partial evidence, when any required class is missing or not proven, then the gate shall list the missing evidence and remain `not_ready`.
3. Given serving, retraining, and automated drift monitoring evidence all marked `status=proven`, then the gate may return `readiness=tier3_ready`.

## REQ-ETRG-002 — Claim Boundary Preservation

**User Story:** As a maintainer, I want the gate to preserve the `no_alpha_claim` boundary and source manifest readiness, so that readiness aggregation does not erase the research-only context.

#### Acceptance Criteria

1. The gate shall validate the input Tier3 run manifest before classification.
2. The gate shall emit `claim_boundary=no_alpha_claim`.
3. The gate shall expose `source_manifest_readiness=artifact_manifest_only`.

## REQ-ETRG-003 — Regression Protection

**User Story:** As a maintainer, I want mutation coverage for the ready/not-ready branch, so that false-green readiness cannot silently regress.

#### Acceptance Criteria

1. A mutation that always emits `tier3_ready` shall be killed by the artifact-only readiness test.
2. Test registries shall record the new gate and mutation evidence.
