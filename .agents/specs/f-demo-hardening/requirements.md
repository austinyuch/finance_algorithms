# Requirements — F Demo Hardening

## Introduction

This slice hardens the existing local Next.js dashboard so demo-readiness evidence remains conservative. It adds explicit public hosting, visual regression, dependency-audit, and local-demo claim fields to the dashboard contract and renders them in the evidence panel.

## Dependencies, Impacts & CRs

- [Depends On: f-nextjs-showcase-dashboard]
- [Impacts: f-nextjs-showcase-dashboard] additive contract fields in generated payload/dashboard.
- [Open Change Requests: none]
- Current payload authority is the CR-FPS-006 generated local result-store scenario; this slice no longer treats inline fixture records as the dashboard source.

## Repo-side Closure vs External Execution

- **Repo-side Closure:** dashboard contract validation, UI rendering, tests, frontend mutation, coverage, build, and local HTTP smoke.
- **External Execution:** public deployment and screenshot baseline are not executed in this slice.
- **External Blockers / Constraints:** `npm audit` still reports moderate advisories before public deployment.

## Requirements

### Requirement 1 [REQ-F-DEMO-001]

**User Story:** As a showcase viewer, I want demo readiness fields visible, so that local proof is not mistaken for public deployment proof.

#### Acceptance Criteria

1. When the dashboard payload is served, it shall include `publicHosting=not_proven`.
2. When the dashboard payload is served with current passed browser visual diff evidence, it shall include `visualRegression=proven`.
3. When the dashboard renders, it shall show the local-demo claim and not-proven fields.

### Requirement 2 [REQ-F-DEMO-002]

**User Story:** As a maintainer, I want overclaimed or under-wired demo readiness rejected, so that future generated payloads cannot silently claim public hosting or drop browser visual evidence.

#### Acceptance Criteria

1. If public hosting is marked `proven` without deployment evidence, the contract validator shall reject the payload.
2. If visual regression proof artifacts are missing or failed, payload generation shall reject the evidence-backed artifact.
3. When frontend mutation checks run, public-hosting overclaim and visual-regression underclaim mutations shall be killed.
