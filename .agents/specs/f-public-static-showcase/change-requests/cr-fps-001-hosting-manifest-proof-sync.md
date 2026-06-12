# CR-FPS-001 — Public Hosting Manifest Proof Sync

## Status

Implemented · Review PASSED.

## Owner

`f-public-static-showcase` / F public hosting evidence.

## Problem

The rolling memo and stakeholder docs correctly referenced a proven public-hosting probe, but the committed `docs/deployment-manifest.json` still recorded `hostingEvidence.status=configured_not_observed`. The `docs/public-hosting-probe.json` evidence artifact was also missing from version control, so `npm run export:public-demo:docs` could silently regenerate the manifest back to weaker evidence.

This is a false-green/stale-evidence risk: prose could claim public hosting proof while the committed machine-readable deployment manifest contradicted it.

## Requirements

1. When a tracked public-hosting probe proves HTTP 200 for `https://austinyuch.github.io/finance_algorithms/`, the committed deployment manifest must record `hostingEvidence.status=proven`, `httpStatus=200`, and the observed timestamp.
2. The docs static export must reuse a colocated `public-hosting-probe.json` unless explicit hosting evidence environment variables are supplied.
3. Malformed probe evidence must fail the export instead of producing a plausible but unproven manifest.
4. A Python governance guard and mutation spot check must kill regressions that downgrade the committed manifest back to `configured_not_observed`.

## Implementation

- Added tracked `docs/public-hosting-probe.json` with the HTTP 200 Pages observation.
- Updated `frontend/scripts/export-public-demo.tsx` to read and validate a colocated `public-hosting-probe.json`, preserving explicit environment override behavior.
- Regenerated `docs/deployment-manifest.json` through `cd frontend && npm run export:public-demo:docs`.
- Added `test_public_hosting_manifest_carries_observed_proof` to `tests/quantlab/test_governance_guards.py`.
- Added `public-hosting-manifest-status-regression` and `governance-stale-cr-b17-promotion` to `scripts/run_mutation_spot_checks.py`.

## Evidence

- RED: `uv run pytest -q tests/quantlab/test_governance_guards.py::test_public_hosting_manifest_carries_observed_proof` failed while manifest status was `configured_not_observed`.
- GREEN: same targeted test passed after regenerating the docs export.
- Focused governance/mutation tests: `uv run pytest -q tests/quantlab/test_governance_guards.py tests/test_mutation_spot_checks.py` -> 21 passed.
- Python full suite: `uv run pytest -q` -> 226 passed.
- Type/import gates: `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py --ignore-missing-imports` -> clean over 53 files; `uv run lint-imports` -> KEPT.
- Coverage: `uv run pytest --cov=quantlab.mlops.experiment_registry --cov-report=term-missing tests/quantlab/test_e_1_experiment_registry.py` -> 27 passed, 100%; `uv run pytest --cov=scripts.run_mutation_spot_checks --cov-report=term-missing tests/test_mutation_spot_checks.py` -> 8 passed, 90%.
- Python mutation: `uv run python scripts/run_mutation_spot_checks.py` -> 43/43 killed, including `governance-stale-cr-b17-promotion` and `public-hosting-manifest-status-regression`.
- Frontend gates: `cd frontend && npm test -- --run && npm run coverage && npm audit --json && npm run mutation && npm run export:public-demo:docs && npm run visual && npm run visual:browser && npm run probe:public-demo && npm run build && npm run smoke` -> passed; browser visual diff `230 / 1,296,000`, mismatch ratio `0.00017746913580246913`.

## Claim Boundary

This CR proves only the committed static GitHub Pages deployment artifact and hosted URL observation. The dashboard remains fixture-backed and `local_demo_only`; this CR does not create live backend, live data, auth, or Tier3 production readiness.
