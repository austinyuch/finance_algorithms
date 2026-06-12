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
    string to traceable non-local URI for serving, retraining, drift, and
    validators.
    - _Eval: `test_production_evidence_requires_traceable_external_proof_uri`
      failed before the URI gate, then passed; `e-production-external-proof-uri-gate`
      mutation killed._
  - [x] 4.3 Refresh `quantlab/TESTS.md`, `.agents/specs/TESTS.md`, `RTM.md`, `SPECS.md`, `NEXT_STEPS.md`, correctness checklist, and feature catalog from upstream evidence.
  - [x] 4.4 Run full pytest, mypy, import-linter, focused line coverage, mutation, and smoke gates.
    - _Eval: 210 passed, 1 skipped; E coverage 27 passed at 100%; production serving/retraining mutations killed; mypy clean; import-linter KEPT._
