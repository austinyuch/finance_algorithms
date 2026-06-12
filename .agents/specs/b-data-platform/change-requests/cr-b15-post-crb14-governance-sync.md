# CR-B15 - post CR-B14 promotion governance sync

- **Status:** Implemented(repo-side governance guard)
- **Target baseline:** B CR-B14 post CR-B13 governance sync promotion state
- **Type:** stale-resume / false-green governance reduction

## Trigger

CR-B14 was promoted to both integration branches, but the rolling memo still identified CR-B13 as the latest promotion. That would send the next agent to a stale resume point and omit PR #65/#66 from current governance evidence.

## Scope

1. Update `NEXT_STEPS.md` so the current branch lane is explicitly none after CR-B14 promotion.
2. Record PR #65 (`dev`, `05485cc`) and PR #66 (`main`, `c1e1591`) as CR-B14 promotion evidence.
3. Add a governance guard so the memo cannot regress CR-B14 to "implemented locally; open PRs".
4. Add a mutation spot-check for stale CR-B14 promotion wording.

## Boundary

This CR is governance-only. It does not add new live source availability proof, production Tier3 evidence, or a broader default snapshot source claim.

## Evidence

- `tests/quantlab/test_governance_guards.py::test_next_steps_reflects_post_merge_cr_b14_state`
- `scripts/run_mutation_spot_checks.py --only governance-stale-cr-b14-promotion`
