# Design — A Torch Default Dependency Isolation

Requirement source: [requirements.md](./requirements.md).

## Overview

This lane narrows the default Python dependency surface. PyTorch remains a
strategy-layer capability, but it is no longer part of the root UAT/runtime lock.
The default TSMC demo becomes honest about whether the optional PyTorch lane is
installed.

## Architecture

- `pyproject.toml`: remove `torch>=2.12.0` from `[project].dependencies`.
- `uv.lock`: regenerated from the root dependency set, removing `torch`,
  `triton`, CUDA packages, and related transitive packages.
- `quantlab/envs/pytorch.txt`: remains the dedicated PyTorch lane definition.
- `scripts/run_tsmc_hedge_slice.py`: lazy-loads `quantlab.strategies.lstm` only
  when Torch is installed; otherwise runs hedge/baseline strategies and emits an
  explicit optional-lane notice.
- `tests/test_dependency_security.py`: guards the root dependency boundary and
  the no-Torch demo smoke path.
- `tests/quantlab/test_a_2_lstm.py`: skips with an explicit reason when the
  optional PyTorch lane is not installed.

## Test Coverage Declaration

- Real-wired evidence: `uv sync`, `uv run pytest -q`,
  `uv run python scripts/run_tsmc_hedge_slice.py`.
- Negative coverage: dependency test rejects root `torch` dependency.
- Mutation coverage: `root-torch-default-dependency` mutates `pyproject.toml`
  to re-add Torch and is killed by the dependency-security test.
- Existing PBT coverage remains in the full test suite; this lane does not add
  randomized dependency parsing.

## Repo-side Closure vs External Execution Boundary

- Repo-side closure is complete when default sync excludes Torch and local tests
  prove graceful no-Torch behavior.
- External execution remains pending until GitHub Dependabot rescans `main` and
  updates alert #7 state.

## Contracts

No public API or data contract changes. This is dependency-surface governance and
CLI demo fallback behavior.

## Components and Interfaces

- `load_lstm_strategy()`: returns `LSTMStrategy` when Torch is available, returns
  `None` only for `ModuleNotFoundError(name="torch")`, and re-raises unrelated
  import errors to avoid hiding real bugs.
- `run_tsmc_hedge_slice.py` output: default output omits `LSTMStrategy` and emits
  a stderr notice describing the optional PyTorch lane.

## FMEA

| Risk ID | Failure Mode | Effect | Current Control | Planned Response | Task |
|---|---|---|---|---|---|
| FMEA-ATORCH-1 | Torch remains in root lock despite advisory | false-green dependency hygiene | Dependabot alert #7 | remove root dependency; add manifest test and mutation | 1 |
| FMEA-ATORCH-2 | Demo fails when optional Torch is absent | broken default smoke path | direct import currently fails | lazy import and explicit fallback notice | 2 |
| FMEA-ATORCH-3 | Optional LSTM proof is overstated after skip | stakeholder overclaim | LSTM tests previously passed in default env | explicit skip reason and docs/test registry update | 3 |
| FMEA-ATORCH-4 | Lazy import hides unrelated strategy bugs | false green | none | catch only missing `torch`, re-raise other import errors | 2 |

## EDD / Success Criteria

- `uv run pytest -q tests/test_dependency_security.py` passes.
- `uv run python scripts/run_mutation_spot_checks.py --only root-torch-default-dependency`
  reports `KILLED`.
- `uv sync` removes Torch and CUDA transitive packages from the default env.
- `uv run pytest -q` passes with one explicit PyTorch-lane skip.
- `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py --ignore-missing-imports`
  is clean.
- `uv run lint-imports` remains KEPT.

## Traceability References

- REQ-ATORCH-001 -> dependency manifest, lockfile, `tests/test_dependency_security.py`,
  mutation `root-torch-default-dependency`.
- REQ-ATORCH-002 -> `scripts/run_tsmc_hedge_slice.py`,
  `tests/test_dependency_security.py`, `tests/quantlab/test_a_2_lstm.py`.
