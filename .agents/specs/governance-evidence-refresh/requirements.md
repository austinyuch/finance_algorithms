# Requirements — Governance Evidence Refresh

## Introduction

This spec closes a current-state governance drift after the Torch dependency isolation lane was merged to `dev` and `main`. The issue is not product behavior; it is false-green / stale operational evidence in current governance surfaces that could tell the next agent or stakeholder to repeat already-completed work or trust obsolete gate counts.

## Dependencies, Impacts & Change Requests

- [Depends On: a-torch-default-dependency-isolation, f-browser-pixel-baseline, ops-visual-drift-artifacts]
- [Impacts: SPECS.md, NEXT_STEPS.md, RTM.md, ISSUE_LOG.md, quantlab/TESTS.md, quantlab/CORRECTNESS_CHECKLIST.md, stakeholder docs]
- [Open Change Requests: none]

## Repo-side Closure vs External Execution

- **Repo-side Closure**: refresh current governance/stakeholder evidence, add guard tests, add a mutation spot check for stale governance wording, and verify Python/static visual gates locally.
- **External Execution**: GitHub Dependabot alert state is queried live through `gh api`; autonomous cron `event=schedule` proof remains external/pending until GitHub naturally emits a scheduled run.
- **External Blockers / Constraints**: no local command can honestly create a real autonomous `event=schedule` Actions run; the repo must keep that residual explicit.

## Requirements

### Requirement 1 [REQ-GOV-EVID-001]

**User Story:** As a future agent resuming the program, I want current governance memos to reflect merged branch and alert state, so that I do not repeat completed PR or rescan work.

#### Acceptance Criteria

1. When `.agents/specs/NEXT_STEPS.md` is read after PR #24/#26, then it shall state that Torch isolation has landed in `dev` and `main`.
2. When GitHub Dependabot alert #7 is fixed, then `NEXT_STEPS.md` and `SPECS.md` shall not continue to describe it as pending.
3. If autonomous cron proof is still absent, then the memo shall keep that residual separate from completed Torch dependency work.

### Requirement 2 [REQ-GOV-EVID-002]

**User Story:** As a stakeholder reading generated docs or registries, I want evidence counts to match the latest verified suite, so that the docs do not overstate or understate readiness.

#### Acceptance Criteria

1. When the Python suite count changes, then current registries and generated docs shall use the latest verified count.
2. When the browser visual diff changes, then current docs shall report the actual pixel mismatch and threshold instead of stale zero-diff language.
3. If a historical spec review contains older evidence, then it may remain unchanged as a historical snapshot and shall not be used as current rollup authority.

### Requirement 3 [REQ-GOV-EVID-003]

**User Story:** As a maintainer, I want stale governance evidence to fail a deterministic guard, so that future false-green drift is caught before merge.

#### Acceptance Criteria

1. When current governance files contain stale pre-refresh markers, then `tests/quantlab/test_governance_guards.py` shall fail.
2. When `NEXT_STEPS.md` reintroduces the stale Dependabot rescan-pending wording, then the mutation runner shall mark the mutation killed.
3. When governance artifacts are refreshed, then the targeted governance tests shall pass without weakening import-linter or contract drift guards.
