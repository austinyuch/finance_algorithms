# CR-RDO-003 — Market-index real-data OOS + approximate availability + degeneracy guard

## Critical finding

The committed `real-data-oos-artifact.json` reported `status=computed`, but the
comparison was **degenerate**: `provider.get()` returned no data at every
historical as-of, so the backtest produced flat ~zero returns (BuyAndHold
OOS-net = 0.0). Root cause: single-capture FRED vintage sets every row's
`available_date` to the **2026 capture date**, so PIT-strict access correctly
hides all of it from historical as-ofs (2016–2026). A misleading "computed"
claim survived because nothing detected the degeneracy. This corrects shipped
work (the #2c dashboard `realData` panel rested on it).

## Change (directive: "use the market index, not the low-frequency source")

- **Market index source:** the CLI universe is the **SP500 index** (a
  high-frequency series with real history), not the low-frequency macro proxies
  (copper/oil/FX). `min_assets=1` — a single index compares a timing candidate
  vs a buy-and-hold baseline (>=2 assets keeps the cross-sectional mix).
- **Explicit approximate availability:** `build_provider_from_vintage(...,
  approximate_availability=True)` sets `available_date = event_date` so
  single-capture data is visible to historical as-ofs. This is **NOT true PIT**
  (may introduce lookahead); the artifact records
  `availability_mode=approximate_event_date` (per CLAUDE.md "mark approximate").
- **Degeneracy guard:** `build_real_data_oos_report` raises when every strategy's
  OOS net return series is flat (max OOS vol `< 1e-6`); the CLI fails closed
  (exit 2, `reason=degenerate_flat_oos`) instead of emitting "computed".
- **`SmaTimingStrategy`** — single-asset MA timing (invests above SMA, cash
  below): the minimal strategy that differs from buy-and-hold on one index.

## Requirements

### REQ-RDO-CR3-001 — honest, non-degenerate market-index comparison
1. With the SP500 index + approximate availability, the CLI emits a `computed`
   comparison with real (non-flat) OOS returns and `availability_mode` recorded.
2. True-PIT single-capture data (flat OOS) fails closed (`degenerate_flat_oos`,
   exit 2) — never `computed`.
3. The comparison candidate differs from the baseline (timing vs buy-and-hold),
   so a single index is non-degenerate. `no_alpha_claim` preserved.

## Real result

SP500 index, `approximate_event_date`, 2016–2026: **BuyAndHold OOS-net 0.877**
(baseline) vs **SmaTimingStrategy 0.808** — buy-and-hold beats SMA-timing net of
cost over a bull run (SMA-timing has lower vol, 11.9% vs 16.2%). Honest mechanism
evidence, not a strategy verdict.

## Gates / cascade

- `quantlab/data/vintage.py`, `quantlab/strategies/timing.py`,
  `quantlab/research/real_data_oos.py`, `scripts/run_real_data_oos_backtest.py`.
- Tests: `tests/quantlab/test_real_data_oos_index.py` (5) + updated CLI tests;
  mutation `real-data-oos-degeneracy-guard` killed.
- Governance resync: pytest 338→345, mypy 60→61, lint-imports 77/198→78/201,
  Python mutation 106→107. Visual baseline hash unchanged (`realData` panel is
  below the 1440×900 fold). Public hosting reverts to `configured_not_observed`
  (new `dataHash a99453c3…` not yet deployed); re-prove after this lands on `main`
  and Pages redeploys.
