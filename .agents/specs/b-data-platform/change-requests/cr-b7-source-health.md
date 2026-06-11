# CR-B7 — snapshot source health correction

- **CR ID:** CR-B7
- **Status:** Open → Implemented(repo-side)
- **Owner spec:** `b-data-platform`
- **Target baseline:** B-3 external/source contract proof
- **Type:** source-contract correction; no A0 contract change

## Motivation

`ISSUE-B3-001` recorded a 2026-06-11 live `scripts/daily_snapshot.py` run with partial capture: FRED/NOAA succeeded for several sources, but all configured Stooq symbols returned HTTP 404 and the configured FRED London gold proxy `GOLDAMGBD228NLBM` also returned HTTP 404. Follow-up live probes confirmed both `GOLDAMGBD228NLBM` and `GOLDPMGBD228NLBM` currently return FRED HTTP 404 from this environment, while FRED commodity series such as `PCOPPUSDM` are reachable.

## Change

1. Replace the invalid default FRED gold proxy in `scripts/daily_snapshot.py` and `scripts/run_vintage_slice.py` with `PCOPPUSDM` as a reachable commodity proxy.
2. Keep Stooq/TSMC classified as external/source-contract blocked until a verified replacement endpoint or symbol map exists.
3. Update tests to assert invalid London gold IDs are not part of the default capture list.

## Re-sync / Freshness Evidence

- 2026-06-11 live probe:
  - `GOLDAMGBD228NLBM` → HTTP 404
  - `GOLDPMGBD228NLBM` → HTTP 404
  - `PCOPPUSDM` → HTTP 200 CSV
- `uv run pytest -q tests/quantlab/test_b_2_fred_prices.py tests/test_daily_snapshot.py` → **12 passed**.
- Full closeout: `uv run pytest -q` → **114 passed**; `uv run mypy quantlab/ --ignore-missing-imports` → clean(38 files); `uv run lint-imports` → KEPT.

## Residual

Stooq symbols, including `2330.tw`, are not closed by this CR. That path remains external/source-contract blocked until a verified data source is selected and proven with non-empty close rows.

## Closure

Repo-side CR-B7 is **Implemented** for invalid FRED gold proxy removal. `ISSUE-B3-001` remains as residual Stooq/TSMC external source-contract blocker rather than a fully closed B-3 proof.
