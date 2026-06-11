# CR-A0 — Regime-aware rebalance scheduling

- **CR ID:** CR-A0-regime-rebalance-scheduling
- **Status:** Open → Implemented(repo-side)
- **Owner spec:** `a0-backtest-foundation`
- **Impacts:** `c-portfolio-core` C-3, `d-first-regime-model`
- **Type:** additive engine scheduling overlay; no Strategy/DataProvider contract break

## Motivation

C-3 added a portfolio-layer time/regime rebalance selector, but A0 still executed only plain calendar schedules. That meant regime rebalance dates could be selected but not executed by the engine.

## Change

`VectorizedEngine.run()` now accepts an optional serializable `rebalance_policy`:

```python
{
    "kind": "regime",
    "frequency": "quarterly",  # or monthly/semiannual/None
    "labels": {"2020-01-31": "risk_on", "...": "defensive"},
}
```

The engine builds candidate dates from the existing `rebalance` cadence, filters them through the C-3 selector, and records executed `rebalance_dates` in the result. Existing configs without `rebalance_policy` keep prior behavior.

## Evidence

- RED: new A0 engine tests initially failed because the engine called every calendar date and did not expose `rebalance_dates`.
- GREEN: `uv run pytest -q tests/quantlab/test_a0_2_engine.py -k "regime_rebalance"` → **3 passed**.
- Integration: `run_and_log()` logs serializable regime-label policies to `LocalResultStore`.
- PBT: generated regime-label sequences must match `select_rebalance_dates(...)`.
- Line coverage: `quantlab/engine/vectorized.py` + `quantlab/portfolio/rebalance.py` combined **89%**.
- Mutation: replacing the selector result with all candidate dates was killed by the example and PBT engine tests.

## Residual

This is event selection within the existing vectorized engine. It is not the future high-frequency `event_driven` engine.
