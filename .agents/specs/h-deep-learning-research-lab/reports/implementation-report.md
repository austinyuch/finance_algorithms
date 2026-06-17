# Implementation Report — H Deep-Learning Research Lab (slice H-1)

## Scope delivered

A new Epic H research-capability lane built TDD+DDD on an isolated branch
(`spec/h-deep-learning-research-lab`), proven entirely in the default environment.

| Component | Module | Role |
|---|---|---|
| Reference forecaster | `quantlab/models/dl_forecaster.py` | Framework-free deterministic numpy MLP (`NumpyMLPForecaster`), PIT-safe, per-epoch learning trace; `DeepForecastAllocationStrategy` A0 adapter; `run_deep_forecast_benchmark`. |
| Backend boundary | `quantlab/models/dl/backends.py` | `FrameworkAdapterRegistry` resolves torch/jax/tf when installed, degrades honestly to `reference` otherwise (never raises for a known label); unknown label fails closed. |
| Statistical report | `quantlab/research/model_performance_report.py` | Deterministic checksummed `build_deep_model_performance_report` — OOS-net ranking authority, distribution/rolling-Sharpe/drawdown/equity/learning-curve, fail-closed on degenerate input. |
| Visualization | `quantlab/research/model_report_viz.py` | Self-contained SVG/HTML (no CDN/script/external fetch); equity, drawdown, learning curve, return distribution. |
| Experiment CLI | `scripts/run_dl_experiment.py` | Parameterized run → engine leaderboard + report + viz + `ExperimentRegistry` lineage (deterministic idempotent `experiment_id`); fail-closed `insufficient_data` (exit 2). |

## TDD trace

- RED: 22 tests added before implementation across `tests/quantlab/test_h_dl_forecaster.py`
  (10), `tests/quantlab/test_h_model_performance_report.py` (7), and
  `tests/test_h_dl_experiment_cli.py` (5) — all confirmed failing.
- GREEN: modules implemented; all 22 pass; full suite **396 passed**.
- REFACTOR: stat helpers and naming kept small/DRY; no public behaviour drift.

## Evidence

- `uv run pytest -q` → 396 passed.
- `uv run mypy quantlab/ … scripts/run_dl_experiment.py --ignore-missing-imports` → clean (67 files).
- `uv run lint-imports` → KEPT (85 files / 224 dependencies; 2 contracts — framework-agnostic core + DL backend boundary).
- Trace line coverage over the five new modules → 95.7% (per-module 91.1%–100%).
- Mutations `h-deep-report-oos-net-ranking`, `h-deep-report-no-alpha-claim`,
  `h-backend-honest-fallback` → KILLED (suite 114/114).
- Headless chromium render-validation of the report HTML → renders cleanly, self-contained.

## Honesty boundary

Everything is `no_alpha_claim`. The reference MLP proves the research mechanism and the
framework boundary, not alpha. Deep history is the CR-B21 approximate backfill consumed in
research mode (`approximate_availability=True`); strict-PIT runs are unaffected. The
report's realized net path is a transparent commission-net PIT-forward path; the canonical
OOS-net ranking remains the A0 engine leaderboard.

## Deferred (later H slices)

Real PyTorch/JAX/TensorFlow GPU training runs (adapters proven by interface + honest
degradation here), a live interactive parameter UI with server-side re-execution, and
production-tier MLOps (serving/retraining/drift — governed by the existing E Tier3 gates).
