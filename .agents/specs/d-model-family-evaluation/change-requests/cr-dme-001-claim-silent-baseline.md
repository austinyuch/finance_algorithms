# CR-DME-001 — Accept a claim-silent dumb baseline in the family evaluator

> CR overlay against the **completed** baseline `d-model-family-evaluation`
> (Implemented · Review PASSED). Behavior-narrowing bugfix: the evaluator now
> rejects only **explicit** alpha overclaims, not a claim-silent dumb baseline.
> Resolves `ISSUE-EVAL-001`.

## Dependencies, Impacts & CRs

- **[Depends On:** a0-backtest-foundation (Strategy protocol), d-model-family-evaluation baseline.**]**
- **[Impacts:** d-model-family-evaluation (`quantlab/models/evaluation.py::_claim_boundary`
  contract narrowed — additive acceptance, no change to alpha-rejection or ranking).
  Unblocks any caller wanting to rank a canonical dumb baseline (`BuyAndHold`) — the
  row that must always stay visible in an OOS-net leaderboard.**]**
- **[Open Change Requests:** none.**]**

## Problem (ISSUE-EVAL-001)

`build_model_family_evaluation` ranks families OOS-net only and **requires a
visible baseline row**. But `_claim_boundary` raised unless
`strategy_metadata.claim_boundary == "no_alpha_claim"` was *present*, while the
canonical dumb baseline `BuyAndHold.metadata` (`quantlab/strategies/buyandhold.py`)
**omits the key entirely**. So the evaluator could not score a `BuyAndHold`
baseline — the one row that must always be visible — forcing callers to use a
non-canonical baseline or duplicate the claim logic (CR-RDO-005's
`multi_cycle_oos` had to add its own `_assert_no_overclaim`). Surfaced while
building CR-RDO-005; recorded as `ISSUE-EVAL-001`.

This is a `no_alpha_claim` honesty-contract fix, not an alpha or ranking change.

## Requirements

### REQ-DME-CR1-001 — a claim-silent dumb baseline is accepted

#### Acceptance Criteria

1. When a run record's `strategy_metadata` omits `claim_boundary` (a claim-silent
   dumb baseline such as `BuyAndHold`), then `score_model_family` /
   `build_model_family_evaluation` shall accept it, score it with the default
   `claim_boundary="no_alpha_claim"`, and keep it visible/rankable.
2. When such a baseline is the visible baseline row, then the evaluation shall
   succeed (not raise) and `baseline_run_ids` shall include it.

### REQ-DME-CR1-002 — an explicit overclaim still fails closed

#### Acceptance Criteria

1. When a run record's `strategy_metadata.claim_boundary` is present and not
   `"no_alpha_claim"` (e.g. `"alpha_claim"`), then the evaluator shall fail closed
   (`ValueError`), preserving the project-level no-alpha boundary.
2. When no baseline row is present, then the evaluator shall still fail closed
   (unchanged `requires a visible baseline row`).

## Design

- `_claim_boundary(record)`: reject only when `claim is not None and claim !=
  "no_alpha_claim"`; a missing key (`None`) is accepted and normalized to
  `"no_alpha_claim"`. `score_model_family` calls it for its raise side-effect only
  (the prior redundant `!= "no_alpha_claim"` re-check is removed — `_claim_boundary`
  now returns the canonical boundary or raises).
- No change to OOS-net ranking, baseline-visibility requirement, artifact
  checksum, or the `ModelFamilyScore.claim_boundary` default.

## Tests (TDD)

- Repurposed (no net test-count change — keeps the published pytest count stable):
  - `test_model_family_evaluation_ranks_only_oos_net_and_keeps_baseline` now uses a
    **claim-silent `BuyAndHold` baseline** (RED before fix: raised; GREEN after) and
    asserts every row carries the default `no_alpha_claim`.
  - `test_model_family_evaluation_rejects_alpha_claim_and_missing_baseline` keeps the
    explicit-`alpha_claim` rejection + missing-baseline rejection; the claim-silent
    `→ raise` assertion is removed (behavior intentionally reversed).
- Mutation `d-model-evaluation-alpha-gate` re-pointed to the new guard
  (`claim != "no_alpha_claim"` → `==`), verified **KILLED**.

## Boundary

No alpha claim; no ranking/metric/artifact semantics change; no engine/data touch;
no new runtime/credentials/E2E surface (pure backend logic). `mypy` clean;
mutation count unchanged at 115/115 (anchor re-pointed, not added). Project stays
`local_demo_only` / `no_alpha_claim`.

## Review verdict

**State: Implemented · Review PASSED.** REQ-DME-CR1-001/002 met; `test_d_6` 7 passed
(claim-silent baseline accepted + ranked, explicit overclaim still rejected);
`d-model-evaluation-alpha-gate` mutation KILLED with the re-pointed anchor; mypy
clean; full default-env suite green. `ISSUE-EVAL-001` closed.
