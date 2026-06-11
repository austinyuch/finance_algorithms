# Tasks — E MLOps Tier3 Lite

References: [requirements.md](./requirements.md), [design.md](./design.md).

- [x] 1. RED: experiment registry tests
  - [x] 1.1 Add unit/PBT/integration tests before implementation.
    - _Requirements: [REQ-E-LITE-REG-001], [REQ-E-LITE-READ-001]_
    - _Eval: targeted pytest fails before `quantlab.mlops` exists._

- [x] 2. GREEN: implement registry
  - [x] 2.1 Add `quantlab/mlops/experiment_registry.py` and exports.
    - _Requirements: [REQ-E-LITE-REG-001], [REQ-E-LITE-READ-001]_
    - _Eval: targeted tests pass._

- [x] 3. REFACTOR: stabilize persistence and validation
  - [x] 3.1 Keep deterministic ID and no-alpha validation small and local.
    - _Eval: targeted tests remain green._

- [x] 4. Quality gates
  - [x] 4.1 Run line coverage.
  - [x] 4.2 Add and run mutation spot check.
  - [x] 4.3 Run full suite, mypy, and import-linter.

- [x] 5. Review and governance closeout
  - [x] 5.1 Update `quantlab/TESTS.md`, `.agents/specs/TESTS.md`, `SPECS.md`, `NEXT_STEPS.md`, and mirrors.
  - [x] 5.2 Create `review.md`.
