# Review — F Public Static Showcase

## Verdict

Implemented · Review PASSED (configured static showcase + visual contract baseline).

## Evidence

- `cd frontend && npm test -- --run tests/dashboard.test.tsx tests/public-demo.test.tsx` -> 14 passed.
- `cd frontend && npm run visual` -> deterministic static export and visual-contract baseline check passed.
- `frontend/scripts/export-public-demo.tsx` exports either `frontend/out` or committed `docs/` static artifacts for GitHub Pages branch-source hosting.

## Claim Boundary

The public URL target is configured as `https://austinyuch.github.io/finance_algorithms/`, but hosted availability is `configured_not_observed` until Pages source settings are enabled for `docs/` on the target branch and the URL is checked.

## Residual Risk

This baseline is a static visual contract hash, not a browser pixel screenshot. Browser screenshot regression remains a future stronger proof.
