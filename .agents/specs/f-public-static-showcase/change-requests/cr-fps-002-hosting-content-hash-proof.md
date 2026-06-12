# CR-FPS-002 — Public Hosting Content Hash Proof

## Status

Implemented · Review PASSED.

## Owner

`f-public-static-showcase` / F public hosting evidence.

## Problem

CR-FPS-001 made the committed deployment manifest follow a tracked public-hosting probe, but the proof boundary was still too weak: HTTP 200 only proves that GitHub Pages serves a page. After a local static export changes `docs/deployment-manifest.json`, the public URL can still return HTTP 200 while serving an older deployment manifest.

That is a false-green risk for stakeholder docs and review artifacts because current-content deployment proof could be inferred from host reachability.

## Requirements

1. Public hosting may be `proven` only when GitHub Pages returns HTTP 200 and the deployed `deployment-manifest.json` exposes a `dataHash` matching the local manifest `dataHash`.
2. HTTP 200 with a missing or mismatched deployed `dataHash` must remain `configured_not_observed`.
3. `docs/public-hosting-probe.json` must capture the deployed manifest status and deployed `dataHash`.
4. Frontend unit/PBT, frontend mutation, Python governance guard, and Python mutation coverage must kill status-only or stale-hash regressions.

## Implementation

- Extended `PublicHostingProbe` and `deployment-manifest.json` hosting evidence with `deployedDataHash`, `expectedDataHash`, and `hashStatus`.
- Updated `classifyPublicHostingEvidence(...)` so `status=proven` requires `httpStatus=200` and `hashStatus=matched`.
- Updated `frontend/scripts/probe-public-demo.mjs` to fetch the deployed `deployment-manifest.json` and record its `dataHash`.
- Updated `frontend/scripts/export-public-demo.tsx` to reject a `proven` probe missing `deployedDataHash`.
- Added frontend unit/PBT coverage for stale deployed hashes and matching-hash proof.
- Added `frontend-public-demo-hosting-hash-gate` and `public-hosting-manifest-hash-regression` mutation coverage.

## Evidence

- RED: `cd frontend && npm test -- --run tests/public-demo.test.tsx` failed when HTTP 200 plus a stale deployed `dataHash` still produced `status=proven`.
- GREEN: `cd frontend && npm test -- --run tests/public-demo.test.tsx` -> 18 passed.
- Live probe: `cd frontend && npm run probe:public-demo` -> `proven 200 200`; `docs/public-hosting-probe.json` records deployed `dataHash=98ce5c660b826cb91c59ddbcc407e9bc1e262de91c89d3096c470f0bb64f84e4`.
- Static docs export: `cd frontend && npm run export:public-demo:docs` -> passed; `docs/deployment-manifest.json` records `hashStatus=matched`.
- Frontend mutation: `cd frontend && npm run mutation` -> 10/10 killed, including `frontend-public-demo-hosting-hash-gate`.
- Python governance guard: `uv run pytest -q tests/quantlab/test_governance_guards.py::test_public_hosting_manifest_carries_observed_proof` -> passed.

## Claim Boundary

This CR proves the committed static GitHub Pages artifact observed at the public URL by content hash for this CR slice. It still does not prove live backend, live QuantLab data, authentication, production MLOps, or Tier3 readiness. The current dashboard payload boundary is superseded by CR-FPS-006: generated canonical local `LocalResultStore` / `ExperimentRegistry` scenario evidence, still `local_demo_only`.
