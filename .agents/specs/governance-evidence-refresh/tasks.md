# Tasks — Governance Evidence Refresh

## Lane Classification

`new spec` for current-state governance false-green hardening after the completed Torch dependency isolation lane.

- [x] 1. TDD stale-governance guard [Implements REQ-GOV-EVID-001, REQ-GOV-EVID-003]
  - [x] 1.1 RED: add tests that fail on stale current-state gate counts and stale Torch rescan/local-lane wording.
    - _Eval: `uv run pytest -q tests/quantlab/test_governance_guards.py` fails on stale `ISSUE_LOG.md` and `NEXT_STEPS.md`._
  - [x] 1.2 GREEN: refresh current governance surfaces so the guard passes.
    - _Eval: `uv run pytest -q tests/quantlab/test_governance_guards.py`._
  - [x] 1.3 REFACTOR: keep the guard scoped to current governance surfaces, leaving historical reviews as immutable snapshots.
    - _Eval: targeted guard remains green._

- [x] 2. Evidence and stakeholder-doc refresh [Implements REQ-GOV-EVID-002]
  - [x] 2.1 Update `quantlab/TESTS.md`, `.agents/specs/TESTS.md`, `RTM.md`, `SPECS.md`, `ISSUE_LOG.md`, and `CORRECTNESS_CHECKLIST.md` from verified outputs.
    - _Eval: stale-string scan and targeted governance tests._
  - [x] 2.2 Refresh generated `local_result_store` showcase payload/static docs exports, visual snapshot hash, and tracked browser visual artifacts.
    - _Eval: `cd frontend && npm run export:public-demo:docs && npm run visual && npm run visual:browser`._
  - [x] 2.3 Contain visual diff overclaim by reporting the actual threshold-passing mismatch count.
    - _Eval: `docs/browser-visual-diff.json` matches docs wording._

- [x] 3. Mutation proof [Implements REQ-GOV-EVID-003]
  - [x] 3.1 Add `governance-stale-next-steps-alert` mutation.
    - _Eval: mutation appears in `tests/test_mutation_spot_checks.py` list smoke._
  - [x] 3.2 Kill the targeted mutation.
    - _Eval: `uv run python scripts/run_mutation_spot_checks.py --only governance-stale-next-steps-alert`._

- [x] 4. Review and closeout [Implements REQ-GOV-EVID-001, REQ-GOV-EVID-002, REQ-GOV-EVID-003]
  - [x] 4.1 Record implementation evidence.
  - [x] 4.2 Produce `review.md`.
  - [x] 4.3 Run final checks.
