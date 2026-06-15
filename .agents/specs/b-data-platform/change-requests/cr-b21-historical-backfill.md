# CR-B21 — Historical vintage backfill (1990+, marked approximate)

## Problem

`data/vintage/raw/` holds only a few real-time daily captures (2026-06-09/11/12),
and the daily snapshot fetches only recent data (Yahoo `range=5d`). With no deep
history, research backtests can't span business cycles — and the real OOS run was
stuck at 2016–2026 because it used FRED `SP500`, which FRED **licensing-caps to
~10 years**. The maintainer wants multi-cycle coverage (dot-com → crash, GFC,
COVID, 2022) back to **1990-01-01**, "everything available".

## Honesty boundary (non-negotiable)

History fetched today is **NOT true point-in-time**: `available_date = capture
date`. Per CLAUDE.md ("mark approximate when no true vintage source"), every
backfilled record is written with **`is_approximate=true`** and a `backfill`
marker. Consequences, surfaced in docs and the manifest:

- In **strict** PIT mode the loader **excludes** these records — only the genuine
  forward-accumulating daily captures remain. The backfill never contaminates a
  strict-PIT run.
- Only **`approximate_availability=True`** (research mode, already documented in
  `build_provider_from_vintage`) exposes them, setting `available_date =
  event_date`. This enables multi-regime *mechanism* backtests under
  `no_alpha_claim` — never true PIT, never an alpha claim.
- **Macro revisions:** FRED `fredgraph.csv` returns latest-*revised* values, so
  backfilled macro (GDP/CPI/UNRATE…) carries revision look-ahead. Equity/index
  *prices* are not revised → honest-approximate. Both are marked approximate; the
  macro revision caveat is documented.

## Requirements

### REQ-B21-001 — deep backfill, marked approximate, per-source degradation
`scripts/backfill_history.py` fetches deep history for the configured universe —
Yahoo with `period1=<since>` (incl. deep indices `^GSPC` 1927 / `^IXIC` 1971 for
1990+ equity coverage beyond ETF start dates), full FRED series, NOAA ONI — and
writes `is_approximate=true` records under `data/vintage/raw/backfill-<since>/`.
One failed source must not corrupt others (try/except per source); transient
network failures retry (the live probe hit intermittent HTTP 000). It is
**idempotent**: existing files are skipped, never overwritten (vintage
immutability). A `_backfill_manifest.json` records the run (since/until,
per-source ok/skip/fail, captured_at, approximate=true).

### REQ-B21-002 — deep research backtest becomes multi-cycle
With the backfill present, `build_provider_from_vintage(..., approximate_availability=True)`
over `data/vintage/raw/` spans 1990→2026 across multiple assets, so the
real-data OOS run produces a multi-regime computed comparison (still
`no_alpha_claim`). Strict mode is unaffected (backfill excluded).

## Design

- Reuse `_safe_source_id` (`:`→`_`, `^`→`idx_`) and the existing record schema
  (`source`, `available_date`, `is_approximate`, `captured_at`, `raw`,
  `event_date`); add `backfill: true` + `history_start`.
- `fetch_yahoo_history(symbol, since, until, *, get)` uses `period1/period2`
  epochs; `fetch_fred_full(series, *, get)` reuses the fredgraph CSV (already full
  history); `fetch_noaa(*, get)`. `get` is injected for tests.
- `_with_retries` wraps each fetch; `backfill(...)` loops, degrades per source,
  skips existing, writes the manifest.

## Tests (TDD)

- Unit: `is_approximate=true` + `backfill` marking; event_date extraction from
  Yahoo/FRED payloads; idempotent skip (existing file untouched); per-source
  degradation (one fetch raises → others still written, manifest records `fail`);
  retry succeeds on a transient failure then success.
- Integration: a fake-`get` backfill writes records the vintage loader reads;
  strict mode excludes them, approximate mode includes deep history.
- `TESTS.md` registry row.

## Evidence (2026-06-15)

- **RED→GREEN:** `tests/test_backfill_history.py` — **7 passed** (approximate+backfill
  marking, Yahoo/FRED event-date extraction, idempotent skip immutability,
  per-source degradation, retry recovery, manifest, strict-excludes/approximate-includes
  integration). `uv run mypy scripts/backfill_history.py --ignore-missing-imports` clean
  (REFACTOR: `functools.partial` + named `_no_event` helper replaced default-capture
  lambdas).
- **Live backfill run:** `uv run python scripts/backfill_history.py --since 1990-01-01`
  captured **18/24 sources** into `data/vintage/raw/backfill-1990-01-01/` — all 11 deep
  Yahoo histories (`^GSPC` **9179 rows, 1990-01-02→2026-06-12**, plus `^IXIC`, `SPY`,
  `AGG`, `TLT`, `GLD`, `DBC`, `BTC-USD`, `2330.TW`, `^TWII`, `TWD=X`), 6 FRED
  (`FEDFUNDS`, `CPIAUCSL`, `GDPC1`, `UNRATE`, `SP500`, `PCOPPUSDM`), and NOAA ONI.
  The 6 FRED rate/FX series (`DGS10`, `DGS2`, `T10Y2Y`, `NASDAQCOM`, `DCOILWTICO`,
  `DEXTAUS`) hit `fail:ReadTimeout` under transient FRED HTTP/2 throttling and are
  honestly recorded as `fail` in `_backfill_manifest.json` (`approximate:true`,
  `claim_boundary:no_alpha_claim`). Per-source degradation worked — no failed source
  corrupted another; an idempotent re-run completes the 6 when throttling clears.
- **REQ-B21-002 multi-cycle backtest:** with the backfill present,
  `build_provider_from_vintage(..., approximate_availability=True)` over
  `data/vintage/raw/` exposes 12 co-temporal assets; restricting to the deep indices
  `{^GSPC, ^IXIC}` yields a **`computed`** OOS-net comparison spanning
  **1990-01-02→2026-06-12 (437 months; dot-com 2000, GFC 2008, COVID 2020, 2022)** —
  BuyAndHold OOS-net Sharpe **0.7007** vs SmaTimingStrategy **0.2264** (timing's
  whipsaw cost drags net Sharpe over 36 years; honest, real, `no_alpha_claim`).
  Artifact: `reports/cr-b21-deep-cycle-1990-oos-artifact.json`.
- **Honesty boundary verified:** strict mode (`strict=True`) excludes the approximate
  backfill — `test_cli_degenerate_flat_oos_fails_closed` re-pinned to strict true-PIT
  still fails closed (`status=insufficient_data`, `reason=degenerate_flat_oos`), proving
  the backfill never contaminates a strict-PIT run.
- **Mutation:** `b-backfill-approximate-marking` (mutates `is_approximate: True→False`)
  **KILLED** by `test_backfill_marks_approximate_and_backfill`; full suite **111/111**.
- **Governance:** pytest **367→374**, mutation **110/110→111/111**, dashboard
  `dataHash 0f170441…` regenerated, all 25 governance guards green. After CR-B21
  landed on `main` (`693f780`), GitHub Pages redeployed and the live probe matched —
  committed probe/review-copy/manifest `hostingEvidence` re-pinned to `proven`
  (deployed==expected `0f170441…`, HTTP 200); the dashboard self-claim stays
  `not_proven` by design.

## Data validation (2026-06-15)

The backfilled deep history is not just *present* but historically *correct* —
peak-to-trough drawdowns computed from the `^GSPC` / `^IXIC` backfill match the
real record across every regime the maintainer named (dot-com 2000, GFC 2008,
COVID, 2022), confirming the data supports genuine multi-cycle study
(`approximate_availability=True`, `no_alpha_claim`):

| Regime | Index | Peak → Trough | Max drawdown |
|---|---|---|---|
| Dot-com crash | `^GSPC` | 2000-03-24 → 2002-10-09 | −49.1% |
| Dot-com crash | `^IXIC` | 2000-03-10 → 2002-10-09 | −77.9% |
| Global Financial Crisis | `^GSPC` | 2007-10-09 → 2009-03-09 | −56.8% |
| COVID crash | `^GSPC` | 2020-02-19 → 2020-03-23 | −33.9% |
| 2022 rate-hike bear | `^GSPC` | 2022-01-03 → 2022-10-12 | −25.4% |

Coverage: `^GSPC` **9,179 daily rows, 1990-01-02 → 2026-06-12**. (Read-only
provenance check over the committed backfill; no engine/test change.)

## Boundary

`approximate_event_date` / `no_alpha_claim` / `local_demo_only` preserved. This
adds approximate research history; it does not make anything true-PIT, change the
strict-mode default, or assert alpha. Stooq stays de-scoped (CR-B20 decision).
