# CR-B10 — Source health registry

- **CR ID:** CR-B10
- **Status:** Implemented(repo-side)
- **Owner spec:** `b-data-platform`
- **Target baseline:** B-3 external source contract
- **Type:** source contract status evidence

## Motivation

CR-B7/B8/B9 fixed source defaults, Yahoo fallback, and Stooq opt-in policy. The remaining gap was a small explicit status surface so source health summaries cannot silently turn a blocked source into a default source.

## Change

1. Add `quantlab.data.source_health.SourceHealthRegistry`.
2. Record source, symbol, observed status, default-enabled posture, and reason.
3. Summaries expose `claim_boundary=source_contract_status_only`.

## Evidence

- RED: tests failed while `quantlab.data.source_health` did not exist.
- GREEN: `uv run pytest -q tests/quantlab/test_e_1_experiment_registry.py tests/quantlab/test_b_6_source_health.py` -> 7 passed.
- Line coverage: stdlib trace fallback parsed `quantlab.data.source_health` at 97.6%.
- Mutation: `b-source-health-claim-boundary` killed.

## Residual

This CR records observed source-contract status only. It does not live-probe Stooq or re-enable Stooq defaults.
