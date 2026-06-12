# CR-FPS-005 — Public Hosting Deployment Catch-up Proof

## Status

Implemented · Review PASSED.

## Owner

`f-public-static-showcase` / public hosting proof.

## Problem

CR-FPS-004 refreshed the committed static dashboard evidence and correctly
downgraded the branch-local hosting manifest to `configured_not_observed`
because GitHub Pages was still serving the previous `dataHash`.

After the CR-FPS-004 content was promoted to `main`, GitHub Pages began serving
the refreshed `deployment-manifest.json`. The committed proof artifacts needed a
post-deployment sync so stakeholder docs and governance rollups no longer
reported a stale branch-local deployment gap.

## Requirements

1. Probe the public GitHub Pages URL and deployed `deployment-manifest.json`.
2. Commit proof only when HTTP status is 200, deployed manifest status is 200,
   deployed `dataHash` equals the committed static dashboard hash, and deployed
   manifest contract metadata matches the committed manifest.
3. Keep the dashboard readiness panel conservative (`not_proven`) because it is
   fixture-backed local demo evidence, not a live QuantLab service.
4. Update current governance and stakeholder docs to distinguish public hosting
   parity from the dashboard's embedded local-demo readiness boundary.

## Implementation

- Re-ran the public hosting probe after `main` promotion.
- Regenerated `docs/deployment-manifest.json` from the live probe.
- Copied the refreshed probe into review assets.
- Updated current governance and stakeholder surfaces from branch-local pending
  language to deployed content-hash and manifest-contract parity.
- Updated Python mutation specs so public-hosting proof regressions now kill
  downgrades from `proven` / `matched` to weaker states.

## Evidence

- Live deployed manifest:
  `https://austinyuch.github.io/finance_algorithms/deployment-manifest.json`
  served `dataHash=035b8509a2a08b2b1abc3101902ec3d9cf5b3470c533d926e045c9deaf4f8d4e`.
- Public probe: `cd frontend && npm run probe:public-demo` ->
  `public-demo-probe: proven 200 200`.
- Static docs export: `cd frontend && npm run export:public-demo:docs` ->
  passed.

## Claim Boundary

This CR proves the committed static `docs/` artifact is now deployed with
matching content hash and manifest contract metadata. It does not change the
dashboard payload's `local_demo_only` / fixture-backed boundary and does not
prove a live QuantLab backend service.
