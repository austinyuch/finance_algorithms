# Tasks — A Torch Default Dependency Isolation

Lane classification: CR overlay against completed `a-tsmc-hedge-slice`.

- [x] 1. TDD root dependency isolation [Implements REQ-ATORCH-001]
  - [x] 1.1 RED: add a dependency-security test that fails while
    `pyproject.toml` includes `torch`.
  - [x] 1.2 GREEN: remove Torch from default dependencies and regenerate
    `uv.lock`.
  - [x] 1.3 REFACTOR: add mutation spot-check coverage for root Torch
    reintroduction.
  - _Eval: `uv run pytest -q tests/test_dependency_security.py`;
    `uv run python scripts/run_mutation_spot_checks.py --only root-torch-default-dependency`._

- [x] 2. Default demo graceful fallback [Implements REQ-ATORCH-002]
  - [x] 2.1 RED: test `run_tsmc_hedge_slice.py` no-Torch fallback behavior.
  - [x] 2.2 GREEN: lazy-load LSTM and emit an explicit optional-lane notice.
  - [x] 2.3 REFACTOR: catch only missing Torch so unrelated import defects still fail.
  - _Eval: `uv run python scripts/run_tsmc_hedge_slice.py`._

- [x] 3. Governance and evidence closeout [Implements REQ-ATORCH-001, REQ-ATORCH-002]
  - [x] 3.1 Refresh test registries, RTM/SPECS/NEXT_STEPS, stakeholder docs,
    and static showcase evidence strings.
  - [x] 3.2 Record implementation report and review including security-review summary.
  - _Eval: full Python gates, dependency scan readback, and stale claim search._
