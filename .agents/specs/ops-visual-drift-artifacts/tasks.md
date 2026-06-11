# Tasks — Ops Visual Drift Artifacts

Lane classification: CR overlay against completed B/F/E/D baselines.

- [x] 1. B scheduled snapshot real ops proof [Implements REQ-OVD-B-SCHEDULE]
  - [x] 1.1 RED: add tests for scheduled proof status, degraded nonzero exit handling, and workflow command smoke.
  - [x] 1.2 GREEN: add schedule run proof builder and workflow config.
  - [x] 1.3 REFACTOR: reuse snapshot report validation and preserve smoke/live labels.
  - _Eval: `uv run pytest -q tests/test_daily_snapshot.py`._
- [x] 2. F visual diff thresholding [Implements REQ-OVD-F-VISUAL-DIFF]
  - [x] 2.1 RED: add Vitest/PBT coverage for threshold pass/fail and malformed evidence.
  - [x] 2.2 GREEN: add browser visual diff evidence builder and script output.
  - [x] 2.3 REFACTOR: keep screenshot proof and diff gate as separate artifacts.
  - _Eval: `cd frontend && npm test -- --run tests/public-demo.test.tsx && npm run visual:browser`._
- [x] 3. E drift monitoring first slice [Implements REQ-OVD-E-DRIFT]
  - [x] 3.1 RED: add drift assessment unit/PBT tests and overclaim rejection.
  - [x] 3.2 GREEN: add drift assessment report builder and validator.
  - [x] 3.3 REFACTOR: preserve non-serving/no-retraining boundary.
  - _Eval: `uv run pytest -q tests/quantlab/test_e_1_experiment_registry.py`._
- [x] 4. B source-contract restoration decision [Implements REQ-OVD-B-SOURCE]
  - [x] 4.1 RED: add Stooq live close-row evidence tests and PBT malformed-row rejection.
  - [x] 4.2 GREEN: add source reopen evidence helper and decision gate.
  - [x] 4.3 REFACTOR: keep source status summary non-probing.
  - _Eval: `uv run pytest -q tests/test_daily_snapshot.py`._
- [x] 5. D evaluation artifact expansion [Implements REQ-OVD-D-ARTIFACTS]
  - [x] 5.1 RED: add artifact checksum/write/validation tests and PBT row-count determinism.
  - [x] 5.2 GREEN: add D evaluation artifact builder, writer, and validator.
  - [x] 5.3 REFACTOR: keep ranking logic in existing evaluator.
  - _Eval: `uv run pytest -q tests/quantlab/test_d_6_model_family_evaluation.py`._
- [x] 6. Verification and governance closeout
  - [x] 6.1 Run full Python, typing, import, mutation, frontend coverage/build/visual/browser/probe/smoke/audit gates.
  - [x] 6.2 Refresh `quantlab/TESTS.md`, `.agents/specs/TESTS.md`, `SPECS.md`, `NEXT_STEPS.md`, and `review.md`.
