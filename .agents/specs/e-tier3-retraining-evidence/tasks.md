# Tasks — E Tier3 Retraining Evidence

- [x] 1. TDD retraining evidence builder [Implements REQ-E-RETRAIN-001, REQ-E-RETRAIN-002]
  - [x] 1.1 RED: add completed, failed, alpha-claim, missing OOS-net, and deterministic digest tests.
    - _Eval: `uv run pytest -q tests/quantlab/test_e_1_experiment_registry.py -k retraining_smoke` failed before implementation with missing imports._
  - [x] 1.2 GREEN: implement `build_retraining_smoke_evidence` and `validate_retraining_smoke_evidence`.
    - _Eval: targeted retraining smoke tests pass._
  - [x] 1.3 REFACTOR: keep implementation in existing E-lite registry module, reuse `_oos_net_metrics`, and export through `quantlab.mlops`.
    - _Eval: targeted tests remain green._

- [x] 2. Mutation, PBT, and line coverage closeout [Implements REQ-E-RETRAIN-001]
  - [x] 2.1 Add `e-retraining-smoke-status-gate` mutation.
    - _Eval: `uv run python scripts/run_mutation_spot_checks.py --only e-retraining-smoke-status-gate` is killed._
  - [x] 2.2 Add defensive validation coverage for fail-closed branches.
    - _Eval: `uv run pytest --cov=quantlab.mlops.experiment_registry --cov-report=term-missing tests/quantlab/test_e_1_experiment_registry.py` reports 100% line coverage._
  - [x] 2.3 Preserve PBT digest stability.
    - _Eval: `test_pbt_retraining_smoke_digest_is_deterministic` passes._

- [x] 3. Governance closeout [Implements REQ-E-RETRAIN-001, REQ-E-RETRAIN-002]
  - [x] 3.1 Refresh folder-level and workspace test registries from current upstream evidence.
  - [x] 3.2 Refresh `SPECS.md`, `RTM.md`, `NEXT_STEPS.md`, correctness checklist, and feature catalog with conservative readiness wording.
  - [x] 3.3 Run final Python, mypy, import-linter, and mutation gates.
