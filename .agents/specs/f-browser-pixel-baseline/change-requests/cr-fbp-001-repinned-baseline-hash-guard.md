# CR-FBP-001 — Tolerate a freshly re-pinned baseline (baseline == current)

## Context

`test_traceability_visual_evidence_tracks_current_pixel_diff` asserts every
current hash surface contains `currentHash` **and not** `baselineHash`. The intent
is to catch docs that still publish a *stale* baseline hash after a re-pin.

When the browser visual baseline is legitimately re-pinned to the current render
(e.g. an intentional dashboard UI change) **in a deterministic-rendering
environment**, the capture equals the baseline byte-for-byte, so
`baselineHash == currentHash` and `mismatchedPixels == 0`. The current guard then
asserts `currentHash in text` **and** `baselineHash (== currentHash) not in text`
— impossible to satisfy. This blocks any honest UI change whose baseline is
re-pinned deterministically (it surfaced while wiring real OOS-net runs into the
dashboard, the `real-data-oos-backtest` #2c follow-up).

## Change

- The stale-baseline-hash check fires **only when `baselineHash != currentHash`**.
  When they are equal (a fresh deterministic re-pin), there is no distinct stale
  hash to guard against, so requiring its absence is incorrect.
- The current-hash publication requirement (`currentHash in text`) is unchanged.
- The pixel-diff mechanism is unchanged: `mismatchRatio <= maxMismatchRatio`
  still gates, and a real regression (current != baseline beyond threshold) still
  fails closed. This does **not** revert to hash-equality; it accepts a 0-pixel
  diff as a valid floor while keeping the tolerant pixel comparison.

## Requirements

### REQ-FBP-CR1-001 — accept equal re-pinned hashes
1. When `baselineHash == currentHash`, the hash-surface check passes as long as
   the surface publishes `currentHash` (no stale-hash assertion).
2. When `baselineHash != currentHash`, the surface must publish `currentHash` and
   must **not** contain `baselineHash` (unchanged stale-hash protection).
3. The pixel-count / threshold / `no_alpha_claim` assertions are unchanged.

## Out of scope

- The dashboard `realData` rendering itself (real-data-oos #2c) — lands on top of
  this CR.
- Any change to the pixel-diff threshold or capture mechanism.

## Implementation & Review

- Extracted `_assert_hash_surface_publishes_current(text, current_hash,
  baseline_hash)` in `tests/quantlab/test_governance_guards.py`; the traceability
  guard calls it. Unit-tested in `tests/quantlab/test_visual_baseline_guard.py`
  (equal-hash re-pin accepted; differing-hash stale reference rejected; clean
  differing-hash accepted). Mutation `visual-baseline-repin-hash-guard` flips the
  `!=` to `==` and is killed by the unit test.
