# Tasks — E Tier3 Production Probes

- [x] 1. TDD production serving evidence [Implements REQ-E-PRODPROBE-001, REQ-E-PRODPROBE-004]
  - [x] 1.1 RED: add tests that reject localhost/non-HTTPS/in-process serving endpoints and alpha-claim prediction payloads.
    - _Eval: `uv run pytest -q tests/quantlab/test_e_1_experiment_registry.py -k production` failed before implementation with missing imports._
  - [x] 1.2 GREEN: implement `build_production_serving_evidence` and `validate_production_serving_evidence`.
    - _Eval: targeted production tests pass._
  - [x] 1.3 REFACTOR: share production identity and proof-id helpers with other production builders.
    - _Eval: E registry tests remain green._

- [x] 2. TDD production retraining evidence [Implements REQ-E-PRODPROBE-002, REQ-E-PRODPROBE-004]
  - [x] 2.1 RED: add tests that reject local orchestrators, incomplete runs, alpha claims, missing artifact URI, and missing OOS-net metrics.
  - [x] 2.2 GREEN: implement `build_production_retraining_evidence` and `validate_production_retraining_evidence`.
  - [x] 2.3 REFACTOR: reuse OOS-net metric extraction and proof identity helpers.

- [x] 3. TDD production automated drift monitoring evidence [Implements REQ-E-PRODPROBE-003, REQ-E-PRODPROBE-004]
  - [x] 3.1 RED: add tests that reject local monitor identity, unsupported status, alpha claims, and empty deltas.
  - [x] 3.2 GREEN: implement `build_production_automated_drift_monitoring_evidence` and `validate_production_automated_drift_monitoring_evidence`.
  - [x] 3.3 REFACTOR: keep status/delta normalization deterministic.

- [x] 4. Integration, mutation, and governance closeout [Implements REQ-E-PRODPROBE-001, REQ-E-PRODPROBE-002, REQ-E-PRODPROBE-003, REQ-E-PRODPROBE-004]
  - [x] 4.1 Verify governed production triplet can satisfy the Tier3 gate while malformed artifacts fail validators.
  - [x] 4.2 Add mutation targets for production endpoint and retraining status gates.
  - [x] 4.2a RED/GREEN/REFACTOR: harden `external_proof_id` from non-empty
    string to traceable external HTTPS URL for serving, retraining, drift, and
    validators.
    - _Eval: `test_production_evidence_requires_traceable_external_proof_uri`
      failed before the URI gate, then passed; `test_pbt_production_external_proof_id_requires_https_url`
      failed before the HTTPS-only gate, then passed; `e-production-external-proof-uri-gate`
      mutation killed._
  - [x] 4.2b RED/GREEN/REFACTOR: harden production retraining orchestrator and
    drift monitor identities from non-local labels to allowlisted URI-backed
    identities.
    - _Eval: `test_pbt_production_external_identities_require_uri_authority`
      failed before the identity URI-scheme gate, then passed; later expanded to
      reject non-allowlisted `http://`, `ftp://`, and `ssh://` identity
      schemes while preserving governed `https` / `github-actions` identities;
      `e-production-external-identity-uri-gate` mutation killed._
  - [x] 4.2c RED/GREEN/REFACTOR: harden final Tier3 readiness against local
    manifest artifact URIs when all production evidence maps otherwise pass.
    - _Eval: `test_production_evidence_triplet_requires_external_manifest_artifact`
      failed with a `file://` manifest before the gate, then passed as sampled
      PBT over `file://`, `memory://`, bare labels, and localhost URIs;
      `e-tier3-manifest-artifact-uri-gate` mutation killed._
  - [x] 4.2d RED/GREEN/REFACTOR: harden production retraining result
    `artifact_uri` from non-empty to allowlisted remote artifact URI.
    - _Eval: `test_pbt_production_retraining_artifact_uri_requires_external_authority`
      failed before the artifact URI gate, then passed as sampled PBT over
      `file://`, `memory://`, bare labels, localhost, non-TLS HTTP, `ftp://`,
      `ssh://`, and control-plane URIs;
      `e-production-retraining-artifact-uri-gate` mutation killed._
  - [x] 4.2g RED/GREEN/REFACTOR: restrict production manifest and retraining
    artifact URIs to allowlisted remote artifact schemes (`https`, `s3`, `gs`,
    `az`, `abfs`, `abfss`) instead of accepting any URI with authority.
    - _Eval: manifest and retraining artifact PBT samples reject non-TLS HTTP,
      `ftp://`, `ssh://`, and `github-actions://` artifact locations while
      keeping `s3://` happy-path evidence valid; `e-production-artifact-scheme-allowlist-gate`
      mutation killed._
  - [x] 4.2e RED/GREEN/REFACTOR: harden production drift monitoring `threshold`
    from optional/defaulted to explicitly positive.
    - _Eval: `test_pbt_production_drift_monitoring_requires_positive_threshold`
      failed before the threshold gate with a missing threshold, then passed as
      sampled PBT over missing, zero, and negative thresholds;
      `e-production-drift-threshold-gate` mutation killed._
  - [x] 4.2h RED/GREEN/REFACTOR: harden production serving, retraining, and
    drift `observed_at` from non-empty string to UTC timestamp.
    - _Eval: `test_pbt_production_evidence_requires_utc_observed_at`
      passed over blank, free-form, date-only, timezone-less, and non-UTC
      timestamp samples; `e-production-observed-at-utc-gate` mutation killed._
  - [x] 4.2f RED/GREEN/REFACTOR: bind production serving, retraining, and drift
    evidence to the same experiment id present in the Tier3 manifest.
    - _Eval: `test_tier3_gate_rejects_production_evidence_for_different_experiment`
      failed before the binding gate because mismatched production evidence
      returned `tier3_ready`, then passed after the gate added
      `experiment_binding`; CLI integration rejects the same mismatch;
      `e-tier3-experiment-binding-gate` mutation killed._
  - [x] 4.3 Refresh `quantlab/TESTS.md`, `.agents/specs/TESTS.md`, `RTM.md`, `SPECS.md`, `NEXT_STEPS.md`, correctness checklist, and feature catalog from upstream evidence.
  - [x] 4.4 Run full pytest, mypy, import-linter, focused line coverage, mutation, and smoke gates.
    - _Eval: 288 passed; E coverage 37 passed at 99%; production serving/retraining/proof-URL/identity-URI-scheme/manifest-artifact-URI/experiment-binding/retraining-artifact-URI/artifact-scheme-allowlist/observed-at UTC/drift-threshold mutations killed; mypy clean; import-linter KEPT._
