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

### Downstream fix (research sufficiency layer)

Hardening `_close` to *drop* invalid legs removed an accidental fail-closed signal the
multi-cycle research layer relied on: previously an all-`NaN` asset poisoned OOS vol to
`NaN`, and `max(0.0, NaN) == 0.0` made the flat-OOS degeneracy guard fire. With the engine
now dropping NaN legs, a NaN-poisoned asset would *silently* enter a "2-asset" comparison
contributing nothing (effectively half-cash) — a false-green the honesty charter forbids.
Fixed at the shared sufficiency layer: `quantlab/research/real_data_oos.py::_asset_spans`
now computes per-asset spans from **usable (finite, positive) close rows only** (same
boundary as `_close`), so an asset with no usable closes has no span, drops out of the
co-temporal universe, and the comparison fails sufficiency *closed* (`fewer_than_min_assets`
/ `no_cotemporal_overlap`) instead of computing a misleading subset. Caught by
`tests/quantlab/test_multi_cycle_oos.py::test_chaos_nan_closes_do_not_crash`, which the
full-suite transcript (only completable post-merge) surfaced as a real regression on `dev`.

## Evidence

- RED: pre-fix `tests/quantlab/test_a0_2_engine_chaos.py` → `test_chaos_all_nan_close...`
  and `test_chaos_total_loss_path_metrics_bounded` failed (NaN metrics / NaN drawdown).
- GREEN: `uv run pytest -q tests/quantlab/test_a0_2_engine_chaos.py tests/quantlab/test_a0_2_engine.py` → **16 passed**.
- `uv run mypy quantlab/engine/vectorized.py quantlab/engine/metrics.py --ignore-missing-imports` → clean.
- Regression detectors (consumers of engine/metrics): `test_a0_5_integration` 4 passed,
  `test_governance_guards` 25 passed, `test_f_1_showcase_api` 28 passed,
  `test_d_6_model_family_evaluation` 7 passed, `test_c_1_optimize` 5 passed.
- Downstream regression (surfaced by the full-suite transcript, fixed): `_asset_spans`
  usable-close filter → `test_multi_cycle_oos` + all `test_real_data_oos*` suites **79 passed**;
  `uv run mypy quantlab/research/real_data_oos.py quantlab/engine/vectorized.py quantlab/engine/metrics.py --ignore-missing-imports` → clean.
- Mutation guards **registered** in `scripts/run_mutation_spot_checks.py` and proven killed:
  `a0-chaos-close-finite-positive-guard`, `a0-chaos-total-loss-drawdown-fillna`,
  `a0-chaos-asset-span-usable-close-filter` (CR-A0) — all KILLED. Publishing the new total
  (`118`→`122`, incl. CR-B's `b-chaos-snapshot-atomic-write`) across governance/dashboard
  surfaces is bundled with the deploy-coupled dataHash re-pin (see Boundary).

## FMEA (lightweight)

| Risk ID | Failure Mode | Effect | Current Control | Planned Response | Task Trace |
|---|---|---|---|---|---|
| FMEA-A0-CHAOS-01 | NaN/invalid close fabricates return | NaN/bogus OOS-net metric on dashboard | (new) `_close` finite+positive guard | Prevent: drop leg as missing | `test_chaos_all_nan_close...`, `test_chaos_negative_close...` |
| FMEA-A0-CHAOS-02 | Total-loss path → NaN drawdown | dashboard renders NaN drawdown | (new) drawdown `fillna(-1.0)` | Prevent: honest -100% | `test_chaos_total_loss_path_metrics_bounded` |
| FMEA-A0-CHAOS-03 | Degenerate zero-vol → div-by-zero Sharpe | inf/NaN Sharpe | existing `std > 0` guard + chaos pin | Detect: chaos test asserts finite | `test_chaos_zero_volatility_returns_finite_sharpe` |
| FMEA-A0-CHAOS-04 | NaN-poisoned asset silently enters multi-cycle comparison at fabricated weight | false-green "2-asset" comparison that is really 1 asset (charter violation) | (new) `_asset_spans` usable-close filter → fails sufficiency closed | Prevent: drop asset from co-temporal universe | `test_multi_cycle_oos.py::test_chaos_nan_closes_do_not_crash` |

## Boundary

Hardens invalid *market-data* ingress to the A0 engine and the downstream research
sufficiency layer. Mutation guards are now registered + proven killed (see Evidence); the
**published** mutation total bump (`118`→`122`) is deploy-coupled — it lives in the live
`docs/showcase.json` dashboard payload, so it is bundled with the dataHash re-pin at the
`dev`→`main` promotion (mirrors the documented CR-RDO-005 deploy-coupling), not flipped
mid-branch. Does not cover strategy-emitted invalid weights or non-A0 high-frequency
simulation. `no_alpha_claim`.

## Review verdict

**State: Implemented · Review PASSED (repo-side).** Both latent bugs are fixed with honest,
fail-closed behaviour and pinned by chaos tests: (1) `_close` finite+positive guard drops
invalid legs (FMEA-A0-CHAOS-01); (2) total-loss drawdown is honest `-1.0`, never `NaN`
(FMEA-A0-CHAOS-02); (3) zero-vol Sharpe stays finite (FMEA-A0-CHAOS-03); (4) the downstream
`_asset_spans` usable-close filter makes a NaN-poisoned asset fail sufficiency closed rather
than silently enter a multi-cycle comparison (FMEA-A0-CHAOS-04). Evidence: A0 chaos+engine
**16 passed**; multi-cycle + all `real_data_oos*` **79 passed**; mutation guards
`a0-chaos-close-finite-positive-guard`, `a0-chaos-total-loss-drawdown-fillna`,
`a0-chaos-asset-span-usable-close-filter` **registered + KILLED**; mypy clean; full default-env
suite green (**446 passed, 2 skipped** — see `gate-pytest` transcript). The published mutation
total bump (`118`→`122`) is deploy-coupled and bundled with the dataHash re-pin at promotion.
`no_alpha_claim`.
