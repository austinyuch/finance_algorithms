# CR-B8 — Yahoo chart fallback for TW and broad market prices

- **CR ID:** CR-B8
- **Status:** Open → Implemented(repo-side)
- **Owner spec:** `b-data-platform`
- **Target baseline:** B-3 external/source contract proof
- **Type:** source fallback; no A0 contract change

## Motivation

`ISSUE-B3-001` left Stooq/TSMC as an external source-contract residual after all configured Stooq symbols returned HTTP 404 on 2026-06-11. A fresh probe found Yahoo chart endpoints reachable for the needed TW and broad-market symbols, including `2330.TW` and `^TWII`.

## Change

1. Add Yahoo chart capture jobs to `scripts/daily_snapshot.py` with source names `yahoo:<symbol>`.
2. Parse the latest non-null Yahoo close timestamp into `event_date` so bitemporal snapshots keep a market event date separate from `available_date`.
3. Extend the vintage loader to convert `yahoo:*` raw payloads into PIT price rows.
4. Keep Stooq classified as an external/source-contract residual; this CR adds a fallback source rather than proving Stooq.

## Evidence

- TDD RED: `tests/test_daily_snapshot.py` and `tests/quantlab/test_b_1_vintage.py` initially failed on missing Yahoo capture/loader support.
- GREEN/REFACTOR: `uv run pytest -q tests/test_daily_snapshot.py tests/quantlab/test_b_1_vintage.py tests/quantlab/test_b_2_fred_prices.py` → **19 passed**.
- PBT: `test_pbt_yahoo_latest_event_date_matches_last_valid_close` verifies latest non-null close selection.
- Mutation spot-check: changing the Yahoo event-date parser to accept trailing null closes was killed by the PBT test.
- Smoke: `fetch_yahoo_chart("2330.TW", "2026-06-11")` and `fetch_yahoo_chart("^TWII", "2026-06-11")` returned non-empty raw payloads with `event_date=2026-06-11`.

## Residual

Stooq remains blocked from this environment. B-3 can now proceed through the Yahoo fallback for TSMC/TWSE proof, but any claim about Stooq itself must remain blocked until a working Stooq contract is selected or removed.
