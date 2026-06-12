# Promotion Ledger Stale-Proof

## Summary

Closed the recursive stale-memo gap in `NEXT_STEPS.md`: the rolling governance
memo no longer keeps an exhaustive hand-maintained squash-PR ledger. Promotion
proof is now bounded to GitHub PR state and spec-local reports, while
`NEXT_STEPS.md` records current resume state, evidence boundaries, and owning
spec/report links.

## Changes

- Added `test_next_steps_uses_non_self_staling_promotion_boundary`.
- Replaced exact PR-pair promotion mutations with
  `governance-exhaustive-pr-ledger-regression`.
- Removed current-surface requirements that every prior dev/main squash PR be
  re-copied into `NEXT_STEPS.md`.
- Refreshed current governance and stakeholder evidence from 227 to 222 Python
  tests and from 44/44 to 38/38 Python mutation spot checks.
- Regenerated the static showcase export and updated the static visual contract
  hash for the evidence-count text change.

## Evidence

- RED: `uv run pytest -q tests/quantlab/test_governance_guards.py::test_next_steps_uses_non_self_staling_promotion_boundary` failed while the exhaustive `- **Merged:**` ledger remained in `NEXT_STEPS.md`.
- GREEN: `uv run pytest -q tests/quantlab/test_governance_guards.py tests/test_mutation_spot_checks.py` -> 17 passed.
- Focused mutation: `uv run python scripts/run_mutation_spot_checks.py --only governance-stale-post-merge-sync-promotion --only governance-exhaustive-pr-ledger-regression` -> 2/2 killed.
- Full Python suite: `uv run pytest -q` -> 222 passed.
- Python mutation: `uv run python scripts/run_mutation_spot_checks.py` -> 38/38 killed.
- Static showcase export: `cd frontend && npm run export:public-demo:docs` -> PASS.

## Boundary

This CR overlay proves that rolling governance cannot self-stale by requiring
every future squash PR to be appended to `NEXT_STEPS.md`. It does not replace
GitHub PR state as the source of truth for promotion status and does not change
runtime, live-data, hosted-service, or Tier3 production claims.
