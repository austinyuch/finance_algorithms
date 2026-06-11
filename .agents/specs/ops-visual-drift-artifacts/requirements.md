# Requirements — Ops Visual Drift Artifacts

## Introduction

This lane handles the next five gaps after the tier3/public lane shipped: B scheduled snapshot real-ops proof, F visual diff thresholding, E drift monitoring first real slice, B external source-contract restoration decision evidence, and D evaluation artifact expansion.

## Dependencies, Impacts & CRs

- [Depends On: b-data-platform, b-snapshot-ops-gate, f-public-static-showcase, e-mlops-tier3-lite, d-model-family-evaluation]
- [Impacts: b-data-platform, b-snapshot-ops-gate, f-public-static-showcase, e-mlops-tier3-lite, d-model-family-evaluation]
- [Open Change Requests: CR-B-SCHEDULE-REAL-OPS, CR-F-VISUAL-DIFF, CR-E-DRIFT-FIRST-SLICE, CR-B-STOOQ-REOPEN-EVIDENCE, CR-D-EVAL-ARTIFACTS]

## Repo-side Closure vs External Execution

- **Repo-side Closure:** add deterministic workflow/proof builders, visual diff threshold contracts, drift assessment reports, source-contract reopen evidence helpers, D evaluation artifact writers, tests, mutation checks, and governance updates.
- **External Execution:** GitHub Actions scheduled execution after merge and any future live source probes.
- **External Blockers / Constraints:** Stooq default restoration remains blocked until non-empty live close rows are proven; E Tier3 still cannot claim serving/retraining.

## Requirements

### Requirement 1 [REQ-OVD-B-SCHEDULE]

**User story:** As the QuantLab operator, I want scheduled snapshot ops proof to include a real workflow/run contract, so that daily snapshot readiness is not just a helper function.

#### Acceptance Criteria

1. When a scheduled snapshot workflow is inspected, then the repo should expose a deterministic proof artifact that records workflow trigger, command, report path, exit status, and append-only schedule report status.
2. If a scheduled run exits nonzero, then the proof status should be degraded and must not be reported as clean.
3. When the scheduled proof is generated from a dry-run smoke, then it should be labeled as smoke evidence rather than live production capture.

### Requirement 2 [REQ-OVD-F-VISUAL-DIFF]

**User story:** As a dashboard reviewer, I want browser visual regression to compare current evidence against a baseline with a threshold, so that a screenshot hash is not mistaken for a visual regression gate.

#### Acceptance Criteria

1. When current and baseline browser visual evidence are compared, then the result should include current hash, baseline hash, mismatch ratio, threshold, and pass/fail status.
2. If mismatch ratio exceeds the configured threshold, then the visual diff gate should fail.
3. When malformed hashes or thresholds are supplied, then the gate should reject them instead of producing proof.

### Requirement 3 [REQ-OVD-E-DRIFT]

**User story:** As a model lifecycle reviewer, I want E Tier3 to produce a real drift assessment from metrics, so that drift monitoring moves beyond skeleton-only without claiming serving or retraining.

#### Acceptance Criteria

1. When reference and current metrics are provided, then the drift report should compute metric deltas and classify stable versus drift-detected by threshold.
2. If claim boundary or serving status is overclaimed, then validation should reject the report.
3. When generated for registered experiments, then the report should preserve `no_alpha_claim` and `monitoring_status=assessed_not_automated`.

### Requirement 4 [REQ-OVD-B-SOURCE]

**User story:** As a data-source maintainer, I want Stooq restoration to require concrete live close-row evidence, so that default sources are not re-enabled by optimistic source-health status alone.

#### Acceptance Criteria

1. When Stooq is blocked/default-disabled, then the decision should remain `keep_default_disabled`.
2. If Stooq is available but no non-empty live close rows are supplied, then the decision should remain non-default with required evidence.
3. When non-empty live close rows are supplied with valid event dates and close values, then the decision may become `eligible_for_opt_in_review` but still must not silently default-enable.

### Requirement 5 [REQ-OVD-D-ARTIFACTS]

**User story:** As a portfolio-lab reviewer, I want D model-family evaluation to emit checksumed artifacts, so that dashboard/history consumers can use stable report files instead of ad hoc in-memory summaries.

#### Acceptance Criteria

1. When a model-family evaluation is built, then it should be serializable as an artifact with checksum, generated timestamp, row count, and source.
2. If the evaluation report overclaims alpha or lacks OOS-net authority, then artifact validation should reject it.
3. When artifact rows are reordered by evaluation ranking, then checksum and row count should remain deterministic for the serialized artifact.
