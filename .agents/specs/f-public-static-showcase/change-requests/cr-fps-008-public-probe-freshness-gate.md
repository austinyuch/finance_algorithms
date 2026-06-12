# CR-FPS-008 — Public Probe Freshness Gate

## Problem

CR-FPS-007 made the standalone public probe fail closed when the deployed
`dataHash` is stale, but the public-hosting classifier still allowed a matching
HTTP/hash/manifest-contract observation to remain `proven` without checking
whether the observation itself was fresh. That left a stale-proof false-green
risk for future deployment catch-up checks.

## Requirements

1. Public hosting can be `proven` only when HTTP status, deployed `dataHash`,
   deployed manifest contract metadata, and observation freshness all pass.
2. Otherwise matching public-hosting evidence older than the configured
   freshness window must remain `configured_not_observed`.
3. The committed deployment manifest and standalone probe must carry
   machine-readable freshness classification for the public-hosting
   observation.
4. Frontend tests and mutation coverage must kill a freshness-gate bypass.

## Implementation

- Added `PUBLIC_HOSTING_EVIDENCE_MAX_AGE_HOURS` and freshness classification to
  `frontend/lib/public-demo.ts`.
- Extended `classifyPublicHostingEvidence(...)` so `status=proven` requires
  `freshnessStatus=fresh`.
- Added a stale-but-otherwise-matching public-hosting test and kept PBT
  classifiers deterministic with fixed `now` inputs.
- Added frontend mutation target `frontend-public-demo-hosting-freshness-gate`.
- Added standalone probe freshness metadata and helper tests covering stale,
  missing, and future observations.
- Regenerated static docs artifacts and manifest/probe evidence. The branch
  remains `configured_not_observed` because Pages still serves the old deployed
  `dataHash`, but the observation is now explicitly `fresh`.

## Evidence

- `cd frontend && npm test -- --run` -> 32 passed.
- `cd frontend && npm run coverage` -> 32 passed; line coverage 91.05%.
- `cd frontend && npm run mutation` -> 15/15 killed, including
  `frontend-public-demo-hosting-freshness-gate` and
  `frontend-public-demo-probe-freshness-status-gate`.
- `cd frontend && npm run export:public-demo` -> passed.
- `cd frontend && npm run probe:public-demo` -> exit 2 as expected while
  deployed hash is stale.
- `cd frontend && npm run export:public-demo:docs` -> passed.

## Boundary

This CR does not claim live backend, live QuantLab data, authentication,
production MLOps, or Tier3 readiness. It only prevents stale public-hosting
observations from being accepted as current deployment proof.
