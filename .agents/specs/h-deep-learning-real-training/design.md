# Design — H Deep-Learning Real Training (slice H-2)

> SDD Phase 2. Requirements: [requirements.md](./requirements.md).
> Conforms to the A0 contract (`quantlab/contracts/interfaces.py`), the
> framework-isolation contract (NFR-A0-FWAGN-001), and the H-1 "DL backend boundary"
> import-linter contract. Extends the Implemented `h-deep-learning-research-lab` baseline
> additively.

## 1. Overview

H-1 built a `DeepForecastModel` whose `NumpyMLPForecaster` resolves a backend *label* via
`FrameworkAdapterRegistry` but always trains in numpy regardless of the label. H-2 makes the
resolved **`pytorch`** backend actually compute the MLP forward/backward in PyTorch, while
keeping every public shape (forecasts, `training_trace`, `backend`, the
`DeepForecastAllocationStrategy` metadata, the performance report, the experiment CLI) and
the framework-isolation invariant unchanged.

Domain language is inherited from H-1; H-2 adds one component:

- **TorchMLPTrainer** (backend-local domain service): a lazy-imported torch realization of
  the *same* MLP architecture the reference uses (standardized lookback inputs → 1 hidden
  `tanh` layer → linear head, full-batch gradient descent, fixed seed), returning forecasts
  and a per-epoch loss trace structurally identical to the reference.

The contract is "parity, not a second model": the torch path is the same math on a different
numerical engine, asserted to agree with the reference within a documented tolerance.

## 2. Architecture

```
        (framework-free core — import-linter forbids ML frameworks in engine/data)
 quantlab.data ──PIT──▶ quantlab.engine ──result-record──▶ LocalResultStore ──▶ report/viz (unchanged)
        ▲                      ▲ Strategy protocol (unchanged)
        │            ┌─────────┴───────────────────────┐
        │            │ DeepForecastAllocationStrategy   │   (H-1, unchanged)
        │            └─────────┬───────────────────────┘
        │                      │ wraps
        │            quantlab.models.dl_forecaster.NumpyMLPForecaster
        │                      │ dispatch on resolved backend:
        │              ┌───────┴────────┐
        │   backend==reference     backend==pytorch
        │   (numpy, H-1)          quantlab.models.dl.torch_trainer  ◀── NEW (lazy torch)
        │                          (same MLP math via torch autograd)
        └──────────── FrameworkAdapterRegistry (H-1: resolve/fallback, unchanged) ───────────┘
```

- **Dispatch point:** `NumpyMLPForecaster` (kept as the entry forecaster for shape stability)
  resolves the backend label as today; when the resolved label is `pytorch` it delegates the
  fit/forecast numerics to `quantlab.models.dl.torch_trainer.train_mlp_torch(...)`; otherwise
  it runs the existing numpy path. The delegation keeps `forecast()` / `training_trace` /
  `backend` identical in shape.
- **Framework boundary (ACL):** the new `torch_trainer` lives under `quantlab/models/dl/`,
  the same directory already covered by the H-1 "DL backend boundary" forbidden contract, so
  no new contract is needed — only verification it still covers the new module. The torch
  import is lazy (inside the function/module body, behind the registry's `pytorch` resolve),
  never at `dl_forecaster` import time. `report`, `viz`, `engine`, `data` import none of it.
- **Architecture parity:** identical preprocessing (same standardization, lookback windowing,
  weight-init scheme seeded equivalently), identical layer sizes/activation, identical
  full-batch GD update count (`epochs`) and learning rate, so the two engines compute the
  same function up to float/optimizer differences.

## 3. Parity Tolerance (documented control for REQ-H2-PARITY-001)

- **Tolerance:** torch vs reference per-symbol expected returns shall agree within an
  **absolute tolerance of `1e-3`** (forecasts are expected-return scalars on a standardized
  scale). Rationale: full-batch GD on an identical seeded init converges to the same basin;
  residual disagreement is float32-vs-float64 and reduction-order noise, empirically well
  under `1e-3` for this small MLP. The torch trainer shall compute in float64 to keep the gap
  tight.
- **Anti-masking guard:** the parity test shall *also* assert the torch model actually trained
  — `training_trace[-1] < training_trace[0]` (loss decreased) and `len(training_trace)==epochs`
  — so a degenerate/no-op torch path cannot pass merely by sitting inside a loose tolerance.
- If the documented tolerance cannot be met, the slice fails closed (test red) rather than
  widening tolerance silently; any tolerance change must be re-justified here.

## 4. Test Coverage Declaration

- **Optional torch lane (default-skipped via `pytest.importorskip("torch")`):**
  `tests/quantlab/test_h2_torch_training.py` — real torch training produces finite forecasts
  (REQ-H2-TORCHTRAIN-001); torch-vs-reference parity within `1e-3` + trained-not-noop
  (REQ-H2-PARITY-001); report shape/keys/ranking/`no_alpha_claim` parity with reference
  (REQ-H2-PARITY-001); same-seed determinism of forecasts + loss trace (REQ-H2-DETERMINISM-001);
  no lookahead vs reference (REQ-H2-TORCHTRAIN-001 AC4).
- **Default-env tests (no torch required):** honest fallback — `backend="pytorch"` with torch
  absent resolves to `reference`, trains, records reason, never raises (REQ-H2-OPTLANE-001 AC2);
  lazy-import assertion — importing `quantlab.models.dl_forecaster` does not import torch
  (REQ-H2-TORCHTRAIN-001 AC2 / REQ-H2-ISOLATION-001).
- **Architecture / imports:** `uv run lint-imports` KEPT with the new module under the existing
  DL backend boundary contract (REQ-H2-ISOLATION-001).
- **Mutation:** flipping the parity tolerance to "always pass" (e.g. removing the
  trained-not-noop assertion authority) and flipping the `pytorch`-absent fallback to "raise"
  must each be killed by a targeted test. Torch-lane mutations run in the torch-enabled UAT.
- **Coverage:** trace-based line coverage over `torch_trainer` and the new dispatch branch
  (target ≥85% on touched lines, measured in the torch-enabled env).

## 5. Repo-side Closure vs External Execution Boundary

- **Repo-side (default env, torch absent):** dispatch wiring, lazy `torch_trainer` module,
  honest `reference` fallback, lazy-import guard, import-linter KEPT, full default suite green
  with the new torch lane **skipped**. Fully provable here.
- **Torch-enabled capture (reproduced locally by transiently installing torch):** real torch
  training, parity, determinism, torch-lane mutations. Recorded as
  `reports/h2-torch-uat-capture.md` (+ raw transcript). Not an external-machine blocker.

## 6. Components and Interfaces

- `quantlab/models/dl/torch_trainer.py` (NEW): `train_mlp_torch(features, targets, *,
  hidden_units, epochs, seed, learning_rate) -> (weights/forecast_fn, training_trace)` — lazy
  `import torch` inside; float64; seeded; full-batch GD mirroring the reference math. Pure
  numerics, no engine/data import.
- `quantlab/models/dl_forecaster.py` (MODIFIED, additive): in `NumpyMLPForecaster.forecast`
  (and/or its internal fit), branch on `self.backend == "pytorch"` to delegate to
  `train_mlp_torch`; default `reference` path unchanged. Public attributes/return shapes
  unchanged.
- No change to `quantlab/models/dl/backends.py` resolve semantics, to
  `quantlab/research/model_performance_report.py`, to `model_report_viz.py`, or to
  `scripts/run_dl_experiment.py` — they consume the unchanged forecaster shape (the CLI's
  `--backend pytorch` simply now trains for real in a torch-enabled env, and falls back
  honestly otherwise).

## 7. Failure Mode and Effects Analysis

Carries the H-1 design rows pre-tagged `H-2.x` (FMEA-H-01/-02/-06) and adds H-2-specific modes.

| Risk ID | Failure Mode | Effect | Cause | Current Control | Sev | Occ | Det | Planned Response | Task Trace |
|---|---|---|---|---|---:|---:|---:|---|---|
| FMEA-H2-01 | torch import leaks into engine/data core | Framework-isolation broken; non-deterministic core | Eager/mis-placed torch import | Existing "DL backend boundary" import-linter contract + lazy import inside `dl/torch_trainer`; lazy-import test | 10 | 2 | 2 | `lint-imports` KEPT + import-time guard test | H2-1.2 / H2-2.1 |
| FMEA-H2-02 | torch training non-deterministic | Irreproducible research; false efficacy | Unseeded RNG / nondeterministic reductions | `torch.manual_seed`, full-batch GD, float64; same-seed determinism test | 8 | 3 | 2 | Determinism test asserts identical trace | H2-1.1 / H2-2.2 |
| FMEA-H2-03 | torch path silently diverges from reference | Untrustworthy "real training"; inconsistent leaderboard | Architecture/seed/lr mismatch between engines | Documented `1e-3` tolerance parity test + report-shape parity | 8 | 3 | 2 | Parity test red until aligned; tolerance re-justified in §3 | H2-1.1 / H2-2.2 |
| FMEA-H2-04 | Loose tolerance masks a no-op torch path | Green test, no real training | Tolerance too wide / trivial output | Anti-masking assert: loss decreased + trace length == epochs | 7 | 3 | 3 | Mutation flipping the trained-not-noop authority → killed | H2-1.1 / H2-3.2 |
| FMEA-H2-05 | torch absent breaks default env | Default build red; broken degradation story | No fallback / no importorskip | Honest `reference` fallback (never raises) + `pytest.importorskip` lane | 6 | 3 | 2 | Fallback test (default env) + skip lane | H2-1.2 / H2-2.1 |
| FMEA-H2-06 | Alpha-claim leakage via new path | Overclaim vs honesty posture | Wrong claim_boundary on torch run | `no_alpha_claim` enforced through unchanged report/adapter; mutation | 9 | 2 | 2 | Report-shape parity asserts boundary; mutation → killed | H2-1.1 / H2-3.2 |
| FMEA-H2-07 | torch re-added to default root env | Reintroduces Dependabot-isolated dependency | Dependency added to default pyproject/uv.lock | Optional lane only; default `uv sync` excludes torch; dependency-security test | 7 | 2 | 2 | Keep torch out of default lock; verify `test_dependency_security` | H2-3.1 |

## 8. Risk Response and Mitigation Plan

- **Prevent:** lazy torch import confined to `dl/torch_trainer`; identical seeded architecture;
  float64; torch kept out of the default lock.
- **Detect:** import-linter contract + lazy-import test; parity test (`1e-3` + trained-not-noop);
  determinism test; torch-lane mutations; dependency-security test.
- **Contain:** honest `reference` fallback when torch absent; optional `importorskip` lane so the
  default suite stays green; `no_alpha_claim` everywhere; fail-closed on tolerance miss.

## 9. Error Handling

- `backend="pytorch"` + torch present → real torch training.
- `backend="pytorch"` + torch absent → honest fallback to `reference` (recorded reason; no raise).
- Insufficient/degenerate data → inherits H-1 degraded/fail-closed behavior unchanged.
- Unknown backend label → `ValueError` (inherited from H-1 registry).

## 10. Evaluation Standards

- Default env: `uv run pytest -q` green with the torch lane skipped; fallback + lazy-import
  tests pass; `uv run lint-imports` KEPT; `uv run mypy ... --ignore-missing-imports` clean.
- Torch-enabled env: torch lane (training + parity within `1e-3` + determinism + report-shape
  parity) passes; torch-lane mutations KILLED; touched-line coverage ≥85%; UAT capture recorded.
- Canonical no-skip pytest count increases by the number of new torch-lane tests; counts
  resynced cross-surface at closeout (handoff to `test-registry-manager`).

## 11. Traceability References

- `REQ-H2-TORCHTRAIN-001` -> `quantlab.models.dl.torch_trainer.train_mlp_torch` + `dl_forecaster` dispatch
- `REQ-H2-PARITY-001` -> torch-vs-reference parity test + report-shape parity (`1e-3`, trained-not-noop)
- `REQ-H2-DETERMINISM-001` -> torch same-seed determinism test
- `REQ-H2-ISOLATION-001` -> existing "DL backend boundary" import-linter contract + lazy-import guard test
- `REQ-H2-OPTLANE-001` -> `pytest.importorskip("torch")` lane + honest-fallback test + `reports/h2-torch-uat-capture.md`
