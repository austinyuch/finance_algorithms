# Tasks — E Tier3 Serving Evidence

- [x] 1. TDD serving evidence builder [Implements REQ-E-SERVE-001, REQ-E-SERVE-002]
  - [x] 1.1 RED: add healthy, unhealthy, alpha-claim, and deterministic digest tests.
    - _Eval: `uv run pytest -q tests/quantlab/test_e_1_experiment_registry.py -k serving_smoke` fails before implementation._
  - [x] 1.2 GREEN: implement `build_serving_smoke_evidence` and `validate_serving_smoke_evidence`.
    - _Eval: targeted serving smoke tests pass._
  - [x] 1.3 REFACTOR: keep implementation in existing E-lite registry module and export through `quantlab.mlops`.
    - _Eval: targeted tests remain green._

- [x] 2. Mutation and governance closeout [Implements REQ-E-SERVE-001]
  - [x] 2.1 Add `e-serving-smoke-health-gate` mutation.
    - _Eval: `uv run python scripts/run_mutation_spot_checks.py --only e-serving-smoke-health-gate` is killed._
  - [x] 2.2 Refresh test registries and current evidence rollups.
    - _Eval: `rg` stale-count scan finds no current `197 passed` / `28/28` stale claim in current surfaces after update._

- [x] 3. Final verification [Implements REQ-E-SERVE-001, REQ-E-SERVE-002]
  - [x] 3.1 Run targeted E tests and mutation-list tests.
  - [x] 3.2 Run full Python, mypy, and import-linter gates.
  - [x] 3.3 Record review and implementation evidence.
