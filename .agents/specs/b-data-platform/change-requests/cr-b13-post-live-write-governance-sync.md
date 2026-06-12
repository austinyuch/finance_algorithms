# CR-B13 — post live-write promotion governance sync

- **Status:** Implemented(repo-side governance guard)
- **Target baseline:** B CR-B12 scoped live-write smoke promotion state
- **Type:** stale-resume / false-green governance reduction

## Trigger

CR-B12 landed in both integration branches, but the rolling memo still stated that no lane was active after the E Tier3 readiness proof CLI promotion. That wording could route future agents to stale work and omit the actual CR-B12 squash PR evidence.

## Scope

1. Update `NEXT_STEPS.md` so the current branch lane is explicitly none after CR-B12 promotion.
2. Record PR #61 (`dev`, `0f3af09`) and PR #62 (`main`, `4f2f58a`) as the CR-B12 promotion evidence.
3. Add a governance guard so the memo cannot regress to "implemented locally; open PRs".
4. Add a mutation spot-check for the stale live-write promotion wording.

## Boundary

This CR does not add new live source availability proof. CR-B12 remains scoped to append-only live write/skip mechanics, while broad default source success and Stooq readiness remain separate B residuals.

## Evidence

- `tests/quantlab/test_governance_guards.py::test_next_steps_reflects_post_merge_live_write_smoke_state`
- `scripts/run_mutation_spot_checks.py --only governance-stale-live-write-promotion`
