# Stooq Opt-In Report — CR-B9

Date: 2026-06-11

## Summary

Changed the daily snapshot source policy so Stooq is no longer a default capture source after repeated 404s. Stooq can still be retried through `QUANTLAB_STOOQ_SYMBOLS` without code changes.

## Verification

```bash
uv run pytest -q tests/test_daily_snapshot.py
uv run python scripts/daily_snapshot.py --dry-run
```

Results:
- Daily snapshot tests: **14 passed**.
- Dry-run smoke: 22 jobs, no Stooq jobs, `fail=0`.
- Line coverage: `scripts/daily_snapshot.py` **95%**.
- Mutation: defaulting Stooq to `["spy.us"]` was killed.

## Claim Boundary

This closes the default-source policy issue. It does not prove Stooq availability.
