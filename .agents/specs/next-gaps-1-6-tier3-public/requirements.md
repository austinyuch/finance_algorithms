# Requirements — Next Gaps 1-6 Tier3/Public/Ops

## Introduction

This continuation lane handles the six highest-value follow-ups from the 2026-06-11 reassessment: F public hosting proof, F browser visual proof, E Tier3 first real slice, B scheduled snapshot ops, D real-source family evaluation, and B Stooq source-contract decision.

## Dependencies, Impacts & CRs

- [Depends On: f-public-static-showcase, f-public-demo-readiness, e-registry-durability-bridge, d-model-family-evaluation, b-snapshot-ops-gate, b-data-platform]
- [Impacts: f-public-static-showcase, f-public-demo-readiness, e-mlops-tier3-lite, e-registry-durability-bridge, d-model-family-evaluation, b-snapshot-ops-gate, b-data-platform]
- [Open Change Requests: CR-NG16-F-PUBLIC, CR-NG16-F-VISUAL, CR-NG16-E-TIER3-MANIFEST, CR-NG16-B-SCHEDULE, CR-NG16-D-REAL-SOURCE-EVAL, CR-NG16-B-STOOQ-DECISION]

## Repo-side Closure vs External Execution

- **Repo-side Closure:** Add typed evidence builders, validators, tests, mutation targets, scripts, generated `docs/` evidence, and governance updates.
- **External Execution:** GitHub Pages settings and hosted URL availability are external to the repo. This lane may configure Pages through GitHub API and record observed URL status, but must not claim proof unless `https://austinyuch.github.io/finance_algorithms/` returns HTTP 200.
- **External Blockers / Constraints:** Stooq remains source-contract blocked until a working endpoint/symbol map returns non-empty close rows.

## Requirements

### Requirement 1 [REQ-NG16-F-PUBLIC]

**User Story:** As a maintainer, I want public static showcase hosting evidence separated from local demo readiness, so that the project can claim public hosting only when GitHub Pages and the hosted URL are both observed.

#### Acceptance Criteria

1. When GitHub Pages is configured but the hosted URL is not HTTP 200, the manifest shall remain `configured_not_observed`.
2. When GitHub Pages is configured and the hosted URL returns HTTP 200, the manifest shall record the HTTP status and observation time; `hostingEvidence.status=proven` requires deployed `dataHash` parity, manifest-contract parity, and fresh standalone probe evidence.
3. If dashboard runtime readiness remains local-only, the dashboard payload shall continue to preserve `local_demo_only` and `no_alpha_claim`.

### Requirement 2 [REQ-NG16-F-VISUAL]

**User Story:** As a maintainer, I want browser screenshot evidence in addition to static visual contract hashes, so that visual regression proof is not overstated.

#### Acceptance Criteria

1. When a Chromium screenshot is captured from the exported static page, the system shall write browser visual evidence with a SHA-256 screenshot hash.
2. If screenshot evidence is malformed, the visual evidence builder shall reject it.
3. The static visual contract baseline shall remain deterministic and conservative.

### Requirement 3 [REQ-NG16-E-TIER3]

**User Story:** As a research operator, I want the first Tier3-like artifact manifest and drift report skeleton without serving claims, so that E can progress beyond registry-only without overbuilding full MLOps.

#### Acceptance Criteria

1. When an E registry snapshot is used, the Tier3 manifest shall preserve `no_alpha_claim`.
2. The manifest shall remain `artifact_manifest_only`, with `serving_status=not_serving`.
3. Drift output shall be a `not_assessed` skeleton requiring manual review, not automated production monitoring.

### Requirement 4 [REQ-NG16-B-SCHEDULE]

**User Story:** As a data maintainer, I want scheduled snapshot report evidence with append-only retention, so that daily ops can be audited without overwriting vintage data.

#### Acceptance Criteria

1. When a valid snapshot report is summarized, the schedule report shall preserve the source-contract claim boundary.
2. The schedule report shall declare `retention=append_only`.
3. The writer shall update a latest pointer without modifying historical report files.

### Requirement 5 [REQ-NG16-D-EVAL]

**User Story:** As a model researcher, I want D family evaluation to consume real `LocalResultStore` records, so that model-family comparisons are not fixture-only.

#### Acceptance Criteria

1. When run IDs are supplied by family, the evaluator shall load records from `LocalResultStore`.
2. The resulting evaluation shall rank only OOS-net metrics.
3. A visible baseline row shall remain required.

### Requirement 6 [REQ-NG16-B-STOOQ]

**User Story:** As a data maintainer, I want a formal Stooq source-contract decision helper, so that blocked/default-disabled status cannot be confused with restoration readiness.

#### Acceptance Criteria

1. If Stooq is blocked/default-disabled, the decision shall be `keep_default_disabled`.
2. If Stooq is available/default-enabled, the decision shall still require live non-empty close-row proof before default enablement.
3. The decision shall remain `source_contract_status_only` evidence, not source-contract readiness.
