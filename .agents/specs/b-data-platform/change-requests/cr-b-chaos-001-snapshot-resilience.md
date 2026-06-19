# CR-B-CHAOS-001 — Snapshot Resilience Chaos Hardening

> Owner spec: [b-data-platform](../)
> Type: additive durability/chaos hardening; no source-contract or default-enablement change
> Status: Implemented(repo-side)
> Date: 2026-06-19

## Problem

The daily snapshot capture had chaos coverage for **single**-source failure only
(CR-B19 one FRED timeout, CR-B20 one Stooq 404). Two resilience gaps were untested:

1. **Non-atomic write → permanently corrupt immutable vintage.**
   `_write` did `fpath.write_text(...)` directly. A crash mid-write would leave a
   **truncated JSON** file; because writes are append-only/immutable (`SKIP if exists`),
   that truncated record would be preserved forever and silently poison the PIT vintage.

2. **No multi-source cascade test.** Real outages hit several sources at once; only a
   single-bad-source path was proven to degrade gracefully.

## Scope

- `scripts/daily_snapshot.py::_write` now writes atomically: serialize to a `.tmp` sibling,
  then `os.replace` to the final path; on any failure the temp is removed and the exception
  re-raised, so a crash never leaves a truncated immutable record. Append-only/immutable and
  dry-run semantics are unchanged.
- New chaos suite `tests/test_daily_snapshot_chaos.py` (5 tests):
  - multi-source **timeout cascade** degrades gracefully, writes survivors, and records a
    structured `error_type` per failed job in the report;
  - **atomic write** leaves no partial file and no temp leftover when `os.replace` fails;
  - atomic write success still produces valid JSON with the temp cleaned up;
  - a 200-but-malformed FRED body is captured (lenient `event_date=None`) without crashing;
  - malformed Yahoo JSON fails only that source and is caught by `main` (`rc=1`).

This is capture-resilience hardening only — no change to source enablement, Stooq policy
(stays blocked/default-disabled), or the source-health contract.

## Evidence

- RED (pre-fix): a forced `os.replace` failure left `fred_X.json` behind (truncated-record risk).
- GREEN: `uv run pytest -q tests/test_daily_snapshot_chaos.py tests/test_daily_snapshot.py` → **49 passed** (5 chaos + 44 existing, incl. the append-only/immutable + dry-run guards).

## FMEA (lightweight)

| Risk ID | Failure Mode | Effect | Current Control | Planned Response | Task Trace |
|---|---|---|---|---|---|
| FMEA-B-CHAOS-01 | Crash mid-write | truncated record SKIP'd forever as immutable | (new) temp + `os.replace` atomic write | Prevent: atomic rename, temp cleanup | `test_write_is_atomic_no_partial_or_temp_on_failure` |
| FMEA-B-CHAOS-02 | Multi-source simultaneous outage | run aborts / silent partial capture | per-source try/except + (new) cascade test | Detect/Contain: degrade + structured error_type | `test_main_multi_source_timeout_cascade_degrades_and_reports` |
| FMEA-B-CHAOS-03 | 200-but-malformed body | crash or silent garbage | lenient parse + (new) chaos pin | Detect: capture raw, `event_date=None` / fail one source | `test_fetch_fred_malformed_body_does_not_crash`, `test_fetch_yahoo_malformed_json...` |

## Boundary

Hardens local capture durability/resilience. Does not change broad source availability,
Stooq policy, or downstream vintage-loader validation of malformed-but-captured bodies
(a 200 HTML error page is still stored as raw — downstream PIT loading remains the validator).
`no_alpha_claim`.
