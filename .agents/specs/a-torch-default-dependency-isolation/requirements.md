# Requirements — A Torch Default Dependency Isolation

## Introduction

Dependabot alert #7 reports `torch<=2.12.0` in the root `uv.lock` with no patched
version listed. Epic A still owns the PyTorch LSTM strategy, but the root
UAT/production install should not carry an unpatched optional ML framework when
the default demos and gates can run without it.

## Dependencies, Impacts & CRs

- Work classification: CR overlay against completed `a-tsmc-hedge-slice` and
  A0 framework-isolation governance.
- Depends On: `a-tsmc-hedge-slice`, `a0-backtest-foundation`.
- Impacts: default dependency surface in `pyproject.toml` / `uv.lock`,
  `scripts/run_tsmc_hedge_slice.py`, test registry, stakeholder docs.
- Open Change Requests: none. This lane closes the default-runtime part of
  Dependabot alert #7 by removing root lock reachability; the optional PyTorch
  lane remains documented in `quantlab/envs/pytorch.txt`.

## Repo-side Closure vs External Execution

- Repo-side closure: remove Torch from the root dependency graph, make the TSMC
  slice degrade honestly when the optional PyTorch lane is absent, and add tests
  plus mutation evidence that reject reintroducing Torch as a default dependency.
- External execution: GitHub Dependabot must rescan the default branch after
  merge before the alert state can be observed as closed.
- External blockers / constraints: the advisory has no patched version, so the
  safe local action is dependency isolation, not version upgrade.

## Requirements

### Requirement 1 [REQ-ATORCH-001]

**User story:** As a QuantLab maintainer, I want the default UAT/runtime install
to exclude unpatched optional PyTorch dependencies so that the production
dependency surface is smaller and the default lockfile does not carry known
unfixed ML framework risk.

#### Acceptance Criteria

1. When `uv sync` is run for the default project, then `torch` and its CUDA stack
   should not be installed from the root dependency graph.
2. When `pyproject.toml` and `uv.lock` are inspected, then root dependency
   metadata should not include `torch`.
3. If a future change reintroduces `torch>=...` in root project dependencies,
   then an automated test and mutation spot check should fail.

### Requirement 2 [REQ-ATORCH-002]

**User story:** As a research user, I want the TSMC hedge demo to keep running
without the optional PyTorch lane so that default smoke tests stay useful while
the LSTM strategy remains available in an isolated PyTorch environment.

#### Acceptance Criteria

1. When `scripts/run_tsmc_hedge_slice.py` runs without `torch`, then it should
   complete with non-LSTM strategies and print an explicit optional-lane notice.
2. When `torch` is installed in the dedicated PyTorch environment, then
   `quantlab.strategies.lstm.LSTMStrategy` should remain importable and governed
   by the existing LSTM tests.
3. If the default environment lacks `torch`, then PyTorch-specific tests should
   skip explicitly rather than fail ambiguously or imply LSTM proof.
