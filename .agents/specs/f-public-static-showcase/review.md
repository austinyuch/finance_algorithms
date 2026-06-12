# Review — F Public Static Showcase

## Verdict

Implemented · Review PASSED (configured static showcase + visual contract baseline).

Post-baseline CRs: [CR-FPS-001](./change-requests/cr-fps-001-hosting-manifest-proof-sync.md) supersedes the original hosted-availability note for the committed `docs/` artifact, [CR-FPS-002](./change-requests/cr-fps-002-hosting-content-hash-proof.md) requires deployed `dataHash` parity, [CR-FPS-003](./change-requests/cr-fps-003-hosting-manifest-contract-proof.md) requires deployed manifest contract parity before `hostingEvidence.status=proven`, [CR-FPS-004](./change-requests/cr-fps-004-dashboard-evidence-freshness.md) keeps static dashboard gate evidence current, and [CR-FPS-005](./change-requests/cr-fps-005-deployment-catchup-proof.md) records deployment catch-up proof.

## Evidence

- `cd frontend && npm test -- --run` -> 27 passed.
- `cd frontend && npm run visual` -> deterministic static export and visual-contract baseline check passed.
- `frontend/scripts/export-public-demo.tsx` exports either `frontend/out` or committed `docs/` static artifacts for GitHub Pages branch-source hosting.
- `docs/public-hosting-probe.json` records HTTP 200 plus deployed `deployment-manifest.json` status/hash/contract metadata. After CR-FPS-005, `docs/deployment-manifest.json` records `hashStatus=matched`, `manifestContractStatus=matched`, and `status=proven` for the deployed `dataHash`.

## Claim Boundary

The public URL target is `https://austinyuch.github.io/finance_algorithms/`. The baseline review originally closed before hosted availability was observed; CR-FPS-001 records hosted reachability, CR-FPS-002 requires deployed content hash parity, CR-FPS-003 requires deployed manifest contract parity, CR-FPS-004 prevents stale gate evidence in the dashboard fixture, and CR-FPS-005 records deployment catch-up after `main` served the refreshed `dataHash`. The dashboard itself remains `local_demo_only` / fixture-backed and is not a live QuantLab service.

## Residual Risk

This baseline is a static visual contract hash, not a browser pixel screenshot. Browser screenshot regression remains a future stronger proof.
