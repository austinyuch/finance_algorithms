# Design — Governance Evidence Refresh

## Overview

This is a governance/readiness hardening slice. It treats stale current-state evidence as a false-green defect and adds a deterministic guard in the existing governance test file.

## Architecture

- **Authority inputs**
  - GitHub PR/alert state from `gh`.
  - Test execution output from local commands.
  - Existing row-level test authority in `quantlab/TESTS.md`.
- **Authoritative current surfaces**
  - `.agents/specs/NEXT_STEPS.md`
  - `.agents/specs/SPECS.md`
  - `.agents/specs/RTM.md`
  - `.agents/specs/ISSUE_LOG.md`
  - `quantlab/TESTS.md`
  - `quantlab/CORRECTNESS_CHECKLIST.md`
- **Stakeholder surfaces**
  - `docs/*`
  - `frontend/lib/showcase-fixture.ts`
  - `frontend/visual-baselines/showcase.visual.json`

## Test Coverage Declaration

- Unit/governance guard: `uv run pytest -q tests/quantlab/test_governance_guards.py`
- Mutation spot check: `uv run python scripts/run_mutation_spot_checks.py --only governance-stale-next-steps-alert`
- Integration/regression: `uv run pytest -q`
- Static visual smoke: `cd frontend && npm run export:public-demo:docs && npm run visual && npm run visual:browser`

## Repo-side Closure vs External Execution Boundary

Repo-side closure is achieved when current governance surfaces and stakeholder docs match verified evidence, stale current-state markers fail deterministic tests, and the static visual contract is regenerated. External autonomous cron proof remains pending because only GitHub can emit a real `event=schedule` run.

## Contracts

No runtime API/data contract changes. This slice adds governance guard behavior and evidence metadata updates only.

## Components and Interfaces

- `tests/quantlab/test_governance_guards.py`
  - Adds current governance stale-marker guards.
  - Keeps existing import-linter and contract drift tests.
- `scripts/run_mutation_spot_checks.py`
  - Adds `governance-stale-next-steps-alert` mutation.
- Current governance/docs files
  - Receive one-way refresh from evidence, not derived-to-derived backfill.

## Failure Mode and Effects Analysis

| Risk ID | Failure Mode | Effect | Cause | Current Control | Severity | Occurrence | Detection Difficulty | Planned Response | Task Trace |
|---|---|---|---|---|---:|---:|---:|---|---|
| FMEA-GOV-1 | Current memo says completed work is still pending | Agents repeat completed PR/rescan work | Post-merge memo not refreshed | Manual review only | 7 | 4 | 3 | Add guard against stale local-lane/rescan wording | T1 |
| FMEA-GOV-2 | Docs report stale suite or visual diff numbers | Stakeholders see false evidence | Generated docs not regenerated after guard changes | Manual grep | 6 | 4 | 4 | Refresh docs from verified outputs; update visual artifacts | T2 |
| FMEA-GOV-3 | Guard exists but does not prove test quality | False-green guard | No mutation check | Existing mutation runner | 5 | 3 | 4 | Add governance stale wording mutation | T3 |

## Risk Response and Mitigation Plan

- Prevent: keep stale markers out of current governance surfaces with deterministic tests.
- Detect: mutation runner reintroduces stale Dependabot wording and expects the guard to fail.
- Contain: historical review artifacts remain snapshots; current rollups must use current evidence.

## Error Handling

If browser visual diff changes after evidence text updates, keep the threshold result but update exact mismatch metadata. Do not claim zero-diff unless the artifact proves zero mismatches.

## EDD

Success requires:

- `uv run pytest -q tests/quantlab/test_governance_guards.py`
- `uv run python scripts/run_mutation_spot_checks.py --only governance-stale-next-steps-alert`
- `uv run pytest -q`
- `cd frontend && npm run export:public-demo:docs && npm run visual && npm run visual:browser`

## Traceability References

- Requirements: `REQ-GOV-EVID-001..003`
- Tests: `test_current_governance_surfaces_do_not_publish_stale_gate_counts`, `test_next_steps_reflects_post_merge_torch_alert_state`
- Mutation: `governance-stale-next-steps-alert`
