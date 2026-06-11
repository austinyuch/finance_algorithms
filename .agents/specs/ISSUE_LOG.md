# ISSUE_LOG.md — Improvement Holding Surface

> Holds unresolved improvement items that are not yet safely closed by an active spec, CR, or review verdict. This is not a second `SPECS.md` and not a task dashboard.

| Issue ID | State | Cluster Key | Observation | Candidate Owner | Evidence | Routing Recommendation | Promotion Threshold |
|---|---|---|---|---|---|---|---|
| ISSUE-B3-001 | Folded | data-source-contract-proof | 2026-06-11 live `scripts/daily_snapshot.py` run captured FRED/NOAA partial data but every configured Stooq symbol, including `2330.tw`, returned HTTP 404; configured FRED gold proxy also returned HTTP 404 and several FRED series timed out. | `b-data-platform` B-3 external source contract | `data/vintage/raw/2026-06-11/` contains `fred_FEDFUNDS`, `fred_CPIAUCSL`, `fred_GDPC1`, `fred_UNRATE`, `fred_SP500`, `noaa_oni`; command exited 1 with ok=6 fail=16. CR-B7 probe found `GOLDAMGBD228NLBM`/`GOLDPMGBD228NLBM` 404 and `PCOPPUSDM` 200. | Folded into [b-data-platform/change-requests/cr-b7-source-health.md](./b-data-platform/change-requests/cr-b7-source-health.md) for invalid FRED gold proxy; Stooq/TSMC remains external/source-contract blocked. | CR-B7 repo-side fix verified; reopen/promote a new B CR only after selecting a verified Stooq replacement/source pin that requires repo changes. |
