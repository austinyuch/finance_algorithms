# CR-RDO-001 — Co-temporal universe + density-aware sufficiency

## Context

`real-data-oos-backtest` (baseline) proved the *mechanism*: the A0 engine runs on
real PIT data and ranks OOS-net honestly. Its review recorded a residual: the
sufficiency gate is calendar-span coarse (any-asset min/max event_date), and the
default proxy universe is **not co-temporal** — it mixes a 1992-start FRED proxy
with 2026-only equities, so the computed comparison is degenerate (baseline
OOS-net ≈ 0; assets do not overlap in time). This CR closes that residual so the
comparison is *meaningful*, not just mechanically valid. Still `no_alpha_claim`.

## Change

- Replace any-asset calendar span with **overlap-aware** sufficiency: sufficient
  only when ≥2 price assets share a *common* window ≥ `min_history_months`.
- Add a **co-temporal universe resolver** that selects the largest set of ≥2
  assets sharing a window ≥ the minimum, and use it as the default backtest
  universe (instead of all price symbols).
- Record the shared window and the selected co-temporal universe in artifact
  provenance; fail closed (`status=insufficient_data`,
  `reason=no_cotemporal_overlap`) when no qualifying overlap exists.

## Requirements

### REQ-RDO-CR1-001 — overlap-aware sufficiency
1. When ≥2 assets share an overlapping event_date window ≥ `min_history_months`,
   `assess_data_sufficiency(...).sufficient` is True with `reason="ok"` and
   records `overlap_start` / `overlap_end` / `overlap_months`.
2. When assets exist but no ≥2 of them share a ≥-window overlap, it returns
   `sufficient=False`, `reason="no_cotemporal_overlap"`.
3. The existing `fewer_than_min_assets` and `history_below_min_window`
   reasons are preserved.

### REQ-RDO-CR1-002 — co-temporal universe selection
1. `resolve_cotemporal_universe(provider, *, min_history_months, min_assets)`
   returns the asset set sharing the qualifying window plus the shared window;
   when none qualifies it returns an empty set.
2. The report/runner uses the co-temporal universe for the candidate and
   baseline strategies, and records it as `data_provenance.cotemporal_universe`
   and `asset_set`.
3. A test proves the degenerate-mix case (1 long-history + 1 short-history
   asset) is rejected as `no_cotemporal_overlap`, while a genuinely overlapping
   ≥2-asset panel is accepted and produces a non-degenerate baseline (OOS-net of
   the equal-weight baseline over co-temporal assets is finite and the
   comparison ranks both strategies).

### REQ-RDO-CR1-003 — boundary preserved
1. Every artifact still carries `claim_boundary=no_alpha_claim`.
2. Vintage snapshots remain read-only; re-running with more overlap upgrades
   status without edits.
3. Real on-disk vintage data: the runner selects whatever co-temporal subset
   qualifies (or fails closed); behavior is honest about the selected window.

## Out of scope

- Curating *which* real assets to capture (data-acquisition policy).
- Surfacing real runs in the dashboard (separate CR / #2c).
- **Sampling-frequency harmonization** — a monthly macro proxy vs a daily equity
  sampled at month-end can still flatten a baseline; aligning sampling frequency
  is its own follow-up.

## Implementation & Review — PASSED

- `resolve_cotemporal_universe` (exact subset enumeration for small asset sets;
  greedy fallback for >18 assets) + overlap-aware `assess_data_sufficiency`
  (`ok` / `no_cotemporal_overlap` / `history_below_min_window` /
  `fewer_than_min_assets`). Report/CLI trade only the co-temporal universe over
  the shared overlap window; provenance records `cotemporal_universe` +
  `overlap_start/end/months`.
- Real-data effect: the runner now selects `{PCOPPUSDM, SP500}` over their shared
  **2016–2026 (~118-month)** window instead of the degenerate 1992-vs-2026 mix.
  Still `no_alpha_claim`; the residual sampling-frequency nuance is documented
  above, not hidden.
- Tests: `tests/quantlab/test_real_data_oos_cotemporal.py` (8 — resolver,
  overlap-aware sufficiency reasons, co-temporal report). Mutations
  `real-data-oos-cotemporal-overlap-reason` / `real-data-oos-cotemporal-asset-set`
  killed. Baseline `test_real_data_oos*` suites stay green (synthetic fixtures
  are co-temporal by construction).
- Evidence artifact regenerated: `reports/real-data-oos-artifact.json`
  (`asset_set=[PCOPPUSDM, SP500]`, overlap window recorded).
