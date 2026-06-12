# CR-FPS-006 — Canonical Dashboard Source Artifact

## Status

Implemented · Review PASSED.

## Owner

`f-public-static-showcase` / F dashboard payload source.

## Problem

The public/static dashboard had real rendering, visual, and hosting evidence, but
the dashboard payload itself was still maintained as an inline TypeScript
fixture. That made the UI artifact more fixture-heavy than the repo-side F read
API proof and created a false-green risk: evidence counts and dashboard rows
could drift from the Python `LocalResultStore` / `ExperimentRegistry` source
surfaces without an explicit source-authority check.

## Requirements

1. The committed frontend dashboard payload must be generated from repo-side
   `LocalResultStore` records and `ExperimentRegistry` rows, not hand-maintained
   as an inline TypeScript object.
2. The payload must carry machine-checkable source metadata proving
   `source=local_result_store`, `sourceRecordCount=2`, and
   `experimentRegistry=experiment_registry`.
3. Frontend and Python tests must fail if the dashboard source regresses to
   `fixture_records` or if source metadata disappears.
4. Static export readiness must remain `local_demo_only`; this CR does not prove
   a live backend service, live market data dashboard, authentication, or Tier3
   production readiness.

## Implementation

- Added `quantlab.showcase.scenario` and `scripts/build_showcase_payload.py` to
  build `frontend/lib/showcase-payload.json` through `LocalResultStore`,
  `ShowcaseReadAPI`, and `ExperimentRegistry`.
- Replaced the inline `frontend/lib/showcase-fixture.ts` data source with
  `frontend/lib/showcase-data.ts`, which validates the generated JSON artifact
  through the existing dashboard contract.
- Added `sourceMetadata` to the frontend dashboard contract and API route test.
- Added Python and frontend mutation targets for source-regression protection.
- Regenerated `docs/` static export and manual/review embedded payload assets.

## Evidence

- RED: `uv run pytest -q tests/quantlab/test_f_1_showcase_api.py::test_canonical_showcase_artifact_uses_result_store_source`
  failed before `build_canonical_dashboard_artifact` existed.
- RED: `cd frontend && npm test -- --run tests/dashboard.test.tsx -t "serves validated"`
  failed while `/api/showcase` returned no `sourceMetadata`.
- GREEN: `uv run pytest -q tests/quantlab/test_f_1_showcase_api.py` -> 7 passed.
- GREEN: `cd frontend && npm test -- --run tests/dashboard.test.tsx` -> 8 passed.
- Static export: `cd frontend && npm run export:public-demo:docs` -> passed;
  because the dashboard `dataHash` changed before deployment, branch-local
  public-hosting parity is correctly `configured_not_observed`.

## Claim Boundary

This CR reduces fixture-heavy dashboard risk by moving the payload to a
canonical local result-store scenario. It still proves a deterministic local demo
artifact only. The dashboard remains `local_demo_only` and must not be described
as live backend, live data, auth, or production Tier3 evidence.
