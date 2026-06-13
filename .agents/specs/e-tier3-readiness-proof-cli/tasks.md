# Tasks — E Tier3 Readiness Proof CLI

- [x] 1. TDD strict CLI gate [Implements REQ-E-CLI-001, REQ-E-CLI-002, REQ-E-CLI-003]
  - [x] 1.1 RED: add tests for valid production evidence gate generation, local-smoke rejection, and invalid JSON chaos rejection.
    - _Eval: `uv run pytest -q tests/test_tier3_readiness_gate_cli.py` failed before `scripts/tier3_readiness_gate.py` existed._
  - [x] 1.2 GREEN: implement `scripts/tier3_readiness_gate.py` using existing production validators and `build_tier3_readiness_gate`.
    - _Eval: targeted CLI tests pass._
  - [x] 1.3 REFACTOR: keep JSON loading/output deterministic and avoid duplicating validation logic.
    - _Eval: targeted tests remain green._

- [x] 2. Mutation, smoke, and governance closeout [Implements REQ-E-CLI-001, REQ-E-CLI-002, REQ-E-CLI-003]
  - [x] 2.1 Add `e-tier3-cli-serving-validator` mutation.
    - _Eval: mutation killed by spoofed production map chaos test._
  - [x] 2.2 Run full Python, mypy, import-linter, CLI smoke, mutation, and stale-evidence checks.
    - _Eval: current rollup `uv run pytest -q` -> 288 passed; mypy clean over 58 files; `uv run lint-imports` KEPT; `e-tier3-cli-serving-validator` and `e-tier3-manifest-artifact-uri-gate` killed._
  - [x] 2.3 Refresh `quantlab/TESTS.md`, `.agents/specs/TESTS.md`, `RTM.md`, `SPECS.md`, `NEXT_STEPS.md`, correctness checklist, and feature catalog.
    - _Eval: governance surfaces now reference 288 passed, 100/100 mutations, and the strict readiness proof CLI with external manifest artifact URI gating._
