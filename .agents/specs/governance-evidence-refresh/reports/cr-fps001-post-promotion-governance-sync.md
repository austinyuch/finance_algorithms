# CR-FPS-001 Post-Promotion Governance Sync

## Summary

Closed a stale-resume gap after CR-FPS-001 was squash-merged through `dev` and
`main`. `NEXT_STEPS.md` now records PR #73 / PR #74 promotion proof, and the
mutation registry includes a dedicated stale-promotion mutation so future memo
regressions fail closed.

## Changes

- Added `test_next_steps_reflects_post_merge_cr_fps001_state`.
- Added mutation `governance-stale-cr-fps001-promotion`.
- Updated current evidence rollups from 226 to 227 Python tests and 43/43 to
  44/44 Python mutation spot checks.
- Refreshed static showcase evidence from `226 passed` to `227 passed`.
- Refreshed browser visual artifacts after the static HTML hash changed only for
  the evidence-count text.

## Evidence

- RED: `uv run pytest -q tests/quantlab/test_governance_guards.py::test_next_steps_reflects_post_merge_cr_fps001_state` failed before PR #73/#74 ledger proof was recorded.
- GREEN: `uv run pytest -q tests/quantlab/test_governance_guards.py tests/test_mutation_spot_checks.py` -> 22 passed.
- Full Python suite: `uv run pytest -q` -> 227 passed.
- Python mutation: `uv run python scripts/run_mutation_spot_checks.py` -> 44/44 killed.
- Type/import gates: `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py --ignore-missing-imports` -> clean over 53 files; `uv run lint-imports` -> KEPT.
- Frontend gates: `npm test -- --run` -> 23 passed; `npm run coverage` -> 91.42% line coverage; `npm audit --json` -> 0 vulnerabilities; `npm run mutation` -> 9/9 killed; `npm run visual`; `npm run visual:browser` -> `234 / 1,296,000` mismatched pixels at threshold `0.001`; `npm run probe:public-demo` -> HTTP 200; `npm run build`; `npm run smoke`.

## Boundary

This sync only proves governance freshness and public/static showcase evidence
consistency after CR-FPS-001 promotion. It does not change the dashboard's
fixture-backed `local_demo_only` claim boundary and does not add live backend,
auth, or Tier3 production execution.
