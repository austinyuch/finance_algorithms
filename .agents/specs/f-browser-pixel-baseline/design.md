# Design

References: `requirements.md`, `frontend/lib/public-demo.ts`, `frontend/scripts/browser-visual-smoke.mjs`, `frontend/tests/public-demo.test.tsx`, `docs/DEMO_RISK_WARNING_TAXONOMY.md`.

## Overview

This lane upgrades the existing browser visual smoke from hash-equality thresholding to a PNG pixel-diff gate. The current dashboard payload boundary is the generated canonical local `local_result_store` / `ExperimentRegistry` scenario introduced by CR-FPS-006; the visual gate proves rendered static dashboard content stability, not investment alpha or full production backend readiness.

## Architecture

- Add `frontend/visual-baselines/browser-visual.png` as the repo-owned baseline screenshot.
- Extend `BrowserVisualDiffEvidence` with `mismatchedPixels`, `totalPixels`, and `baselineImageHash`/`currentImageHash` aliases through the existing hash fields.
- Add a pure `computePixelMismatchRatio(...)` helper in `frontend/lib/public-demo.ts` for unit/PBT coverage.
- Update `frontend/scripts/browser-visual-smoke.mjs` to decode PNGs, compare dimensions, compute pixel mismatch ratio, write `frontend/out/browser-visual-diff.json`, and fail closed on threshold breach.

## Test Coverage Declaration

- Unit/PBT: `frontend/tests/public-demo.test.tsx` covers ratio math, threshold status, dimension mismatch, and malformed thresholds.
- Mutation: frontend mutation checks include threshold inversion / bypass mutants.
- Smoke/E2E: `npm run visual && npm run visual:browser` captures a real chromium-headless screenshot and compares it to the committed PNG baseline.
- Coverage: `npm run coverage` remains the frontend line-coverage authority.

## Repo-side Closure vs External Execution Boundary

Repo-side closure is complete when the committed PNG baseline, pixel diff helper, smoke script, tests, mutation checks, docs, and governance artifacts are green. External CI baseline storage beyond git is out of scope for this slice and must not be claimed.

## Contracts

No external API contract changes. The local evidence contract remains JSON emitted by `browser-visual-smoke.mjs` and typed by `BrowserVisualDiffEvidence`.

## Components And Interfaces

- `frontend/lib/public-demo.ts`: validates visual diff evidence and computes mismatch ratio from same-sized RGBA buffers.
- `frontend/scripts/browser-visual-smoke.mjs`: CLI smoke that captures screenshot, reads baseline PNG, computes mismatch, writes evidence, and exits nonzero on failure.
- `frontend/visual-baselines/browser-visual.png`: committed baseline image.

## Failure Mode And Effects Analysis

| Risk ID | Failure Mode | Effect | Cause | Current Control | Severity | Occurrence | Detection Difficulty | Planned Response | Task Trace |
|---|---|---|---|---|---|---|---|---|---|
| FMEA-FBP-1 | Hash equality presented as visual diff | False-green or overstrict visual proof | Diff uses hash change as mismatch ratio | Honest residual docs | High | Medium | Low | Replace hash gate with pixel ratio from PNG bytes | Task 1 |
| FMEA-FBP-2 | Baseline image missing or dimension drift ignored | Passing artifact without comparable evidence | Script falls back to current evidence | Existing smoke writes JSON | High | Low | Low | Require stored baseline PNG and fail on dimension mismatch | Task 1 |
| FMEA-FBP-3 | Docs retain old residual | Stakeholders see stale readiness warning | Derived docs not refreshed | Manual grep | Medium | Medium | Medium | Refresh docs/governance from new evidence | Task 2 |

## Risk Response And Mitigation Plan

- Prevent: require an explicit baseline PNG path and matching dimensions.
- Detect: PBT/unit tests cover mismatch math and threshold boundaries; smoke covers real chromium screenshot.
- Contain: keep `local_demo_only` and `no_alpha_claim`; do not promote the dashboard to full production/backend readiness.

## Error Handling

The browser smoke exits nonzero when the export is missing, Chromium fails, the baseline is missing, PNG dimensions differ, or mismatch exceeds threshold. The diff artifact records `failed` only when enough evidence exists to compute the failure.

## EDD

- `cd frontend && npm test -- --run tests/public-demo.test.tsx`
- `cd frontend && npm run coverage`
- `cd frontend && npm run visual && npm run visual:browser`
- `cd frontend && npm run mutation`
- `cd frontend && npm run build`
- `cd frontend && npm run smoke`

## Traceability References

- Requirement: `REQ-FBP-001`, `REQ-FBP-002`
- Design IDs: `FBP-PIXEL-DIFF`, `FBP-GOVERNANCE-CLOSEOUT`
