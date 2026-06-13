# CR-FPS-009 - Dashboard Visual Readiness Wire-Up

## Status

Implemented · Review PASSED.

## Owner

`f-public-static-showcase` / F dashboard demo-readiness contract.

## Problem

The dashboard had current browser visual evidence and a pixel-backed visual diff,
but the generated dashboard payload still reported
`demoReadiness.visualRegression=not_proven`. That stale local-demo field made the
UI under-wire proven repo-side visual evidence while other artifacts correctly
reported `browser-visual.png` and `browser-visual-diff.json` as passed.

## Requirements

1. The generated dashboard payload shall set `visualRegression=proven` only when
   committed browser visual diff evidence is present, `status=passed`, and
   `claimBoundary=no_alpha_claim`.
2. The dashboard payload shall keep `publicHosting=not_proven` until external
   Pages hash/manifest/probe evidence catches up.
3. The frontend dashboard contract shall reject stale `visualRegression=not_proven`
   underclaims in the committed payload.
4. Frontend mutation coverage shall kill a visual-regression underclaim.
5. The Python payload builder shall reject malformed browser visual diff evidence
   when `artifactKind`, pixel counts, `mismatchRatio`, or `maxMismatchRatio`
   cannot prove the committed threshold contract.

## Implementation

- Wired `quantlab.showcase.scenario` so evidence-backed payload generation marks
  visual regression as `proven` after `_current_evidence_tests(...)` validates the
  browser visual diff artifact.
- Added fail-closed validation for the visual diff artifact contract:
  `artifactKind=browser_visual_diff`, `status=passed`,
  `claimBoundary=no_alpha_claim`, valid pixel counts, exact
  `mismatchRatio=mismatchedPixels/totalPixels`, and
  `mismatchRatio <= maxMismatchRatio`.
- Kept direct unit-only fallback payloads conservative when no evidence root is
  supplied.
- Updated the frontend dashboard contract and dashboard tests to require
  `visualRegression=proven` in committed/generated payloads.
- Added the `frontend-visual-regression-underclaim` mutation target.
- Regenerated dashboard payload assets for `docs/`, `frontend/`, manual, and
  review consumers.

## Evidence

- RED: `uv run pytest -q tests/quantlab/test_f_1_showcase_api.py::test_canonical_showcase_artifact_reads_current_evidence_artifacts` failed while the generated payload still returned `visualRegression=not_proven`.
- RED: `uv run pytest -q tests/quantlab/test_f_1_showcase_api.py::test_canonical_showcase_artifact_rejects_failed_browser_visual_evidence` failed because malformed visual-diff `artifactKind` and ratio/threshold fields were still accepted as proof.
- GREEN: `uv run pytest -q tests/quantlab/test_f_1_showcase_api.py::test_canonical_showcase_artifact_reads_current_evidence_artifacts tests/quantlab/test_f_1_showcase_api.py::test_canonical_showcase_artifact_rejects_failed_browser_visual_evidence` -> 2 passed.
- GREEN: `cd frontend && npm test -- --run tests/dashboard.test.tsx` -> 8 passed.
- MUTATION: `cd frontend && npm run mutation` -> 26/26 killed, including `frontend-public-demo-probe-absolute-output-path`, `frontend-public-demo-export-absolute-output-dir`, `frontend-public-demo-export-stale-evidence-gate`, `frontend-public-demo-probe-manifest-colocation`, `frontend-public-demo-probe-incomplete-manifest-failclosed`, `frontend-static-export-showcase-sync`, `frontend-coverage-artifact-drift`, `frontend-visual-regression-underclaim`, `frontend-smoke-port-hardcode-regression`, and `frontend-smoke-html-api-parity-regression`.
- INTEGRATION/SMOKE: `cd frontend && npm run build && npm run visual && npm run visual:browser && npm run smoke` -> passed; browser visual diff remained `0 / 1,296,000` under threshold `0.001`, and smoke uses a dynamically selected local port with occupied-`3044` chaos coverage.
- GOVERNANCE: stakeholder payload assets and docs now keep `publicHosting=not_proven` while reporting `visualRegression=proven`.

## Boundary

This CR proves only repo-side browser visual regression evidence. It does not
claim public hosting parity, live backend data, authentication, production
serving, retraining, automated drift monitoring, or Tier3 readiness.
