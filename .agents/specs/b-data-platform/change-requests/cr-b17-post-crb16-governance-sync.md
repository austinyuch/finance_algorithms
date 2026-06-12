# CR-B17 - post CR-B16 promotion governance sync

Status: Implemented (repo-side governance)
Date: 2026-06-12

## Trigger

CR-B16 was promoted through the normal squash PR flow after its CR-B15 guard landed. The rolling memo now needs to record PR #69/#70 in the merged ledger so future agents do not treat the CR-B16 branch as local-only work.

## Scope

1. Record PR #69 (`dev`, `474e17f`) and PR #70 (`main`, `c35571e`) as CR-B16 promotion evidence in the merged ledger.
2. Extend the governance guard so CR-B16 cannot regress to "implemented locally; open PRs".
3. Add a mutation spot-check for stale CR-B16 promotion wording.
4. Refresh derived registry/test wording to include CR-B17 and the 41st configured mutation.

## Boundary

This CR does not change runtime behavior, source contracts, readiness verdicts, or the stable `Current branch lane:** none.` wording. It only keeps post-promotion governance evidence fresh.

## Verification

- `uv run pytest -q tests/quantlab/test_governance_guards.py::test_next_steps_reflects_post_merge_cr_b16_state` -> red before memo update
- `uv run pytest -q tests/quantlab/test_governance_guards.py tests/test_mutation_spot_checks.py` -> 19 passed
- `uv run pytest --cov=scripts.run_mutation_spot_checks --cov-report=term-missing tests/test_mutation_spot_checks.py` -> 8 passed, 90% line coverage
- `uv run python scripts/run_mutation_spot_checks.py` -> 41/41 killed
- `uv run pytest -q` -> 224 passed
- `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py --ignore-missing-imports` -> clean over 53 source files
- `uv run lint-imports` -> KEPT
- `cd frontend && npm test -- --run && npm run export:public-demo:docs` -> 23 passed; export passed
- `cd frontend && npm run visual && npm run visual:browser && npm run probe:public-demo && npm run smoke` -> passed; browser visual diff `235 / 1,296,000`, mismatch ratio `0.00018132716049382717`
