# First Regime Model — Conservative Writeup

> Epic D first model slice. Data in current tests is synthetic and proves pipeline correctness only.

## What Was Built

The first regime model is a deterministic, framework-light signal:

```text
PIT price/macro provider
  -> RegimeFeatureBuilder
  -> FirstRegimeClassifier
  -> RegimeAllocationStrategy
  -> A0 OOS-net leaderboard
```

Labels are intentionally small: `risk_on`, `defensive`, and `unknown`.

## Evidence

Targeted command:

```bash
uv run pytest -q tests/quantlab/test_d_1_regime.py tests/quantlab/test_d_2_regime_integration.py
```

Result: **6 passed**.

## Honest Conclusion

- This slice proves PIT-safe feature access, stable regime labels, missing-data fallback, and A0 leaderboard compatibility.
- It does **not** prove alpha. The current integration data is synthetic.
- If the regime strategy fails to beat a static baseline on real vintage data, that result should be reported directly rather than tuned away.

## Next Use

C-3 can consume `RegimeAllocationStrategy` or the lower-level `RegimeSignal` contract in a later additive rebalance hook.
