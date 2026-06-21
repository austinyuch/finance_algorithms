# Review — Governance Evidence Refresh

## Verdict

**PASSED for repo-side governance evidence refresh.** This slice reduces false-green/stale-state risk by making current governance evidence testable, mutation-backed, and explicit about local-first CI cost boundaries.

## Scores

| Dimension | Score |
|---|---:|
| Requirements fit | 9.5 |
| Design consistency | 9.3 |
| Code/test quality | 9.2 |
| Governance hygiene | 9.5 |
| Overall | 9.4 |

## Live-Demo Readiness

**CONDITIONAL / hybrid.** The static dashboard uses the generated canonical local result-store payload and remains explicitly labeled `local_demo_only` / `no_alpha_claim`. Browser visual evidence is real chromium-headless proof and passed the repo-baseline pixel gate, but this slice does not convert the dashboard into a full live-backend demo.

## Verification Coverage

- `uv run pytest -q tests/quantlab/test_governance_guards.py` -> 25 passed.
- `uv run pytest -q` -> 435 passed, 2 skipped.
- `uv run python scripts/run_mutation_spot_checks.py` -> 118/118 configured/killed.
- `uv run mypy quantlab/ --ignore-missing-imports` -> success over the scoped QuantLab source set.
- `uv run lint-imports` -> KEPT.
- `cd frontend && npm test -- --run` -> 70 passed.
- `cd frontend && npm run build && npm run smoke && npm run visual && npm run visual:browser` -> PASS.
- Browser visual diff -> `0 / 1,296,000` mismatched pixels, threshold `0.001`.

## Acceptance Status

| Requirement | Status | Evidence |
|---|---|---|
| REQ-GOV-EVID-001 | PASS | `NEXT_STEPS.md` records current dependency, cron, F public/static, E Tier3, and local-first CI boundaries without stale completed-work prompts. |
| REQ-GOV-EVID-002 | PASS | Current registries and stakeholder docs use 435 Python tests, 52 frontend tests, 118/118 Python mutation, 29/29 frontend mutation, clean audit, current import-linter status, current browser visual diff, browser fail-closed e2e/VRT, and a machine-readable local CI matrix for repo-runnable workflow gates. |
| REQ-GOV-EVID-003 | PASS | `tests/quantlab/test_governance_guards.py` guards current evidence surfaces, local-first CI policy, public-hosting proof boundaries, visual evidence sync, and stale F fixture/public/audit wording. |

## FMEA Coverage

- FMEA-GOV-1: mitigated by current-state memo and promotion-boundary guards.
- FMEA-GOV-2: mitigated by stale evidence guards over current governance and stakeholder surfaces.
- FMEA-GOV-3: mitigated by mutation spot checks, including governance stale-state and local-first CI default and skill-body regressions mutations.

## Residual Risk

- Historical CR and review artifacts may preserve their original evidence counts by design; current rollups must continue to use current evidence surfaces, not historical snapshots.
- Public hosting remains `configured_not_observed` while deployed `dataHash` is stale relative to the branch-local dashboard payload.
- Local-first CI proof is repo-side evidence; it does not replace hosted workflow proof when a gate genuinely depends on GitHub-hosted state. Routine unit/integration, line coverage, PBT, mutation, smoke, build, visual, audit, type/import, dependency, and generated-evidence sync gates should be completed locally through subagent bundles or parallel local shells before any hosted confirmation, and a push intended to trigger Actions should first complete the local/subagent matrix or record the exact hosted-only gap. GitHub Actions are expensive and should not be used as the routine queue for tests that local agents or subagents can complete; slow local execution is not by itself a hosted-only gap. Subagent handoffs should preserve Matrix cell, Local owner, Command, Isolation, Evidence, and Remainder fields so local proof can be reconciled before any hosted run.

## Next Action

Keep future governance refreshes local-first by default, using `.agents/skills/local-first-ci/` and local subagents or parallel local shells for independent CI-equivalent gates before any hosted Actions run. Hosted Actions should remain confirmation or hosted-state proof, not the default queue where routine failures are discovered. If a gate is truly hosted-only, record why local/subagent proof is insufficient and the smallest hosted run needed before spending Actions minutes.
