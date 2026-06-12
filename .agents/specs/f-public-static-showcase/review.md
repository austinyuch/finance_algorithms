# Review — F Public Static Showcase

## Verdict

Implemented · Review PASSED (configured static showcase + visual contract baseline).

Post-baseline CRs: [CR-FPS-001](./change-requests/cr-fps-001-hosting-manifest-proof-sync.md) supersedes the original hosted-availability note for the committed `docs/` artifact, and [CR-FPS-002](./change-requests/cr-fps-002-hosting-content-hash-proof.md) strengthens the proof boundary so `hostingEvidence.status=proven` requires both HTTP 200 and deployed `dataHash` parity.

## Evidence

- `cd frontend && npm test -- --run tests/dashboard.test.tsx tests/public-demo.test.tsx` -> 14 passed.
- `cd frontend && npm run visual` -> deterministic static export and visual-contract baseline check passed.
- `frontend/scripts/export-public-demo.tsx` exports either `frontend/out` or committed `docs/` static artifacts for GitHub Pages branch-source hosting.
- `docs/public-hosting-probe.json` records HTTP 200 plus deployed `deployment-manifest.json` status/hash; `docs/deployment-manifest.json` records `hashStatus=matched`.

## Claim Boundary

The public URL target is `https://austinyuch.github.io/finance_algorithms/`. The baseline review originally closed before hosted availability was observed; CR-FPS-001 records hosted reachability and CR-FPS-002 requires deployed content hash parity before current static artifact hosting is `proven`. The dashboard itself remains `local_demo_only` / fixture-backed and is not a live QuantLab service.

## Residual Risk

This baseline is a static visual contract hash, not a browser pixel screenshot. Browser screenshot regression remains a future stronger proof.
