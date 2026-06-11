# C-3 Rebalance Report

Date: 2026-06-11

## Summary

Implemented C-3 as an additive portfolio-layer rebalance selector. It combines calendar cadence with regime-label changes and can consume the D `FirstRegimeClassifier` through the existing `predict(asof, data)` signal contract.

## Implemented Surface

- `quantlab/portfolio/rebalance.py`
  - `time_rebalance_dates(dates, frequency)`
  - `select_rebalance_dates(dates, regime_labels, frequency)`
  - `select_regime_rebalance_dates(dates, classifier, data, frequency)`
- `quantlab/portfolio/__init__.py` exports the C-3 helpers.

## Verification

```bash
uv run pytest -q tests/quantlab/test_c_3_rebalance.py
```

Result: **5 passed**.

Coverage:
- monthly / quarterly / semiannual cadence selection
- first observation inclusion
- regime-change trigger
- PBT ordered-subset and change-capture invariants
- smoke integration with `FirstRegimeClassifier`
- input-length validation

Mutation spot-check: changing the regime-change predicate from `!=` to `==` was killed by the PBT test with failing examples for both missed changes and false same-label triggers.

## Claim Boundary

C-3 selects rebalance dates; it does not change A0 engine scheduling or claim model alpha. Downstream engine-level event scheduling remains a future enhancement if needed.
