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
- Refreshed the static showcase evidence strings from superseded frontend gate counts to the then-current conservative gate evidence; CR-FPS-006 later replaced the inline fixture source with a generated canonical local result-store payload.
- Copied current diff evidence to `docs/browser-visual-diff.json`.
- Refreshed `quantlab/TESTS.md`, `.agents/specs/TESTS.md`, `SPECS.md`, `RTM.md`, `NEXT_STEPS.md`, and stakeholder docs to remove the stale hash-equality visual residual where current evidence supports it.

## TDD Evidence

- RED: `cd frontend && npm test -- --run tests/public-demo.test.tsx` failed on missing `computePixelMismatchRatio`.
- GREEN: focused tests passed after adding pixel comparator and PNG smoke wiring.
- REFACTOR: kept pure pixel math in `frontend/lib/public-demo.ts`; kept PNG decoding and filesystem/browser capture in `browser-visual-smoke.mjs`.

## Verification

Current refreshed evidence (2026-06-13):

- `cd frontend && npm test -- --run` -> 46 passed.
- `cd frontend && npm run visual && npm run visual:browser` -> passed; current pixel diff `0 / 1,296,000`, `mismatchRatio=0.0`, threshold `0.001`, screenshot hash `ddd8c9a58e2bf80e300ffa0029707dd7ccdd8533ccafc11ffcae5c3ce32a804a`.
- `cd frontend && npm run coverage` -> 89.85% line coverage.
- `cd frontend && npm run mutation` -> 26/26 frontend mutations killed.
- `cd frontend && npm audit --json` -> 0 vulnerabilities.

Original lane evidence:

- `cd frontend && npm test -- --run tests/public-demo.test.tsx` -> 16 passed.
- `cd frontend && npm run visual && npm run visual:browser` -> passed under the original baseline.
- `cd frontend && npm run coverage` -> passed.
- `cd frontend && npm run mutation` -> killed all configured frontend mutations.
- `cd frontend && npm run build` -> passed.
- `cd frontend && npm run smoke` -> passed on a dynamically selected local port; occupied-`3044` chaos smoke also passed.
- `cd frontend && npm audit --json` -> 0 vulnerabilities.

## Residuals

- Dashboard data is now generated from the canonical local result-store scenario and remains `local_demo_only`; this lane does not prove full backend/live-data dashboard readiness. The export readiness panel intentionally remains `not_proven` by local dashboard contract.
- Visual baseline history is repo-committed, not CI-managed historical storage.
- Scheduled GitHub Actions proof is governed outside this F visual lane by `b-live-scheduled-snapshot-proof` / `b-scheduled-run-observer`; current external proof is still smoke-tier, not a visual-readiness dependency.
