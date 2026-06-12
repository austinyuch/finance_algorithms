# CR-B16 - post CR-B15 promotion governance sync

Status: Implemented (repo-side governance)
Date: 2026-06-12

## Trigger

CR-B15 was promoted through the normal squash PR flow after its stable current-lane guard landed. The rolling memo now needs to record PR #67/#68 in the merged ledger so future agents do not treat the CR-B15 branch as local-only work.

## Scope

1. Record PR #67 (`dev`, `8b72a51`) and PR #68 (`main`, `508187e`) as CR-B15 promotion evidence in the merged ledger.
2. Extend the governance guard so CR-B15 cannot regress to "implemented locally; open PRs".
3. Add a mutation spot-check for stale CR-B15 promotion wording.
4. Refresh derived registry/test wording to include CR-B16 and the 40th configured mutation.

## Boundary

This CR does not change runtime behavior, source contracts, readiness verdicts, or the stable `Current branch lane:** none.` wording introduced by CR-B15. It only keeps post-promotion governance evidence fresh.

## Verification

- `uv run pytest -q tests/quantlab/test_governance_guards.py tests/test_mutation_spot_checks.py` -> 18 passed
- `uv run pytest --cov=scripts.run_mutation_spot_checks --cov-report=term-missing tests/test_mutation_spot_checks.py` -> 8 passed, 90% line coverage
- `uv run python scripts/run_mutation_spot_checks.py` -> 40/40 killed
- `uv run pytest -q` -> 223 passed
- `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py --ignore-missing-imports` -> clean over 53 source files
- `uv run lint-imports` -> KEPT
