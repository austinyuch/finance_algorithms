# ISSUE_LOG.md — Improvement Holding Surface

> Holds unresolved improvement items that are not yet safely closed by an active spec, CR, or review verdict. This is not a second `SPECS.md` and not a task dashboard.

| Issue ID | State | Cluster Key | Observation | Candidate Owner | Evidence | Routing Recommendation | Promotion Threshold |
|---|---|---|---|---|---|---|---|
| ISSUE-B3-001 | Triaged | data-source-contract-proof | 2026-06-11 live `scripts/daily_snapshot.py` run captured FRED/NOAA partial data but every configured Stooq symbol, including `2330.tw`, returned HTTP 404; configured FRED gold proxy also returned HTTP 404 and several FRED series timed out. | `b-data-platform` B-3 external source contract | `data/vintage/raw/2026-06-11/` contains `fred_FEDFUNDS`, `fred_CPIAUCSL`, `fred_GDPC1`, `fred_UNRATE`, `fred_SP500`, `noaa_oni`; command exited 1 with ok=6 fail=16. | Keep B review repo-side PASSED; open B CR overlay if source symbols/URLs or source pins need code/config changes. | Promote to CR when a replacement Stooq endpoint/symbol map or FRED gold source is selected and needs repo changes; close when a live run captures non-empty Stooq close rows for target symbols. |
