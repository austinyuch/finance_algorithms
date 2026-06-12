# Review — F Public Static Showcase

## Verdict

Implemented · Review PASSED (configured static showcase + visual contract baseline).

Post-baseline CRs: [CR-FPS-001](./change-requests/cr-fps-001-hosting-manifest-proof-sync.md) supersedes the original hosted-availability note for the committed `docs/` artifact, [CR-FPS-002](./change-requests/cr-fps-002-hosting-content-hash-proof.md) requires deployed `dataHash` parity, [CR-FPS-003](./change-requests/cr-fps-003-hosting-manifest-contract-proof.md) requires deployed manifest contract parity before `hostingEvidence.status=proven`, [CR-FPS-004](./change-requests/cr-fps-004-dashboard-evidence-freshness.md) keeps static dashboard gate evidence current, [CR-FPS-005](./change-requests/cr-fps-005-deployment-catchup-proof.md) records deployment catch-up proof, [CR-FPS-006](./change-requests/cr-fps-006-canonical-dashboard-source.md) replaces the inline dashboard fixture with a generated canonical local result-store artifact, and [CR-FPS-007](./change-requests/cr-fps-007-public-probe-parity-status.md) makes the standalone public probe fail closed when the deployed `dataHash` is stale.

## Evidence

- `cd frontend && npm test -- --run` -> 28 passed.
- `cd frontend && npm run visual` -> deterministic static export and visual-contract baseline check passed.
- `frontend/scripts/export-public-demo.tsx` exports either `frontend/out` or committed `docs/` static artifacts for GitHub Pages branch-source hosting.
- `docs/public-hosting-probe.json` records HTTP 200 plus deployed `deployment-manifest.json` status/hash/contract metadata. After CR-FPS-006, the branch-local generated payload has a new `dataHash`, so both `docs/public-hosting-probe.json` and `docs/deployment-manifest.json` correctly record `hashStatus=mismatched` and `status=configured_not_observed` until GitHub Pages serves the refreshed artifact.
- `frontend/lib/showcase-payload.json` records `sourceMetadata.source=local_result_store`, `sourceRecordCount=2`, and `experimentRegistry=experiment_registry`.

## Claim Boundary

The public URL target is `https://austinyuch.github.io/finance_algorithms/`. The baseline review originally closed before hosted availability was observed; CR-FPS-001 records hosted reachability, CR-FPS-002 requires deployed content hash parity, CR-FPS-003 requires deployed manifest contract parity, CR-FPS-004 prevents stale gate evidence in the dashboard payload, CR-FPS-005 records deployment catch-up after `main` served the refreshed `dataHash`, CR-FPS-006 moves the payload source from inline TypeScript fixture to a generated local result-store scenario, and CR-FPS-007 prevents the standalone probe from overclaiming stale deployed content. The dashboard itself remains `local_demo_only` and is not a live QuantLab service.

## Residual Risk

This baseline is a static visual contract hash, not a browser pixel screenshot. Browser screenshot regression remains a future stronger proof.
