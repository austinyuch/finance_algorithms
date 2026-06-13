# Implementation Report — E Tier3 Production Probes

## Scope

Added governed production-tier evidence builders and validators for E Tier3 readiness evidence. This closes false-green gaps where callers could hand-write production-looking maps without passing a shared validation path, combine valid production evidence maps with a local or non-allowlisted manifest artifact and still claim `tier3_ready`, pair otherwise-valid production evidence with the wrong experiment manifest, submit production orchestrator/monitor identities with arbitrary external-looking URI schemes, submit free-form or timezone-less production observation timestamps, or submit a production retraining run whose model artifact URI still points at local, bare, non-TLS HTTP, control-plane, or otherwise non-allowlisted storage.

## Implementation

- Added production serving evidence builder/validator.
  - Requires HTTPS non-local endpoint, healthy payload, no-alpha prediction, non-empty sample request, UTC observed timestamp, and traceable external HTTPS proof URL.
- Added production retraining evidence builder/validator.
  - Requires allowlisted URI-backed external orchestrator identity, completed run status, run id, UTC observed timestamp, allowlisted remote artifact URI, traceable external HTTPS proof URL, and out-of-sample net metrics.
- Added production automated drift monitoring evidence builder/validator.
  - Requires allowlisted URI-backed external monitor identity, UTC observed timestamp, supported drift status, metric deltas, an explicit positive threshold, traceable external HTTPS proof URL, and no-alpha claim boundary.
- Tightened final Tier3 readiness so a production evidence triplet still remains
  `not_ready` when the source manifest `artifact_uri` is local (`file://`,
  `memory://`, bare label, localhost URI), non-TLS HTTP, control-plane, or
  another non-allowlisted artifact scheme.
- Tightened final Tier3 readiness so otherwise-valid production evidence remains
  `not_ready` unless all evidence artifacts share one experiment id listed by
  the Tier3 manifest.
- Exported the new production evidence API through `quantlab.mlops`.
- Added PBT and defensive validation branches for local endpoint rejection and malformed production artifacts.
- Added mutation targets:
  - `e-production-serving-endpoint-gate`
  - `e-production-retraining-status-gate`
  - `e-production-external-proof-uri-gate`
  - `e-production-external-identity-uri-gate`
  - `e-tier3-manifest-artifact-uri-gate`
  - `e-tier3-experiment-binding-gate`
  - `e-production-retraining-artifact-uri-gate`
  - `e-production-artifact-scheme-allowlist-gate`
  - `e-production-observed-at-utc-gate`
  - `e-production-drift-threshold-gate`

## Verification

- RED: `uv run pytest -q tests/quantlab/test_e_1_experiment_registry.py -k production` failed before implementation with missing production evidence builder imports.
- Targeted: `uv run pytest -q tests/quantlab/test_e_1_experiment_registry.py tests/test_tier3_readiness_gate_cli.py tests/test_mutation_spot_checks.py` -> 50 passed.
- Focused line coverage: `uv run pytest --cov=quantlab.mlops.experiment_registry --cov-report=term-missing tests/quantlab/test_e_1_experiment_registry.py` -> 37 passed, 99% line coverage.
- Mutation: `uv run python scripts/run_mutation_spot_checks.py --only e-production-serving-endpoint-gate` -> killed.
- Mutation: `uv run python scripts/run_mutation_spot_checks.py --only e-production-retraining-status-gate` -> killed.
- Mutation: `uv run python scripts/run_mutation_spot_checks.py --only e-production-external-proof-uri-gate` -> killed.
- Mutation: `uv run python scripts/run_mutation_spot_checks.py --only e-production-external-identity-uri-gate` -> killed.
- Mutation: `uv run python scripts/run_mutation_spot_checks.py --only e-tier3-manifest-artifact-uri-gate` -> killed.
- Mutation: `uv run python scripts/run_mutation_spot_checks.py --only e-tier3-experiment-binding-gate` -> killed.
- Mutation: `uv run python scripts/run_mutation_spot_checks.py --only e-production-retraining-artifact-uri-gate` -> killed.
- Mutation: `uv run python scripts/run_mutation_spot_checks.py --only e-production-artifact-scheme-allowlist-gate` -> killed.
- Mutation: `uv run python scripts/run_mutation_spot_checks.py --only e-production-observed-at-utc-gate` -> killed.
- Mutation: `uv run python scripts/run_mutation_spot_checks.py --only e-production-drift-threshold-gate` -> killed.
- Full Python: `uv run pytest -q` -> 288 passed.
- Type check: `uv run mypy quantlab/ scripts/build_showcase_payload.py scripts/run_tsmc_hedge_slice.py scripts/run_vintage_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py scripts/source_quorum_proof.py scripts/stooq_contract_proof.py --ignore-missing-imports` -> clean over 58 files.
- Architecture: `uv run lint-imports` -> KEPT.

## Boundary

This slice does not execute production serving, retraining, or drift monitoring. It defines the repo-side validation path for externally supplied production proof payloads and now rejects plain, hand-written proof IDs, bare orchestrator/monitor labels, non-allowlisted production identity URI schemes, non-UTC production observed timestamps, local or non-allowlisted retraining artifacts, missing/non-positive production drift thresholds, local or non-allowlisted manifest artifacts, and mismatched experiment bindings for final readiness. Tier3 readiness remains unproven without real external production evidence with traceable HTTPS proof URLs, allowlisted production identity URI schemes, UTC observed timestamps, an explicit positive production drift threshold, an allowlisted remote production retraining artifact URI, an allowlisted remote manifest artifact URI, and a consistent experiment id bound to that manifest.
