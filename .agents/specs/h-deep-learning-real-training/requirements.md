# Requirements — H Deep-Learning Real Training (slice H-2)

> SDD Phase 1. Spec: `h-deep-learning-real-training`.
> Upstream: h-deep-learning-research-lab (H-1, Implemented · Review PASSED),
> a0-backtest-foundation, b-data-platform, real-data-oos-backtest.

## 0. Governance

- **Work classification:** `new spec` (new sibling spec folder, Epic H slice H-2).
  Resolved via spec-master: H-1 is a completed baseline (not active), and this is a
  substantial new capability slice — a real PyTorch training path, a new optional
  dependency lane, new tests/mutations, and a torch-enabled UAT capture — not a bounded
  CR overlay or a doc/lesson follow-up. It is the explicitly-deferred "later H slice"
  named in H-1 `requirements.md` §0 and pre-tagged `H-2.x` in H-1 `design.md` §6.
- **Depends On:** h-deep-learning-research-lab (the `DeepForecastModel` protocol,
  `NumpyMLPForecaster` reference, `DeepForecastAllocationStrategy`,
  `FrameworkAdapterRegistry`, `model_performance_report`, `run_dl_experiment.py`),
  a0-backtest-foundation (Strategy/engine/result-record contract), b-data-platform
  (PIT vintage + CR-B21 deep history), real-data-oos-backtest (OOS-net comparison +
  fail-closed mechanics).
- **Impacts:** `quantlab/models/dl/` (new lazy torch trainer behind the existing DL
  backend boundary), `quantlab/models/dl_forecaster.py` (additive backend dispatch — no
  change to default `reference` behavior). No change to `quantlab.engine` / `quantlab.data`
  behavior, no change to the H-1 report/viz/CLI public shape, no change to legacy
  `invest_algorithms/`. This slice does **not** weaken or rewrite the H-1 baseline; it
  realizes a backend that H-1 only resolved as a label.
- **First-slice boundary ("minimal real-train parity"):** make the resolved **PyTorch**
  backend *actually train* the existing reference MLP architecture (same standardized
  lookback inputs → 1 hidden tanh layer → linear head, full-batch gradient descent, fixed
  seed) and flow through the unchanged `DeepForecastAllocationStrategy` + A0 engine to emit
  the **same** OOS-net statistical performance report shape as H-1. Real training runs in
  an **optional, default-skipped torch lane** (mirroring `tests/quantlab/test_a_2_lstm.py`'s
  `pytest.importorskip("torch")`), proven via a torch-enabled UAT capture. When torch is
  absent the path **degrades honestly to `reference`** (never raises for a known label),
  so the default torch-excluded environment stays green.
- **Explicitly deferred (later H slices, not this one):** GPU training and larger models;
  genuinely framework-native architectures the reference cannot express (LSTM /
  transformer / conv); JAX and TensorFlow real-training backends (H-2 proves the pattern
  on PyTorch only); a live interactive front-end UI; production Tier3 MLOps
  serving/retraining/drift (governed by the existing E gates).
- **Honesty posture:** every output stays `no_alpha_claim`. The torch path proves that the
  multi-framework harness *trains for real*, not that the model has alpha. Real-vs-reference
  agreement is asserted **within a documented tolerance** (not bit-identity — float and
  optimizer differences are expected), and the test also asserts the torch model *actually
  trained* (loss decreased) so a loose tolerance cannot mask a no-op. Deep history remains
  the CR-B21 `is_approximate=true`, strict-PIT-excluded backfill; experiments over it run in
  research (`approximate_availability=True`) mode and inherit `no_alpha_claim`.

## 1. Dependencies, Impacts & CRs

- [Depends On: h-deep-learning-research-lab, a0-backtest-foundation, b-data-platform, real-data-oos-backtest]
- [Impacts: none] — additive backend realization; no completed-baseline behavior is changed.
- [Open Change Requests: none] — H-1 stays an immutable baseline; H-2 extends it additively
  via a new sibling spec, so no CR overlay against H-1 is required.

## 2. Repo-side Closure vs External Execution

- **Repo-side Closure (default torch-excluded env):** the backend dispatch wiring in
  `dl_forecaster`, the lazy torch trainer module under `quantlab/models/dl/`, the honest
  `reference` fallback when torch is absent, the import-linter "DL backend boundary"
  contract staying KEPT, and the full default suite staying green (the new torch lane is
  skipped, exactly like the LSTM lane). All provable here with no torch installed.
- **External Execution (torch-enabled capture):** the real PyTorch training run, the
  torch-vs-reference parity assertion, and torch-path determinism execute only with torch
  installed. This is **not** an external-machine blocker — it is reproduced locally by
  transiently installing torch into the venv (the same mechanism the repo already uses to
  capture the canonical no-skip pytest gate, see `ISSUE-RDO5-001`). The capture is recorded
  as a UAT evidence transcript under `reports/`.
- **External Blockers / Constraints:** torch is intentionally excluded from the default root
  env (Dependabot history, `a-torch-default-dependency-isolation`); H-2 must not re-add it
  to the default `pyproject.toml`/`uv.lock`. The optional lane and UAT capture are the only
  places torch is required.

## 3. Functional Requirements

### Requirement 1 [REQ-H2-TORCHTRAIN-001]

**User story:** As a QuantLab researcher, I want the resolved PyTorch backend to actually
train the deep forecaster (not just label itself `pytorch`), so that the multi-framework
harness demonstrably trains a real neural net end-to-end.

#### Acceptance Criteria

1. When the forecaster's backend resolves to `pytorch` (torch installed), it shall train
   the MLP using PyTorch tensors/autograd over the same architecture and PIT-windowed
   inputs as the reference, and return one finite expected return per configured symbol.
2. The torch training path shall live only under `quantlab/models/dl/` with a **lazy**
   torch import; no eager torch import shall occur at module import time of
   `quantlab.models.dl_forecaster`.
3. The torch path shall populate the same `training_trace` (per-epoch loss) and `backend`
   label so the existing learning-curve reporting renders unchanged.
4. The torch path shall use only as-of rows (`history(asof, ...)`); it shall introduce no
   lookahead relative to the reference path.

### Requirement 2 [REQ-H2-PARITY-001]

**User story:** As a research reviewer, I want the real torch run to agree with the
framework-free reference within a documented tolerance and emit the identical report shape,
so that "real training" is trustworthy and comparable, not a divergent second code path.

#### Acceptance Criteria

1. When trained on the same data, architecture, seed, learning rate, and epochs, the torch
   forecasts shall agree with the `reference` forecasts within a **documented absolute
   tolerance** recorded in `design.md`, and the test shall assert both within-tolerance
   agreement **and** that the torch model actually trained (final loss < initial loss).
2. The torch run shall flow through the unchanged `DeepForecastAllocationStrategy` and A0
   engine and produce a `build_deep_model_performance_report` output with the **same keys,
   OOS-net ranking authority, and `claim_boundary="no_alpha_claim"`** as the reference run.
3. The leaderboard shall keep the dumb baseline visible and rank on out-of-sample net
   Sharpe only, identically to H-1.

### Requirement 3 [REQ-H2-DETERMINISM-001]

**User story:** As a maintainer, I want the torch training to be deterministic, so that
experiments are reproducible and false efficacy from RNG noise is impossible.

#### Acceptance Criteria

1. When trained twice from the same data, configuration, and seed in the same environment,
   the torch path shall produce identical forecasts and an identical per-epoch loss trace.
2. The torch path shall seed all relevant RNG (`torch.manual_seed`, deterministic
   reductions / full-batch updates) before training.

### Requirement 4 [REQ-H2-ISOLATION-001]

**User story:** As a maintainer, I want the framework-isolation invariant preserved, so that
adding real torch training never lets a framework leak into the deterministic core.

#### Acceptance Criteria

1. No module under `quantlab.engine` or `quantlab.data` shall import torch or the torch
   trainer module; `uv run lint-imports` shall stay KEPT (the existing "DL backend boundary"
   contract shall cover the new module without weakening).
2. The torch trainer shall be reachable only through the `FrameworkAdapterRegistry` /
   `dl_forecaster` dispatch, not imported directly by report/viz/engine/data modules.
3. `mypy` shall stay clean over the touched modules with torch treated as an optional,
   ignore-missing-imports dependency.

### Requirement 5 [REQ-H2-OPTLANE-001]

**User story:** As a developer on the default (torch-excluded) environment, I want the real
training to live in an optional lane with honest fallback, so that the default build stays
green and the torch evidence is captured explicitly.

#### Acceptance Criteria

1. Tests exercising the real torch training shall begin with
   `pytest.importorskip("torch", ...)` so they are **skipped** in the default env and
   **run** in a torch-enabled env, exactly like `tests/quantlab/test_a_2_lstm.py`.
2. When `backend="pytorch"` is requested but torch is absent, the forecaster shall resolve
   to `reference`, train via numpy, and record the honest fallback reason — never raise for
   the known label.
3. `uv run pytest -q` in the default env shall stay green with the torch lane reported as
   skipped (the canonical no-skip count, captured in a torch-enabled venv, shall increase by
   the number of new torch-lane tests).
4. A torch-enabled UAT capture (real training + parity + determinism passing) shall be
   recorded as an evidence transcript under `reports/`.

## 4. Out of Scope

- GPU training, larger models, or any performance/throughput target.
- Framework-native architectures the reference cannot express (LSTM / transformer / conv).
- JAX and TensorFlow real-training backends (pattern proven on PyTorch only this slice).
- Live front-end re-execution; production-tier serving/retraining/drift readiness.
- Re-adding torch to the default root environment, or any alpha/efficacy claim.
