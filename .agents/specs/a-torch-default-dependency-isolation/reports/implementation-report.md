# Implementation Report

## Scope

Removed unpatched PyTorch from the default UAT/runtime dependency graph while
keeping the Epic A LSTM strategy available for a dedicated PyTorch environment.

## Changes

- Removed `torch>=2.12.0` from root `pyproject.toml`.
- Regenerated `uv.lock`, removing `torch`, `triton`, CUDA packages, and related
  transitive dependencies from the default lock.
- Added `load_lstm_strategy()` to `scripts/run_tsmc_hedge_slice.py`.
- Updated the TSMC hedge script to run hedge/baseline strategies without Torch
  and print an explicit optional-lane notice.
- Added `tests/test_dependency_security.py`.
- Added explicit PyTorch-lane skip behavior to `tests/quantlab/test_a_2_lstm.py`.
- Added mutation spot-check `root-torch-default-dependency`.
- Refreshed static showcase evidence strings and hedge-slice transcript for the
  default no-Torch runtime.

## TDD Evidence

- RED: `uv run pytest -q tests/test_dependency_security.py` failed because root
  dependencies included `torch` and the script lacked `load_lstm_strategy`.
- GREEN: after dependency and script changes, the same command passed with 2 tests.
- REFACTOR / mutation: `root-torch-default-dependency` was killed when it
  reintroduced `torch>=2.12.0` in `pyproject.toml`.

## Verification

- `uv sync` removed `torch==2.12.0`, `triton`, CUDA packages, and related
  transitive dependencies.
- `rg -n "name = \"torch\"|torch>=|torch" uv.lock pyproject.toml` only finds the
  import-linter forbidden module list.
- `uv run pytest -q tests/test_dependency_security.py` -> 2 passed.
- `uv run python scripts/run_mutation_spot_checks.py --only root-torch-default-dependency`
  -> KILLED.
- `uv run pytest -q tests/test_mutation_spot_checks.py` -> 8 passed.
- `uv run python scripts/run_tsmc_hedge_slice.py` -> exits 0 with explicit
  PyTorch-lane skip notice and non-LSTM leaderboard.
- `uv run pytest -q` -> 188 passed, 1 skipped.
- `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py --ignore-missing-imports`
  -> clean over 51 files.
- `uv run lint-imports` -> KEPT.

## Claim Boundary

This closes root default dependency reachability for Dependabot alert #7. It does
not prove GitHub has rescanned and closed the alert yet, and it does not remove
the optional PyTorch strategy lane.
