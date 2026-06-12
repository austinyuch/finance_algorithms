# CR-FPS-007 — Public Probe Parity Status

Status: Implemented

## Problem

After CR-FPS-006 regenerated the dashboard payload from the canonical local
`LocalResultStore` / `ExperimentRegistry` scenario, the branch-local
`docs/deployment-manifest.json` correctly downgraded public hosting to
`configured_not_observed` because GitHub Pages was still serving the previous
`dataHash`.

The standalone `frontend/scripts/probe-public-demo.mjs` still reported
`status=proven` when the public URL returned HTTP 200 and the deployed manifest
contract fields matched, even when the deployed `dataHash` did not match the
branch-local manifest. This made `docs/public-hosting-probe.json` more
optimistic than `docs/deployment-manifest.json`.

## Acceptance Criteria

1. Public probe `status=proven` requires HTTP 200, deployed `dataHash` parity
   with the local expected manifest, and matched deployed manifest contract
   metadata.
2. HTTP 200 with stale or missing deployed `dataHash` must write
   `status=configured_not_observed`, `hashStatus=mismatched|missing`, and a
   nonzero probe exit code.
3. `docs/public-hosting-probe.json` and `docs/deployment-manifest.json` must
   agree on the branch-local hosting parity state.
4. Python governance and frontend tests must reject a committed probe artifact
   that claims `proven` while the deployment manifest records a data-hash
   mismatch.

## Implementation

- Updated `frontend/scripts/probe-public-demo.mjs` to read the local expected
  manifest from `frontend/out/deployment-manifest.json` or
  `docs/deployment-manifest.json`, emit `expectedDataHash`, `hashStatus`, and
  `manifestContractStatus`, and prove only when all parity gates match.
- Strengthened `frontend/scripts/export-public-demo.tsx` so any existing probe
  artifact that claims `proven` must carry matched data-hash and manifest
  contract statuses.
- Regenerated `docs/public-hosting-probe.json` and
  `docs/deployment-manifest.json`; current branch-local evidence remains
  `configured_not_observed` because the deployed hash is stale.
- Added frontend and Python governance guards for the committed
  probe/manifest parity relationship.

## Evidence

- RED: `uv run pytest -q tests/quantlab/test_governance_guards.py::test_public_hosting_manifest_carries_observed_proof` failed while `docs/public-hosting-probe.json` still reported `status=proven` with a stale deployed hash.
- RED: `npm test -- --run tests/public-demo.test.tsx -t "committed public-hosting probe"` failed on the same stale-probe overclaim.
- Probe refresh: `QUANTLAB_PUBLIC_DEMO_PROBE_OUT_PATH=../docs/public-hosting-probe.json npm run probe:public-demo` returned exit code 2 and wrote `status=configured_not_observed`, `hashStatus=mismatched`, `manifestContractStatus=matched`.
- GREEN: `npm test -- --run tests/public-demo.test.tsx` -> 20 passed.
- GREEN: `npm test -- --run` -> 28 passed; `npm run coverage` -> 91.07% line coverage.
- GREEN: `uv run pytest -q tests/quantlab/test_governance_guards.py` -> 10 passed.
- GREEN: `npm run visual`, `npm run visual:browser`, `npm run build`, `npm run smoke`, `npm audit --json`, and `npm run mutation` passed. `npm run probe:public-demo` is expected to return exit code 2 while deployed `dataHash` is stale.

## Claim Boundary

This CR improves public-demo evidence honesty only. It does not deploy the
branch-local artifact to GitHub Pages and does not change the dashboard's
`local_demo_only` / `no_alpha_claim` posture.
