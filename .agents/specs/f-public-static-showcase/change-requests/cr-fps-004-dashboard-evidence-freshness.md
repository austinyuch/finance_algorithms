# CR-FPS-004 — Static Dashboard Gate Evidence Freshness

## Status

Implemented · Review PASSED.

## Owner

`f-public-static-showcase` / F static dashboard evidence.

## Problem

The committed static showcase payload and generated HTML still displayed older
frontend gate evidence (`mutation 9/9 killed`, `F Next.js coverage 91.42%`)
after the current governed frontend evidence had advanced to 27 tests,
91.81% line coverage, and 12/12 frontend mutations killed.

That stale dashboard evidence made the public static artifact weaker than the
current spec/test registry and could mislead stakeholder-facing review/manual
artifacts.

## Requirements

1. Static dashboard evidence must show the current governed frontend and
   Python evidence counts.
2. A unit test must fail if the dashboard fixture reintroduces stale frontend
   gate evidence such as `mutation 9/9 killed` or `F Next.js coverage 91.42%`.
3. Frontend mutation coverage must kill a stale gate-evidence regression.
4. If refreshed static content no longer matches the currently deployed
   GitHub Pages manifest hash, the branch manifest must remain
   `configured_not_observed` until deployment catches up.

## Implementation

- Refreshed static dashboard evidence strings to the then-current governed
  counts; CR-FPS-006 later replaced the inline fixture source with generated
  canonical local `LocalResultStore` / `ExperimentRegistry` scenario evidence.
- Added a dashboard test for current gate-evidence freshness.
- Added `frontend-dashboard-stale-gate-evidence` mutation coverage.
- Regenerated committed `docs/` and manual/review static showcase assets.
- Updated public-hosting governance so a branch-local content hash mismatch is
  treated as `configured_not_observed`, not `proven`.

## Evidence

- RED: `cd frontend && npm test -- --run tests/dashboard.test.tsx -t gate`
  failed while the fixture still contained `mutation 9/9 killed`.
- GREEN: `cd frontend && npm test -- --run` -> 27 passed.
- Frontend coverage: `cd frontend && npm run coverage` -> 91.81% line coverage.
- Static export: `cd frontend && npm run export:public-demo:docs` -> passed
  after visual baseline refresh.
- Frontend mutation: `cd frontend && npm run mutation` -> 12/12 killed,
  including `frontend-dashboard-stale-gate-evidence`.
- Governance guard:
  `uv run pytest -q tests/quantlab/test_governance_guards.py::test_public_hosting_manifest_carries_observed_proof`
  -> passed with branch-local hash mismatch correctly downgraded.

## Claim Boundary

This CR refreshes static dashboard evidence and prevents stale frontend gate
counts. Because the branch changes the committed `docs/` artifact before GitHub
Pages has deployed it, public-hosting parity is intentionally
`configured_not_observed` until a deployed manifest reports the same
`dataHash` and manifest contract metadata.
