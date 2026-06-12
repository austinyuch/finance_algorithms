# CR-B14 — post CR-B13 promotion governance sync

- **Status:** Implemented(repo-side governance guard)
- **Target baseline:** B CR-B13 post live-write governance sync promotion state
- **Type:** stale-resume / false-green governance reduction

## Trigger

CR-B13 was promoted to both integration branches, but the rolling memo still identified CR-B12 as the latest promotion. That creates the same stale-resume risk CR-B13 was meant to prevent.

## Scope

1. Update `NEXT_STEPS.md` so the current branch lane is explicitly none after CR-B13 promotion.
2. Record PR #63 (`dev`, `8c5b3f1`) and PR #64 (`main`, `aea683f`) as CR-B13 promotion evidence.
3. Add a governance guard so the memo cannot regress CR-B13 to "implemented locally; open PRs".
4. Add a mutation spot-check for stale CR-B13 promotion wording.

## Boundary

This CR is governance-only. It does not add new live source availability proof, production Tier3 evidence, or a broader default snapshot source claim.

## Evidence

- `tests/quantlab/test_governance_guards.py::test_next_steps_reflects_post_merge_cr_b13_state`
- `scripts/run_mutation_spot_checks.py --only governance-stale-cr-b13-promotion`
