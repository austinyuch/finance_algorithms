# CR-RDO-004 — Sampling-frequency homogeneity guard (mixed-cadence oversampling)

## Problem

The real-data OOS comparison ranks strategies on out-of-sample **net Sharpe**,
which depends on the realized return series sampled at the **rebalance cadence**
(default `monthly`). `assess_data_sufficiency` / `resolve_cotemporal_universe`
select a co-temporal universe by **calendar overlap only** — they do not check
that the selected assets actually *update* at least as often as the rebalance
cadence. The default `PRICE_PROXIES` mixes native cadences: `SP500` /
`NASDAQCOM` / `DCOILWTICO` / `DEXTAUS` are daily, but `PCOPPUSDM` is **monthly**.

When the rebalance cadence is **finer** than an asset's native cadence, the PIT
loader forward-fills the last known (stale) price across the gap, so the
backtest sees **fabricated flat-return periods** for that asset. Flat returns
understate annualized volatility, which inflates the OOS-net **Sharpe** — a
methodologically dishonest comparison. This is the residual flagged by CR-RDO-001
("Residual follow-up: sampling-frequency harmonization") and the real-data
review. CR-RDO-003 narrowed the *default CLI* to a single daily index, which
sidesteps the issue for that one run, but the **library path remains unguarded**
for any >=2-asset universe a future caller assembles.

This is a `no_alpha_claim` mechanism-honesty fix, not a strategy change.

## Requirements

### REQ-RDO-CR4-001 — native sampling frequency is estimated and recorded
The research module estimates each price asset's **native sampling frequency**
from the PIT price panel (median spacing of distinct `event_date`s per symbol)
and classifies it to a canonical cadence (`daily` / `weekly` / `monthly` /
`quarterly` / `irregular`). `DataSufficiency` carries the per-asset cadences,
the coarsest selected cadence, and a `frequency_homogeneous` flag; `computed`
reports record a `sampling_frequency` block in `data_provenance`.

### REQ-RDO-CR4-002 — oversampling vs native cadence fails closed
`build_real_data_oos_report` fails closed (raises `SamplingFrequencyError`, a
`ValueError` subclass) when the rebalance cadence is meaningfully **finer** than
the **coarsest** selected asset's native cadence — i.e. the comparison would
forward-fill stale prices into fabricated flat returns. The guard fires when
`coarsest_native_days > rebalance_days * (1 + tol)` (`tol = 0.5`). A
frequency-homogeneous universe, or one whose assets all update at least as often
as the rebalance cadence, passes. `no_alpha_claim` is preserved.

### REQ-RDO-CR4-003 — CLI maps the guard to an explicit fail-closed reason
`scripts/run_real_data_oos_backtest.py` distinguishes the sampling-frequency
guard from the pre-existing degeneracy guard: it emits
`status=insufficient_data`, `reason=oversampled_vs_native_frequency`, exit 2 —
never a misleading `computed`. The default single-index SP500 run is unaffected
(single homogeneous asset; rebalance not finer than native), so it stays
`computed` and the committed dashboard `realData` panel is unchanged.

## Design

- `SamplingFrequency(symbol, median_spacing_days, cadence)` dataclass.
- `estimate_sampling_frequencies(provider) -> dict[str, SamplingFrequency]` —
  median consecutive spacing of sorted distinct `event_date`s per symbol; <2
  distinct dates → `median_spacing_days=0.0`, `cadence="irregular"`.
- `classify_cadence(days) -> str` — `daily` (≤4), `weekly` (≤10), `monthly`
  (≤45), `quarterly` (≤135), else `irregular`.
- `rebalance_cadence_days(rebalance) -> float` — `daily`=1, `weekly`=7,
  `monthly`=30.4375, `quarterly`=91.3125 (fallback `monthly`).
- `DataSufficiency` gains `sampling_frequencies: tuple[tuple[str, str], ...]`,
  `coarsest_cadence_days: float`, `frequency_homogeneous: bool` (defaults keep
  back-compat with existing construction sites).
- `build_real_data_oos_report` computes the guard against the **selected
  co-temporal universe** only, after sufficiency/window resolution, before the
  engine run; on pass it records
  `data_provenance["sampling_frequency"] = {by_symbol, coarsest_cadence,
  coarsest_native_days, rebalance, rebalance_days, homogeneous}`.
- CLI catches `SamplingFrequencyError` first → `oversampled_vs_native_frequency`;
  the generic `ValueError` catch continues to map to `degenerate_flat_oos`.

## Tests (TDD)

- Unit: `classify_cadence` boundaries; `estimate_sampling_frequencies` on daily
  vs monthly providers; `frequency_homogeneous` true/false; guard raises on
  monthly-asset + monthly-rebalance-finer... (daily+quarterly under monthly);
  guard passes on homogeneous daily and on coarse-rebalance; provenance recorded;
  CLI maps guard → `oversampled_vs_native_frequency` exit 2; single-index SP500
  path stays `computed`.
- PBT: for any per-asset native spacings + rebalance cadence, the guard fires iff
  `max(native_days) > rebalance_days * 1.5`; `classify_cadence` is monotonic
  non-decreasing in days.
- Integration: regenerate the committed `real-data-oos-artifact.json`; assert it
  stays `status=computed`, carries the `sampling_frequency` provenance, and the
  dashboard `dataHash` is **unchanged** (`68dfae0f…`, provenance is not surfaced
  by `_real_data_section`).
- Mutation: `real-data-oos-sampling-frequency-guard` (flip the oversampling
  comparison `>` → `<`, must be killed).
- `TESTS.md` registry rows + count resync.

## Boundary

No engine/loader/cost/metric semantics change; no live data; no alpha claim. This
adds a fail-closed honesty guard + provenance to the research composition layer
and leaves the default `computed` SP500 comparison and the dashboard payload
untouched. Project stays `local_demo_only` / `no_alpha_claim`.
