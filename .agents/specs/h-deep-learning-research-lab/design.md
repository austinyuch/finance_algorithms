# Design — H Deep-Learning Research Lab (slice H-1)

> SDD Phase 2. Requirements: [requirements.md](./requirements.md).
> Conforms to A0 contract (`quantlab/contracts/interfaces.py`) and the
> framework-isolation contract (NFR-A0-FWAGN-001).

## 1. Overview

Slice H-1 adds a **Deep-Learning Research bounded context** on top of the existing A0
engine without weakening the framework-isolation invariant. The domain language:

- **DeepForecastModel** (aggregate root): a trainable forecaster that maps lookback
  windows of PIT returns to a next-period expected-return per symbol, exposing a
  `training_trace` (learning curve) and a resolved `backend`.
- **Backend** (value object): the numerical realization — `reference` (framework-free,
  always available), or `pytorch` / `jax` / `tensorflow` when installed.
- **FrameworkAdapterRegistry** (domain service): resolves a `Backend`, applying an
  anti-corruption boundary so the core never imports a framework, and degrading honestly
  to `reference` when a framework is absent.
- **PerformanceReport** (read-model / value object): deterministic, checksummed
  statistical assessment of a model run vs a baseline, OOS-net authority, `no_alpha_claim`.
- **Experiment** (lineage aggregate, via existing `ExperimentRegistry`): a reproducible,
  parameterized run with deterministic id, run_ids, and metrics.

The reference backend keeps the whole slice provable in the default environment; the
framework backends realize the *same* `DeepForecastModel` protocol so the multi-framework
story is real, not mocked.

## 2. Architecture

```
                       (framework-free core — import-linter forbids ML frameworks)
 quantlab.data ──PIT──▶ quantlab.engine ──result-record──▶ quantlab.tracking.LocalResultStore
        ▲                      ▲                                      │
        │                      │ Strategy protocol                    │ leaderboard (OOS-net)
        │            ┌─────────┴───────────┐                          ▼
        │            │ DeepForecastAllocationStrategy │  quantlab.research.model_performance_report
        │            └─────────┬───────────┘          │      (split stats, dist, rollingSharpe,
        │                      │ wraps                  │       drawdown, learning curve, checksum)
        │            quantlab.models.dl_forecaster      │                 │
        │              (NumpyMLP reference model)        │                 ▼
        │                      │ backend via             │   quantlab.research.model_report_viz
        │            quantlab.models.dl.backends         │      (self-contained SVG/HTML)
        │              FrameworkAdapterRegistry          │                 │
        │              (lazy torch/jax/tf, ACL)          │                 ▼
        └──────────────────────┴──────── scripts/run_dl_experiment.py ──▶ ExperimentRegistry
                                          (params → run → report → viz → lineage; fail-closed)
```

- **Framework boundary (ACL):** `quantlab.models.dl_forecaster` and
  `quantlab.research.*` are framework-free (numpy/pandas/stdlib). Lazy framework imports
  live only inside `quantlab.models.dl.backends` and any future
  `quantlab.strategies.dl_*` adapter. `quantlab.engine` / `quantlab.data` import none of
  them — re-asserted by a new import-linter forbidden contract.
- **Reference MLP:** deterministic numpy implementation — standardized lookback-window
  inputs → 1 hidden layer (tanh) → linear head, trained by full-batch gradient descent
  with a fixed seed; emits a per-epoch MSE `training_trace`.

## 3. Test Coverage Declaration

- **Unit:** reference MLP determinism + PIT safety + degraded fallback; adapter weights
  (long-only, sum-to-1) + degraded metadata; backend registry resolve/fallback/unknown;
  report ranking/stat fields/checksum determinism; viz self-containment + determinism.
- **Property-Based (Hypothesis):** for arbitrary positive price paths, adapter weights are
  finite, ≥0, and sum to 1; report numeric fields stay finite; backend fallback is total
  (never raises for the four known labels).
- **Integration:** experiment CLI end-to-end on a synthetic ≥2-asset co-temporal provider
  → artifact + registry entry + viz, exit 0; insufficient data → exit 2, nothing
  registered; idempotent experiment_id on re-run.
- **Smoke:** experiment CLI `--help` and a minimal computed run.
- **Mutation:** flipping the OOS-net ranking authority, the no_alpha_claim boundary, and
  the honest-degradation fallback must each be killed by a targeted test.
- **Coverage:** trace-based line coverage over the new modules via the H test files
  (target ≥85% on touched modules).

## 4. Repo-side Closure vs External Execution Boundary

Implemented repo-side and provable in the default env: reference backend, adapter,
registry + honest degradation, statistical report, SVG viz, experiment CLI + lineage.
NOT executed in this repo (deferred, honestly disclosed): real torch/jax/tf training
runs, GPU, live UI re-execution, production Tier3 serving/retraining/drift.

## 5. Components and Interfaces

- `quantlab/models/dl_forecaster.py`: `DeepForecastModel` (Protocol), `NumpyMLPForecaster`
  (reference impl, `forecast(asof, data) -> list[DeepForecast]`, `.training_trace`,
  `.backend`), `DeepForecastAllocationStrategy` (A0 Strategy adapter),
  `run_deep_forecast_benchmark(...)` (model + StaticWeights baseline → leaderboard).
- `quantlab/models/dl/backends.py`: `Backend` (frozen dataclass: name, available, reason),
  `FrameworkAdapterRegistry` with `available_backends()` / `resolve(name)`; lazy
  `importlib` probes for torch/jax/tensorflow; `reference` always available.
- `quantlab/research/model_performance_report.py`:
  `build_deep_model_performance_report(...) -> dict`, `_distribution_stats`,
  `_rolling_sharpe`, `_drawdown_series`, deterministic `checksum`.
- `quantlab/research/model_report_viz.py`: `render_performance_report_svg(report) -> str`,
  `render_performance_report_html(report) -> str` (self-contained).
- `scripts/run_dl_experiment.py`: argparse CLI → computed comparison + report + viz +
  `ExperimentRegistry` entry; fail-closed `insufficient_data` exit 2.

## 6. Failure Mode and Effects Analysis

| Risk ID | Failure Mode | Effect | Cause | Current Control | Sev | Occ | Det | Planned Response | Task Trace |
|---|---|---|---|---|---:|---:|---:|---|---|
| FMEA-H-01 | Engine/data imports an ML framework | Framework-isolation rule broken; non-deterministic core | Lazy import leaks into core | New import-linter forbidden contract + lazy import only in adapters | 10 | 2 | 2 | Fail `lint-imports`; backend module is the only framework boundary | H-2.2 |
| FMEA-H-02 | Non-deterministic deep model | Irreproducible research; false efficacy | Unseeded init / shuffling | Fixed seed, full-batch GD, numpy only; determinism test + mutation | 8 | 3 | 2 | Determinism unit test asserts identical trace | H-1.1/H-2.1 |
| FMEA-H-03 | Lookahead via training window | Inflated OOS metrics | Using rows after `asof` | PIT `history(asof,...)` only; PIT test | 9 | 3 | 3 | PIT determinism + as-of slice test | H-1.1 |
| FMEA-H-04 | Alpha-claim leakage | Overclaim vs honesty posture | Wrong claim_boundary | `no_alpha_claim` enforced in adapter/report/registry; mutation kill | 9 | 2 | 2 | Mutation flips boundary → killed | H-4.2 |
| FMEA-H-05 | Ranking on in-sample/gross | Misleading efficacy | Wrong metric authority | OOS-net-only authority; mutation kill | 8 | 2 | 2 | Mutation flips ranking → killed | H-4.2 |
| FMEA-H-06 | Backend resolve raises when framework absent | CLI crash; broken degradation story | No fallback | Total fallback to `reference`, never raises for known labels; PBT | 6 | 4 | 2 | Honest-degradation test + PBT | H-2.2 |
| FMEA-H-07 | Viz pulls CDN/remote asset | Breaks offline/headless render; supply-chain | External `<script>/<img>` | Self-contained SVG, assert no `http`/`src=`; render-validation | 5 | 2 | 2 | Self-containment unit test | H-2.4 |
| FMEA-H-08 | Non-finite stats on degenerate input | Corrupt report/checksum | Empty/flat series | Finite guards + fail-closed; unit + PBT | 7 | 3 | 2 | Fail closed before checksum | H-2.3 |

## 7. Risk Response and Mitigation Plan

- Prevent: framework-free core modules; lazy framework imports confined to the registry;
  fixed-seed numpy reference; OOS-net-only authority constants.
- Detect: import-linter contract; determinism/PIT/finite tests; mutation spot checks;
  viz self-containment assertion.
- Contain: honest degradation (`reference` fallback, `is_approximate` history excluded
  from strict PIT); fail-closed `insufficient_data`; `no_alpha_claim` everywhere.

## 8. Error Handling

Insufficient/degenerate data → conservative degraded forecast or fail-closed
`insufficient_data` (CLI exit 2). Unknown backend name → `ValueError`. Missing framework
→ silent honest fallback to `reference` with recorded reason (not an error).

## 9. Evaluation Standards

- Targeted H pytest files pass; `uv run pytest -q` full suite stays green.
- `uv run mypy quantlab/ scripts/run_dl_experiment.py --ignore-missing-imports` clean.
- `uv run lint-imports` KEPT (incl. the new forbidden contract).
- Trace-based line coverage ≥85% on the new modules.
- New mutation spot checks KILLED; registries (`TESTS.md`) reconciled; counts resynced.

## 10. Traceability References

- `REQ-H-DLMODEL-001` -> `quantlab.models.dl_forecaster.NumpyMLPForecaster`
- `REQ-H-DLALLOC-001` -> `quantlab.models.dl_forecaster.DeepForecastAllocationStrategy`
- `REQ-H-FWBACKEND-001` -> `quantlab.models.dl.backends.FrameworkAdapterRegistry`
- `REQ-H-STATREPORT-001` -> `quantlab.research.model_performance_report.build_deep_model_performance_report`
- `REQ-H-VIZ-001` -> `quantlab.research.model_report_viz.render_performance_report_svg`
- `REQ-H-EXPERIMENT-001` -> `scripts/run_dl_experiment.py`
