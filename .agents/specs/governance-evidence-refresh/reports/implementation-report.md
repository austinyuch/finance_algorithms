# Implementation Report — Governance Evidence Refresh

## Summary

Closed current-state governance drift across the active UAT/production-readiness evidence surfaces and added local-first CI cost governance. The lane now guards current evidence counts, public-hosting proof boundaries, visual-readiness wiring, local-first workflow-cost policy, and stakeholder payload sync.

## Changes

- Added and expanded governance guard coverage in `tests/quantlab/test_governance_guards.py`.
- Added mutation coverage for stale governance wording, promotion-boundary drift, local-first CI default regression, public-hosting overclaim paths, payload sync drift, review transcript freshness, and stale visual evidence.
- Added `.agents/skills/local-first-ci/SKILL.md` and repo-root `AGENTS.md` guidance so CI-equivalent gates run locally first, routine CI is delegated to local subagent gate bundles where useful, and hosted GitHub Actions are not triggered unless explicitly required.
- Tightened the local-first CI skill so routine unit/integration, line coverage, PBT, mutation, smoke, build, visual, audit, type/import, dependency, and generated-evidence sync gates are treated as local/subagent-owned work when the repo has commands for them, and pushes intended to trigger Actions first complete the local/subagent matrix or record the exact hosted-only gap.
- Rebased `.agents/skills/local-first-ci/SKILL.md` into a concise semantic contract and updated the governance guard to verify the local/subagent, serialized, and hosted-only boundaries without depending on stale long-form wording.
- Added stronger skill-creator trigger and execution guidance for "Actions are expensive" / "CI flow/testing local/subagent first" requests: GitHub Actions are not the routine queue for tests that local agents or subagents can complete, slow local execution is not itself hosted-only, CI-equivalent subagent dispatches need an explicit return contract, and true hosted-only gaps need an exception ledger before hosted execution.
- Refreshed current governance surfaces:
  - `.agents/specs/NEXT_STEPS.md`
  - `.agents/specs/SPECS.md`
  - `.agents/specs/RTM.md`
  - `.agents/specs/TESTS.md`
  - `.agents/specs/ISSUE_LOG.md`
  - `quantlab/TESTS.md`
  - `quantlab/CORRECTNESS_CHECKLIST.md`
- Refreshed stakeholder/static docs and dashboard payload evidence.
- Regenerated static visual contract, browser visual artifacts, public-hosting probe artifacts, and review gate transcripts.

## Evidence

- RED: `uv run pytest -q tests/quantlab/test_governance_guards.py::test_current_governance_surfaces_do_not_publish_stale_gate_counts` failed after `governance-evidence-refresh/review.md` and `reports/implementation-report.md` were added to current stale-evidence surfaces while they still contained superseded gate evidence.
- GREEN: `uv run pytest -q tests/quantlab/test_governance_guards.py` -> 25 passed.
- Full Python suite: `uv run pytest -q` -> 288 passed.
- Python mutation: `uv run python scripts/run_mutation_spot_checks.py` -> 100/100 configured/killed.
- Type check: `uv run mypy quantlab/ scripts/build_showcase_payload.py scripts/run_tsmc_hedge_slice.py scripts/run_vintage_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py scripts/source_quorum_proof.py scripts/stooq_contract_proof.py --ignore-missing-imports` -> success over 58 source files.
- Import architecture: `uv run lint-imports` -> KEPT over 75 files / 189 dependencies.
- Frontend unit: `cd frontend && npm test -- --run` -> 44 passed.
- Frontend build/smoke/visual: `cd frontend && npm run build && npm run smoke && npm run visual && npm run visual:browser` -> PASS.
- Browser visual diff: `236 / 1,296,000` mismatched pixels, `mismatchRatio=0.00018209876543209876`, threshold `0.001`.
- Local-first CI policy: `tests/quantlab/test_governance_guards.py::test_local_first_ci_policy_is_repo_guided_and_skill_backed` verifies `AGENTS.md` and `.agents/skills/local-first-ci/SKILL.md` keep hosted Actions as explicit/necessary-only proof rather than the default discovery path or routine queue, trigger on workflow-cost / "Actions are expensive" wording, require local subagent gate bundles for routine Python/static/PBT/integration/coverage/mutation/frontend/smoke/visual/audit/dependency/evidence checks before hosted CI confirmation, and require hosted-only exception details when local/subagent proof is insufficient.
- Local CI matrix: `scripts/local_ci_matrix.py --list-json` exposes the repo-runnable `daily-snapshot` dry-run report and schedule-proof commands with `generated-artifact` isolation, while preserving hosted-only schedule event semantics and artifact upload transport.
- Local-first CI mutation spot check: `uv run python scripts/run_mutation_spot_checks.py --only governance-local-first-ci-default-regression --only governance-local-first-ci-skill-default-regression --only governance-workflow-hosted-only-contract --report-json /tmp/local-first-ci-mutation.json` -> 3/3 killed.

## Residuals

- Public hosting remains `configured_not_observed` until GitHub Pages serves the branch-local dashboard `dataHash`.
- Stooq remains blocked/default-disabled until positive finite live close rows are proven through `scripts/stooq_contract_proof.py`.
- E Tier3 remains not production-ready until externally proven production serving, retraining, and automated drift monitoring evidence passes the strict readiness proof CLI.
- Local-first CI reduces hosted workflow cost and false-green discovery loops; it is not itself hosted GitHub Actions proof. Hosted Actions remain necessary only for GitHub event semantics, secrets, permissions, artifact transport, scheduled triggers, Pages deployment state, or other hosted-only evidence, and should be the smallest targeted run after local/subagent proof is complete or explicitly blocked.
