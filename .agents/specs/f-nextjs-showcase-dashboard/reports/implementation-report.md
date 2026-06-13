# Implementation Report — F Next.js Showcase Dashboard

Date: 2026-06-11; refreshed 2026-06-13 for superseding F evidence.

## Scope

Implemented a contained `frontend/` Next.js dashboard runtime:

- `app/page.tsx` dashboard page.
- `app/api/showcase/route.ts` JSON route.
- `components/Dashboard.tsx`.
- `lib/showcase-contract.ts` and generated `lib/showcase-payload.json`.
- Vitest tests, coverage config, frontend mutation script, visual/static export,
  public-demo probe helpers, and local HTTP smoke.

The original checked-in inline payload source has been superseded by CR-FPS-006:
`scripts/build_showcase_payload.py` now generates the dashboard payload from a
canonical local `LocalResultStore` / `ExperimentRegistry` scenario and copies it
to the frontend plus stakeholder assets.

## TDD Evidence

- RED: `npm test -- --run` failed because `../components/Dashboard` did not exist.
- GREEN: the initial runtime slice rendered the dashboard and API route.
- REFACTOR: later F lanes replaced the inline payload source, added public
  hosting/probe/visual guards, and kept the dashboard contract fail-closed.

## Verification

- Unit/PBT/integration: `npm test -- --run` -> 46 passed.
- Line coverage: `npm run coverage` -> 89.85% lines overall.
- Dependency audit: `npm audit --json` -> 0 vulnerabilities.
- Mutation: `npm run mutation` -> 26/26 killed, including source metadata,
  public-hosting freshness, expected-manifest, visual hash, threshold, and pixel
  mismatch guards.
- Build: `npm run build` -> success.
- Static/browser visual: `npm run visual` and `npm run visual:browser` -> success.
- Local HTTP smoke: `npm run smoke` -> success on a dynamically selected local port; chaos proof also passed while legacy port `3044` was occupied.
- Public probe: `npm run probe:public-demo` exits 2 with
  `configured_not_observed` while Pages serves a stale deployed `dataHash`.

## Security / Dependency Note

The current frontend audit is clean. Dependency posture is governed by
`f-public-demo-readiness` and the review gate transcript assets.

## Claim Boundary

This proves local Next.js runtime readiness and guarded static/public-demo
artifact generation only. It does not claim a live backend, live market-data
service, or production MLOps readiness. The dashboard remains
`local_demo_only` / `no_alpha_claim`.
