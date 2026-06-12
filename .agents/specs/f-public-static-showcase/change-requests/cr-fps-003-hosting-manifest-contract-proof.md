# CR-FPS-003 — Public Hosting Manifest Contract Proof

## Status

Implemented · Review PASSED.

## Owner

`f-public-static-showcase` / F public hosting evidence.

## Problem

CR-FPS-002 required deployed `dataHash` parity before public hosting could be marked `proven`. That closed stale-content proof, but a weaker false-green remained: a deployed `deployment-manifest.json` could expose the same dashboard `dataHash` while weakening manifest metadata such as `claimBoundary`, `artifactKind`, `dashboardClaim`, or `targetUrl`.

That would allow hash-only proof to hide a manifest-contract overclaim.

## Requirements

1. Public hosting may be `proven` only when HTTP status, deployed `dataHash`, and deployed manifest contract metadata all match the committed manifest boundary.
2. Deployed manifest metadata must include target URL, artifact kind, claim boundary, and dashboard claim.
3. HTTP 200 plus matching `dataHash` but mismatched manifest metadata must remain `configured_not_observed`.
4. Frontend unit/PBT, frontend mutation, Python governance guard, and Python mutation coverage must kill hash-only or contract-mismatch regressions.

## Implementation

- Extended `PublicHostingProbe` and deployment manifest hosting evidence with deployed manifest contract fields.
- Added `manifestContractStatus` to public hosting evidence and required it to be `matched` before `status=proven`.
- Updated `frontend/scripts/probe-public-demo.mjs` to capture deployed manifest `targetUrl`, `artifactKind`, `claimBoundary`, and `dashboardClaim`.
- Updated `frontend/scripts/export-public-demo.tsx` to reject a `proven` probe missing or weakening those deployed manifest fields.
- Added frontend unit coverage for matching hash plus weakened deployed manifest claim metadata.
- Added `frontend-public-demo-hosting-manifest-contract-gate` and `public-hosting-manifest-contract-regression` mutation coverage.

## Evidence

- RED: `cd frontend && npm test -- --run tests/public-demo.test.tsx` failed when matching deployed `dataHash` plus weakened `deployedClaimBoundary` still produced `status=proven`.
- GREEN: `cd frontend && npm test -- --run` -> 26 passed.
- Frontend coverage: `cd frontend && npm run coverage` -> 91.81% line coverage.
- Live probe/export: `cd frontend && npm run probe:public-demo && npm run export:public-demo:docs` -> probe/export passed; `docs/deployment-manifest.json` records `manifestContractStatus=matched`.
- Frontend mutation: `cd frontend && npm run mutation` -> 11/11 killed, including `frontend-public-demo-hosting-manifest-contract-gate`.
- Python governance guard: `uv run pytest -q tests/quantlab/test_governance_guards.py::test_public_hosting_manifest_carries_observed_proof` -> passed.

## Claim Boundary

This CR proves only that the deployed static manifest observed at the public URL preserves the committed manifest contract metadata and content hash for this CR slice. It does not prove live backend, live QuantLab data, authentication, production MLOps, or Tier3 readiness. The current dashboard payload boundary is superseded by CR-FPS-006: generated canonical local `LocalResultStore` / `ExperimentRegistry` scenario evidence, still `local_demo_only`.
