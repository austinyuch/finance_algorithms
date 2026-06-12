# Review — F Public Static Showcase

## Verdict

Implemented · Review PASSED (configured static showcase + visual contract baseline).

Post-baseline CR: [CR-FPS-001](./change-requests/cr-fps-001-hosting-manifest-proof-sync.md) supersedes the original hosted-availability note for the committed `docs/` artifact: `docs/public-hosting-probe.json` is tracked as HTTP 200 proof and `docs/deployment-manifest.json` now records `hostingEvidence.status=proven`.

## Evidence

- `cd frontend && npm test -- --run tests/dashboard.test.tsx tests/public-demo.test.tsx` -> 14 passed.
- `cd frontend && npm run visual` -> deterministic static export and visual-contract baseline check passed.
- `frontend/scripts/export-public-demo.tsx` exports either `frontend/out` or committed `docs/` static artifacts for GitHub Pages branch-source hosting.

## Claim Boundary

The public URL target is `https://austinyuch.github.io/finance_algorithms/`. The baseline review originally closed before hosted availability was observed; CR-FPS-001 now records the committed static `docs/` artifact as hosted proof (`HTTP 200`, `no_alpha_claim`). The dashboard itself remains `local_demo_only` / fixture-backed and is not a live QuantLab service.

## Residual Risk

This baseline is a static visual contract hash, not a browser pixel screenshot. Browser screenshot regression remains a future stronger proof.
