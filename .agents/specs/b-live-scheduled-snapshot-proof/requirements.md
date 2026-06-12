# Requirements

## Introduction

This lane addresses the remaining B scheduled snapshot proof gap: the repository had smoke-tier local schedule proof and a GitHub Actions workflow, but no successful real Actions run artifact. A manual `workflow_dispatch` run on `dev` exposed a workflow timestamp bug (`github.run_started_at` expands empty), so this lane fixes the workflow and captures real external Actions evidence without claiming cron has fired by itself.

## Dependencies, Impacts & CRs

- [Depends On: b-snapshot-ops-gate, ops-visual-drift-artifacts]
- [Impacts: b-data-platform, stakeholder docs, test registries]
- [Open Change Requests: CR-BLSP-001] Live Actions snapshot proof.

## Repo-side Closure vs External Execution

- **Repo-side Closure:** fix the workflow timestamp bug, add a regression guard, update spec/governance artifacts, and capture local dry-run proof.
- **External Execution:** dispatch the GitHub Actions workflow on the fixed branch and preserve run/artifact metadata as proof.
- **External Blockers / Constraints:** a `workflow_dispatch` success proves real Actions execution, not autonomous cron firing. Cron proof remains pending until a scheduled event run exists.

## Requirements

### Requirement 1 [REQ-BLSP-001]

**User story:** As an ops reviewer, I want the daily snapshot workflow to produce schedule proof in GitHub Actions, so that local smoke proof is not overclaimed as live workflow evidence.

#### Acceptance Criteria

1. When the workflow builds schedule proof in GitHub Actions, then the proof step should receive non-empty start and finish timestamps.
2. If a workflow context field is not valid in GitHub Actions, then tests should reject that field from the workflow before merge.
3. When the workflow is dispatched manually, then the resulting Actions run and artifact metadata should be recorded as `workflow_dispatch` evidence, not cron-schedule evidence.

### Requirement 2 [REQ-BLSP-002]

**User story:** As a governance maintainer, I want the external proof boundary to stay conservative, so that a manual run does not get described as autonomous scheduled production readiness.

#### Acceptance Criteria

1. When the workflow proof is captured, then `review.md`, `NEXT_STEPS.md`, and test registries should distinguish `workflow_dispatch` from `schedule`.
2. If no cron-triggered run exists, then the remaining gap should be named explicitly instead of marked complete.
