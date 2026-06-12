# Implementation Report

## Scope

Implemented `f-browser-pixel-baseline` as a CR overlay against completed F visual/public-demo surfaces.

## Changes

- Added `frontend/visual-baselines/browser-visual.png` as the committed browser screenshot baseline.
- Added `computePixelMismatchRatio(...)` to `frontend/lib/public-demo.ts`.
- Extended browser visual diff evidence with `mismatchedPixels` and `totalPixels`.
- Updated `frontend/scripts/browser-visual-smoke.mjs` to decode PNGs via `pngjs`, compare actual pixels, fail on dimension drift, and fail when mismatch exceeds `QUANTLAB_BROWSER_VISUAL_MAX_MISMATCH_RATIO` (default `0.001`).
- Added frontend tests/PBT for pixel mismatch ratio and dimension/buffer-size rejection.
- Added frontend mutation target for suppressed pixel mismatch counts.
- Refreshed the static showcase fixture evidence strings from stale `156 passed` / `8/8` / `84.37%` values to current conservative gate evidence.
- Copied current diff evidence to `docs/browser-visual-diff.json`.
- Refreshed `quantlab/TESTS.md`, `.agents/specs/TESTS.md`, `SPECS.md`, `RTM.md`, `NEXT_STEPS.md`, and stakeholder docs to remove the stale hash-equality visual residual where current evidence supports it.

## TDD Evidence

- RED: `cd frontend && npm test -- --run tests/public-demo.test.tsx` failed on missing `computePixelMismatchRatio`.
- GREEN: focused tests passed after adding pixel comparator and PNG smoke wiring.
- REFACTOR: kept pure pixel math in `frontend/lib/public-demo.ts`; kept PNG decoding and filesystem/browser capture in `browser-visual-smoke.mjs`.

## Verification

- `cd frontend && npm test -- --run tests/public-demo.test.tsx` -> 16 passed.
- `cd frontend && npm run visual && npm run visual:browser` -> passed; final pixel diff `0 / 1,296,000`, `mismatchRatio=0`, threshold `0.001`, screenshot hash `8acc4d0a14aeca1cc95edfcb402dcd72a41f035b5e367e497634839301fb7c29`.
- `cd frontend && npm run coverage` -> 23 tests passed, 91.42% line coverage.
- `cd frontend && npm run mutation` -> 9/9 frontend mutations killed.
- `cd frontend && npm run build` -> passed.
- `cd frontend && npm run smoke` -> passed on `127.0.0.1:3044`.
- `cd frontend && npm audit --json` -> 0 vulnerabilities.

## Residuals

- Dashboard data remains fixture-driven and `local_demo_only`; this lane does not prove full backend/live-data dashboard readiness. The export readiness panel intentionally remains `not_proven` by local dashboard contract.
- Visual baseline history is repo-committed, not CI-managed historical storage.
- Live scheduled GitHub Actions snapshot artifact remains unproven; existing schedule proof is smoke-tier.
