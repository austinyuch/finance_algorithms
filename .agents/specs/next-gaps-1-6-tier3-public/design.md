# Design — Next Gaps 1-6 Tier3/Public/Ops

## Overview

This lane is a CR overlay across completed F/E/B/D surfaces. It adds proof-oriented evidence builders and scripts while keeping public/demo and MLOps claims conservative.

## Architecture

- **F public hosting:** Extend `frontend/lib/public-demo.ts` with `classifyPublicHostingEvidence(...)` and optional probe input for `buildPublicDemoManifest(...)`. `frontend/scripts/probe-public-demo.mjs` records live URL evidence.
- **F browser visual:** Keep static contract hashes, add `buildBrowserVisualEvidence(...)`, and add `frontend/scripts/browser-visual-smoke.mjs` for Chromium screenshot hash evidence.
- **E Tier3 first slice:** Extend `quantlab.mlops` with a run manifest and drift skeleton. These artifacts explicitly say not serving, not retraining, and skeleton-only drift.
- **B scheduled ops:** Add `scripts/snapshot_schedule_report.py` to summarize validated snapshot reports with append-only retention.
- **D real-source evaluation:** Add `build_result_store_family_evaluation(...)` as a wrapper over existing OOS-net evaluator that loads real `LocalResultStore` records.
- **B Stooq decision:** Add `decide_stooq_contract(...)` to keep Stooq default-disabled unless live close-row proof exists.

## Test Coverage Declaration

- Unit/integration: focused Python tests and Vitest tests for each new API.
- PBT: public-hosting classifier, Tier3 manifest count preservation, existing D/B PBTs.
- Mutation: new Python and frontend mutation targets for serving overclaim, source mislabeling, retention drift, Stooq decision drift, and browser visual hash validation.
- Smoke: GitHub Pages URL probe, static export, Chromium screenshot smoke, full pytest, mypy, import-linter, frontend build/smoke/audit.

## Repo-side Closure vs External Execution Boundary

- Repo-side closure includes committed code, tests, docs manifest, and evidence scripts.
- GitHub Pages configuration and hosted URL HTTP status are external execution evidence. The lane records the observed result rather than assuming it.
- Stooq is not externally restored by this lane. The formal decision remains conservative.

## FMEA

| Risk ID | Failure Mode | Effect | Current Control | Planned Response | Task Trace |
|---|---|---|---|---|---|
| FMEA-NG16-01 | Pages configured is reported as hosted proof | False public readiness | URL probe and manifest status split | Require HTTP 200 for `proven` | REQ-NG16-F-PUBLIC |
| FMEA-NG16-02 | Static hash is mistaken for browser visual proof | False visual regression claim | Separate browser visual evidence artifact | Capture Chromium screenshot hash | REQ-NG16-F-VISUAL |
| FMEA-NG16-03 | E manifest implies serving/Tier3 production | MLOps overclaim | Literal readiness/status fields | Reject serving drift through tests/mutation | REQ-NG16-E-TIER3 |
| FMEA-NG16-04 | Scheduled ops overwrites evidence | Audit loss | Append-only vintage rule | Write dated schedule report plus latest pointer | REQ-NG16-B-SCHEDULE |
| FMEA-NG16-05 | D evaluation remains fixture-only | Weak model comparison proof | LocalResultStore exists | Load run records by ID | REQ-NG16-D-EVAL |
| FMEA-NG16-06 | Stooq gets re-enabled without proof | Daily failures / false source readiness | Stooq default-disabled policy | Decision helper requires live close rows | REQ-NG16-B-STOOQ |

## EDD

Success requires focused tests green, mutation targets killed, frontend visual/browser smoke passing, public URL probe recorded, and governance artifacts updated without changing no-alpha or source-contract claim boundaries.
