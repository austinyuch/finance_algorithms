# Requirements — B Scheduled Run Observer

## Introduction

The daily snapshot workflow has a successful GitHub Actions `workflow_dispatch` proof, but no observed autonomous cron `event=schedule` run. This spec adds a deterministic observer so the project can repeatedly classify the current GitHub Actions evidence without overclaiming manual runs as production schedule proof.

## Dependencies, Impacts & Change Requests

- [Depends On: b-live-scheduled-snapshot-proof, ops-visual-drift-artifacts]
- [Impacts: B scheduled ops evidence, test registries, `NEXT_STEPS.md`, stakeholder docs]
- [Open Change Requests: none]

## Repo-side Closure vs External Execution

- **Repo-side Closure**: parse Actions run-list evidence, emit a machine-readable observation, test manual-only pending status, and record current live observation from `gh run list`.
- **External Execution**: GitHub must emit an actual `event=schedule` run before cron proof becomes `proven`.
- **External Blockers / Constraints**: a local command or manual dispatch cannot honestly create autonomous cron proof.

## Requirements

### Requirement 1 [REQ-BSRO-001]

**User Story:** As an ops reviewer, I want an observer artifact for daily snapshot scheduled runs, so that current cron proof status is repeatable and not manually inferred.

#### Acceptance Criteria

1. When a run list contains only successful `workflow_dispatch` runs, then the observer shall return `status=pending` and `evidence_tier=external_pending`.
2. When a run list contains a completed successful `event=schedule` run, then the observer shall return `status=proven` and `evidence_tier=live`.
3. When a scheduled run failed before a later successful scheduled run, then the observer shall preserve the latest failed schedule run separately from the latest successful schedule proof.

### Requirement 2 [REQ-BSRO-002]

**User Story:** As a maintainer, I want the observer to be usable with pre-fetched JSON, so that tests and reports remain deterministic without requiring live GitHub access.

#### Acceptance Criteria

1. When `--runs-json` is supplied, then the CLI shall read that file instead of calling GitHub.
2. When no successful schedule run exists, then the CLI shall write the observation artifact and exit non-zero to prevent false-green automation.
3. When a successful schedule run exists, then the CLI shall exit zero.

### Requirement 3 [REQ-BSRO-003]

**User Story:** As a governance maintainer, I want mutation coverage for manual-vs-cron classification, so that tests fail if manual evidence is promoted to proven.

#### Acceptance Criteria

1. When the observer is mutated to always return `proven`, then the manual-only test shall fail.
2. The mutation shall be listed by `scripts/run_mutation_spot_checks.py --list`.
