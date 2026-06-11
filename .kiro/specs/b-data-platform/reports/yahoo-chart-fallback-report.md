# Yahoo Chart Fallback Report — CR-B8

Date: 2026-06-11

## Summary

Added a no-key Yahoo chart fallback for daily snapshot captures and vintage PIT loading. This addresses the TSMC/TWSE part of `ISSUE-B3-001` without claiming that the original Stooq path is fixed.

## Implemented Surface

- `scripts/daily_snapshot.py`
  - `YAHOO_SYMBOLS` defaults include broad market ETFs, `BTC-USD`, `TWD=X`, `2330.TW`, and `^TWII`.
  - `fetch_yahoo_chart()` records source, `available_date`, latest non-null close `event_date`, and raw payload.
- `quantlab/data/vintage.py`
  - `yahoo:*` payloads parse into PIT price rows with `symbol`, `event_date`, `available_date`, and `close`.

## Verification

```bash
uv run pytest -q tests/test_daily_snapshot.py::test_pbt_yahoo_latest_event_date_matches_last_valid_close
uv run pytest -q tests/test_daily_snapshot.py tests/quantlab/test_b_1_vintage.py tests/quantlab/test_b_2_fred_prices.py
```

Results:
- PBT parser check: **1 passed**.
- Targeted B/data checks: **19 passed**.
- Manual mutation: accepting trailing null closes was killed by the PBT test.
- Smoke: `yahoo:2330.TW` and `yahoo:^TWII` returned non-empty payloads with `event_date=2026-06-11`.

## Claim Boundary

This is repo-side fallback proof for Yahoo chart capture and PIT conversion. It is not a production SLA, and it does not prove Stooq availability.
