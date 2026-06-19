# CR-A0-CHAOS-001 — Invalid-Market-Data Chaos Hardening

> Owner spec: [a0-backtest-foundation](../)
> Type: additive correctness/chaos hardening; no Strategy/DataProvider contract break
> Status: Implemented(repo-side)
> Date: 2026-06-19

## Problem

The A0 engine had **no chaos coverage for invalid market data**. Two real defects were
latent and would have surfaced on the dashboard as fabricated numbers (garbage-in →
garbage-out), which is unacceptable for a surface that displays OOS-net comparisons:

1. **Non-finite / non-positive close prices were not treated as missing.**
   `VectorizedEngine._close` did `float(df.loc[symbol, "close"])` with no guard, and
   `_simulate`'s `if p0 and p1:` check treats `NaN` as **truthy**. A `NaN` (or negative)
   close therefore fabricated a `NaN`/bogus realised return that propagated silently into
   every metric (Sharpe, drawdown, cumulative).

2. **Total-loss path produced `NaN` max_drawdown.**
   `compute_metrics` computed `dd = wealth / wealth.cummax() - 1.0`; when wealth is wiped to
   exactly `0` with a zero/negative running peak, the `0/0` yielded `NaN`, and the existing
   `if max_drawdown > 0.0` clamp does not catch `NaN` (`NaN > 0` is `False`). The dashboard
   would render `NaN` drawdown for a -100% path.

Both were caught by the new chaos tests, not by the existing happy-path/PBT suite.

## Scope

- `quantlab/engine/vectorized.py::_close` now treats a **non-finite (`NaN`/±inf) or
  non-positive** close as **missing** (returns `None`), so `_simulate` skips the leg instead
  of fabricating a return. Valid prices are unchanged.
- `quantlab/engine/metrics.py::compute_metrics` fills the degenerate `0/0` drawdown with the
  honest total-loss value `-1.0` (`-100%`) so `max_drawdown` is always finite.
- New chaos suite `tests/quantlab/test_a0_2_engine_chaos.py` (5 tests): all-NaN closes,
  partial-NaN drop-only-affected-leg, negative close, infinite close, zero-volatility finite
  Sharpe, and total-loss bounded metrics.
- Folded a sibling flake fix: two engine-running PBTs in `test_a0_2_engine.py`
  (`test_pbt_event_driven_replay_uses_sorted_unique_events`,
  `test_pbt_regime_rebalance_policy_matches_portfolio_selector`) gained `deadline=None`,
  the same `ISSUE-A0-PBT-ASOF-001` runtime-flake stabilization (invariant assertions
  unchanged).

This is data-validity hardening only. Strategy-emitted invalid weights (e.g. a strategy
returning `NaN` weights) remain a separate strategy-contract concern (residual, see Boundary).

## Evidence

- RED: pre-fix `tests/quantlab/test_a0_2_engine_chaos.py` → `test_chaos_all_nan_close...`
  and `test_chaos_total_loss_path_metrics_bounded` failed (NaN metrics / NaN drawdown).
- GREEN: `uv run pytest -q tests/quantlab/test_a0_2_engine_chaos.py tests/quantlab/test_a0_2_engine.py` → **16 passed**.
- `uv run mypy quantlab/engine/vectorized.py quantlab/engine/metrics.py --ignore-missing-imports` → clean.
- Regression detectors (consumers of engine/metrics): `test_a0_5_integration` 4 passed,
  `test_governance_guards` 25 passed, `test_f_1_showcase_api` 28 passed,
  `test_d_6_model_family_evaluation` 7 passed, `test_c_1_optimize` 5 passed.

## FMEA (lightweight)

| Risk ID | Failure Mode | Effect | Current Control | Planned Response | Task Trace |
|---|---|---|---|---|---|
| FMEA-A0-CHAOS-01 | NaN/invalid close fabricates return | NaN/bogus OOS-net metric on dashboard | (new) `_close` finite+positive guard | Prevent: drop leg as missing | `test_chaos_all_nan_close...`, `test_chaos_negative_close...` |
| FMEA-A0-CHAOS-02 | Total-loss path → NaN drawdown | dashboard renders NaN drawdown | (new) drawdown `fillna(-1.0)` | Prevent: honest -100% | `test_chaos_total_loss_path_metrics_bounded` |
| FMEA-A0-CHAOS-03 | Degenerate zero-vol → div-by-zero Sharpe | inf/NaN Sharpe | existing `std > 0` guard + chaos pin | Detect: chaos test asserts finite | `test_chaos_zero_volatility_returns_finite_sharpe` |

## Boundary

Hardens invalid *market-data* ingress to the A0 engine. Does not cover strategy-emitted
invalid weights, mutation-suite registration (the 2 new guards are not yet added to
`run_mutation_spot_checks.py` — follow-up), or non-A0 high-frequency simulation. `no_alpha_claim`.
