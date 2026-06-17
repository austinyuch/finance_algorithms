# Tasks — H Deep-Learning Research Lab (slice H-1)

References: [requirements.md](./requirements.md), [design.md](./design.md).

- [x] 1. RED: add failing H-1 tests before implementation
  - [x] 1.1 Add `tests/quantlab/test_h_dl_forecaster.py` (reference MLP PIT-safe +
        deterministic trace, degraded fallback, adapter long-only/sum-to-1, PBT, backend
        registry resolve/fallback/unknown, benchmark leaderboard).
    - _Requirements: [REQ-H-DLMODEL-001], [REQ-H-DLALLOC-001], [REQ-H-FWBACKEND-001]_
    - _Eval: targeted pytest fails (modules absent)._
  - [x] 1.2 Add `tests/quantlab/test_h_model_performance_report.py` (OOS-net ranking,
        stat fields finite, distribution/rolling-Sharpe/drawdown/learning-curve present,
        checksum determinism, fail-closed degenerate; viz self-containment + determinism).
    - _Requirements: [REQ-H-STATREPORT-001], [REQ-H-VIZ-001]_
    - _Eval: targeted pytest fails._
  - [x] 1.3 Add `tests/quantlab/test_h_dl_experiment_cli.py` (computed run → artifact +
        registry entry + viz exit 0; insufficient data exit 2 nothing registered;
        idempotent experiment_id).
    - _Requirements: [REQ-H-EXPERIMENT-001]_
    - _Eval: targeted pytest fails._

- [x] 2. GREEN: implement the H-1 deep-learning research slice
  - [x] 2.1 Add `quantlab/models/dl_forecaster.py` (`DeepForecastModel`,
        `NumpyMLPForecaster`, `DeepForecastAllocationStrategy`,
        `run_deep_forecast_benchmark`) and export from `quantlab.models`.
    - _Requirements: [REQ-H-DLMODEL-001], [REQ-H-DLALLOC-001]_
    - _Eval: `uv run pytest -q tests/quantlab/test_h_dl_forecaster.py`._
  - [x] 2.2 Add `quantlab/models/dl/backends.py` (`Backend`,
        `FrameworkAdapterRegistry`, lazy torch/jax/tf probes, honest `reference` fallback).
    - _Requirements: [REQ-H-FWBACKEND-001]_
    - _Eval: backend tests pass; framework absence degrades, never raises._
  - [x] 2.3 Add `quantlab/research/model_performance_report.py` and export from
        `quantlab.research`.
    - _Requirements: [REQ-H-STATREPORT-001]_
    - _Eval: `uv run pytest -q tests/quantlab/test_h_model_performance_report.py`._
  - [x] 2.4 Add `quantlab/research/model_report_viz.py` (self-contained SVG/HTML).
    - _Requirements: [REQ-H-VIZ-001]_
    - _Eval: self-containment + determinism tests pass._
  - [x] 2.5 Add `scripts/run_dl_experiment.py` (parameterized CLI + ExperimentRegistry
        lineage; fail-closed insufficient_data).
    - _Requirements: [REQ-H-EXPERIMENT-001]_
    - _Eval: `uv run pytest -q tests/quantlab/test_h_dl_experiment_cli.py`._

- [x] 3. REFACTOR: clarify without behavior drift
  - [x] 3.1 Extract shared stat helpers / naming; keep all H tests green; no public
        behavior change.
    - _Requirements: [REQ-H-STATREPORT-001], [REQ-H-DLMODEL-001]_
    - _Eval: full H test files still pass._

- [x] 4. Quality gates
  - [x] 4.1 Add the new import-linter forbidden contract (engine/data ⊁ DL backends) and
        run `uv run lint-imports`.
    - _Eval: `uv run lint-imports` KEPT._
  - [x] 4.2 Add mutation specs (OOS-net ranking, no_alpha_claim, honest fallback) to
        `scripts/run_mutation_spot_checks.py`; confirm KILLED.
    - _Eval: `uv run python scripts/run_mutation_spot_checks.py --only <names>` KILLED._
  - [x] 4.3 Trace-based line coverage over the new modules (≥85%); `uv run mypy` clean.
    - _Eval: coverage parsed ≥85%; mypy clean._
  - [x] 4.4 Full suite + visual render-validation of the SVG/HTML (headless chromium).
    - _Eval: `uv run pytest -q` green; screenshot renders cleanly._

- [x] 5. Review and governance closeout
  - [x] 5.1 Resync counts (pytest + mutation) across `quantlab/TESTS.md`,
        `.agents/specs/TESTS.md`, `scenario.py` fallback, dashboard payload/dataHash,
        visual baseline, hosting; update `SPECS.md`, `NEXT_STEPS.md`, `RTM.md`.
    - _Eval: governance guard tests pass; counts consistent cross-surface._
  - [x] 5.2 Create `review.md` (verdict, scores, FMEA closure, residual). Record an
        `ISSUE_LOG.md` audit row. Integrate the branch back via dev→main.
    - _Eval: dev==main, PRs absorbed, working tree clean._
