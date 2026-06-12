# Requirements

## Introduction

This CR overlay closes the F visual-regression residual left by `ops-visual-drift-artifacts`: browser visual proof currently records a real screenshot, but the diff gate computes mismatch from screenshot hash equality rather than from pixels. That can fail to measure the actual visual blast radius and keeps stakeholder docs correctly marked with a residual.

## Dependencies, Impacts & CRs

- [Depends On: f-public-static-showcase, f-public-demo-readiness, ops-visual-drift-artifacts]
- [Impacts: f-showcase-read-api-dashboard, f-nextjs-showcase-dashboard, f-public-static-showcase, ops-visual-drift-artifacts]
- [Open Change Requests: CR-FBP-001] Pixel-backed browser visual baseline.

## Repo-side Closure vs External Execution

- **Repo-side Closure:** add a committed browser screenshot baseline, compute pixel mismatch ratio from current and baseline PNGs, fail the browser visual smoke when the ratio exceeds tolerance, update frontend tests/mutations, and refresh governance/docs claims.
- **External Execution:** GitHub Pages hosting remains external proof already covered by the public-hosting probe. No new cloud deployment is required for this lane.
- **External Blockers / Constraints:** CI-stored historical baselines outside git are deferred; this slice uses a repo-committed baseline artifact.

## Requirements

### Requirement 1 [REQ-FBP-001]

**User story:** As a dashboard reviewer, I want browser visual regression to compare actual pixels against a stored baseline, so that screenshot hash changes are not mistaken for measured visual drift.

#### Acceptance Criteria

1. When `npm run visual:browser` runs after `npm run visual`, then it should compare the current PNG screenshot against a stored PNG baseline and emit a diff artifact with pixel counts, mismatch ratio, threshold, baseline hash, and current hash.
2. If the PNG dimensions differ, or the mismatch ratio exceeds the configured threshold, then the visual smoke should fail closed instead of writing a passing artifact.
3. When current and baseline screenshots differ by only tolerated pixels, then the diff artifact should pass and preserve `no_alpha_claim`.

### Requirement 2 [REQ-FBP-002]

**User story:** As a spec maintainer, I want the visual proof claim to be updated across registries and stakeholder docs, so that no artifact keeps repeating the old hash-equality residual after the gate is pixel-backed.

#### Acceptance Criteria

1. When the pixel-backed gate is implemented, then `TESTS.md`, `SPECS.md`, `NEXT_STEPS.md`, and stakeholder docs should describe the visual residual as pixel-baseline-backed rather than hash-equality.
2. If any artifact cannot be refreshed from current evidence in this lane, then it should remain conservative and explicitly identify the missing evidence instead of overclaiming.
