# Tasks — Epic D:First Regime Model

> SDD Phase 3. Requirements: [requirements.md](./requirements.md). Design: [design.md](./design.md).

- [x] 1. Implement PIT-safe regime signal contract and feature builder
  - [x] 1.1 RED: add tests for stable regime labels, missing-feature fallback, and `available_date <= asof` feature access.
    - _Requirement: [Implements REQ-D-REGIME-001, REQ-D-HOOK-001]_
    - _Eval: `uv run pytest -q tests/quantlab/test_d_1_regime.py` initially fails._
  - [x] 1.2 GREEN: add `quantlab/models/regime.py` and PIT-safe feature helpers with no engine/data ML framework imports.
    - _Requirement: [Implements REQ-D-REGIME-001, REQ-D-HOOK-001]_
    - _Eval: `uv run pytest -q tests/quantlab/test_d_1_regime.py` passes._
  - [x] 1.3 REFACTOR: simplify labels/metadata and confirm deterministic output remains unchanged.
    - _Requirement: [Implements REQ-D-HOOK-001]_
    - _Eval: targeted tests remain green._

- [x] 2. Add OOS-net baseline comparison
  - [x] 2.1 RED: add integration test requiring regime-model leaderboard rows next to static/no-regime baseline.
    - _Requirement: [Implements REQ-D-BASELINE-001]_
    - _Eval: targeted D integration test initially fails._
  - [x] 2.2 GREEN: wire the first regime signal into an A0-compatible strategy or strategy adapter.
    - _Requirement: [Implements REQ-D-BASELINE-001, REQ-D-HOOK-001]_
    - _Eval: targeted D tests pass._
  - [x] 2.3 REFACTOR: keep the adapter framework-light and preserve import isolation.
    - _Requirement: [Implements REQ-D-HOOK-001]_
    - _Eval: `uv run lint-imports`; targeted D tests._

- [x] 3. Closeout evidence and governance
  - [x] 3.1 Refresh `quantlab/TESTS.md` and workspace `.agents/specs/TESTS.md` through test-registry governance.
    - _Requirement: [Implements REQ-D-BASELINE-001]_
    - _Eval: test registry points to fresh D evidence._
  - [x] 3.2 Add a conservative writeup: report OOS-net comparison, data source, and whether the model beat the baseline.
    - _Requirement: [Implements REQ-D-BASELINE-001]_
    - _Eval: writeup avoids alpha claims unless supported by evidence._
  - [x] 3.3 Review gate: run `uv run pytest -q`, `uv run mypy quantlab/ --ignore-missing-imports`, and `uv run lint-imports`.
    - _Requirement: [Implements REQ-D-REGIME-001, REQ-D-BASELINE-001, REQ-D-HOOK-001]_
    - _Eval: final review can cite fresh command output._

- [x] 4. D-3 real-source-format benchmark continuation
  - [x] 4.1 RED: add vintage-loader benchmark tests with PBT as-of-gated date selection and OOS baseline logging.
    - _Requirement: [Extends REQ-D-BASELINE-001, REQ-D-HOOK-001]_
    - _Eval: `uv run pytest -q tests/quantlab/test_d_3_real_data_regime_benchmark.py` initially fails._
  - [x] 4.2 GREEN: add `quantlab/models/regime_benchmark.py` to run regime vs static baseline using A0 PIT provider data.
    - _Requirement: [Extends REQ-D-BASELINE-001]_
    - _Eval: targeted D-3 tests pass._
  - [x] 4.3 REFACTOR: keep benchmark helper small, explicit about `no_alpha_claim`, and measured by line coverage/mutation.
    - _Requirement: [Extends REQ-D-BASELINE-001]_
    - _Eval: D-3 helper line coverage 92%; claim-boundary mutation killed._
