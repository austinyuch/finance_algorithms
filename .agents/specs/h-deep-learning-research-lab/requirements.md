# Requirements — H Deep-Learning Research Lab (slice H-1)

> SDD Phase 1. Spec: `h-deep-learning-research-lab`.
> Upstream: a0-backtest-foundation, b-data-platform, d-return-risk-forecast-model,
> e-mlops-tier3-lite, real-data-oos-backtest.

## 0. Governance

- **Work classification:** `new spec` (new Epic H research-capability lane). Resolved
  via spec-master: no active spec or completed-baseline CR can absorb a multi-framework
  deep-learning research surface; it is a net-new bounded context, not a follow-up.
- **Depends On:** a0-backtest-foundation (Strategy/engine/result-record contract),
  b-data-platform (PIT vintage + CR-B21 deep history), d-return-risk-forecast-model
  (model+adapter pattern), e-mlops-tier3-lite (ExperimentRegistry lineage),
  real-data-oos-backtest (OOS-net comparison + fail-closed mechanics).
- **Impacts:** `quantlab/models/` (new framework-free DL reference model),
  `quantlab/strategies/` (framework-specific adapters allowed here only),
  `quantlab/research/` (statistical performance report + self-contained viz),
  `scripts/` (parameterized experiment CLI), `quantlab/mlops` (experiment lineage).
  No change to engine/data behavior; no change to legacy `invest_algorithms/`.
- **First-slice boundary:** This slice delivers (a) a deterministic, PIT-safe,
  framework-free **deep MLP reference forecaster** that always runs in the default
  env, (b) a **framework adapter registry** that resolves real PyTorch/JAX/TensorFlow
  backends when installed and **degrades honestly** to the reference backend when they
  are absent, (c) a deterministic, checksummed **statistical performance report**
  (OOS-net authority, distribution stats, rolling Sharpe, drawdown, learning curve),
  (d) a **self-contained SVG/HTML visualization** of that report, and (e) a
  **parameterized experiment CLI** that records MLOps lineage in `ExperimentRegistry`.
- **Explicitly deferred (later H slices, not this one):** real GPU training runs of
  torch/jax/tf models (the adapters are proven by interface + honest degradation, not
  by forcing installation); a live interactive front-end UI with server-side parameter
  re-execution; production Tier3 MLOps serving/retraining/drift (governed by the
  existing E gates and out of repo scope per the locked decisions).
- **Honesty posture:** every model output is `no_alpha_claim`. The reference MLP is a
  from-scratch deterministic neural net used to prove the research mechanism and the
  framework boundary, not an alpha source. Deep history is the CR-B21 backfill, which is
  `is_approximate=true` and strict-PIT-excluded; experiments over it run in research
  (`approximate_availability=True`) mode and inherit `no_alpha_claim`.

## 1. Functional Requirements

### Requirement 1 [REQ-H-DLMODEL-001]

**User story:** As a QuantLab researcher, I want a framework-free, deterministic deep
neural forecaster, so that I can demonstrate a trainable deep-learning model end-to-end
without requiring any ML framework to be installed and without lookahead.

#### Acceptance Criteria

1. When the forecaster receives sufficient as-of price history, it shall train a
   multi-layer perceptron (≥1 hidden layer, non-linear activation) on lookback-windowed
   returns using only rows available at or before `asof`, and return one finite expected
   return per configured symbol.
2. When trained twice from the same data, configuration, and seed, the forecaster shall
   produce identical forecasts and an identical per-epoch training loss trace
   (determinism).
3. If history is insufficient or produces non-finite values, the forecaster shall return
   a conservatively marked degraded forecast and shall not emit NaN/inf expected returns
   or volatilities.
4. The forecaster shall expose a `training_trace` (per-epoch loss) and the resolved
   `backend` label so that downstream reporting can render a learning curve.

### Requirement 2 [REQ-H-DLALLOC-001]

**User story:** As a backtest operator, I want the deep forecaster wrapped in an
A0-compatible strategy, so that it ranks on OOS-net against dumb baselines through the
existing engine without the engine ever importing an ML framework.

#### Acceptance Criteria

1. The adapter shall implement the A0 `Strategy` protocol (`fit`, `generate_signal`,
   `metadata`) and return long-only weights that sum to 1 over the configured symbols.
2. When the underlying forecasts are degraded, the adapter shall fall back to equal
   weights and record `forecast_status="degraded"`.
3. The adapter `metadata` shall include `name`, `framework` (the resolved backend),
   `claim_boundary="no_alpha_claim"`, and the learning-curve length.

### Requirement 3 [REQ-H-FWBACKEND-001]

**User story:** As a maintainer, I want a framework adapter registry that resolves real
PyTorch/JAX/TensorFlow backends when present and degrades honestly otherwise, so that the
multi-framework story is demonstrable and the framework-isolation rule is never violated.

#### Acceptance Criteria

1. The registry shall expose `available_backends()` and `resolve(name)`; `resolve` shall
   return the requested backend when its framework imports successfully and shall
   **fall back to the deterministic `reference` backend** (never raise) when the framework
   is absent, recording the fallback reason.
2. The registry shall support the labels `reference`, `pytorch`, `jax`, `tensorflow`;
   `reference` shall always be available.
3. No module under `quantlab.engine` or `quantlab.data` shall import the registry or any
   ML framework (enforced by import-linter); framework imports shall be lazy and confined
   to adapter/registry modules.
4. `resolve` for an unknown backend name shall fail closed with a `ValueError`.

### Requirement 4 [REQ-H-STATREPORT-001]

**User story:** As a research reviewer, I want a deterministic, checksummed statistical
performance report comparing the deep model to a baseline, so that model efficacy is
presented with honest, reproducible statistics under `no_alpha_claim`.

#### Acceptance Criteria

1. The report shall be ranked on **out-of-sample net Sharpe only**, keep the baseline
   visible, and carry `claim_boundary="no_alpha_claim"` and
   `metric_authority="out_of_sample_net_only"`.
2. The report shall include, per strategy: return-distribution statistics (mean, vol,
   skew, excess kurtosis, historical 5% VaR), a rolling Sharpe series, a drawdown series,
   and (for the deep model) the learning-curve trace.
3. The report shall carry a deterministic `checksum` over its canonical JSON, and equal
   inputs shall produce an equal checksum.
4. All numeric fields shall be finite; degenerate/empty inputs shall fail closed rather
   than emit non-finite statistics.

### Requirement 5 [REQ-H-VIZ-001]

**User story:** As a stakeholder, I want a self-contained visualization of the
performance report, so that model efficacy is legible without any network/CDN dependency
and renders under headless validation / `file://`.

#### Acceptance Criteria

1. The renderer shall emit a single self-contained SVG (and an HTML wrapper) with no
   external/CDN references and no client-side data fetch.
2. The visualization shall plot at least the equity/relative-performance curve, the
   drawdown series, the learning curve, and the return distribution, each with an
   accessible text-equivalent label.
3. The renderer shall be deterministic for equal report input.

### Requirement 6 [REQ-H-EXPERIMENT-001]

**User story:** As a researcher, I want a parameterized experiment CLI that builds a
deep-learning experiment from tunable parameters, runs it against a baseline, and records
MLOps lineage, so that the interactive "set parameters → see results" research mechanism
is demonstrable and reproducible.

#### Acceptance Criteria

1. The CLI shall accept parameters (at least `hidden_units`, `lookback`, `epochs`,
   `seed`, `rebalance`, `backend`, output path) and run the deep model plus a dumb
   baseline through the engine on ≥2 real co-temporal price assets.
2. On success the CLI shall write a JSON artifact containing the computed OOS-net
   comparison, the statistical performance report, and the SVG path, register an
   `ExperimentRegistry` entry (deterministic id, run_ids, metrics, `no_alpha_claim`), and
   exit 0.
3. When data is insufficient (<2 co-temporal assets / thin history), the CLI shall fail
   closed with `status=insufficient_data` and exit 2, registering nothing.
4. Re-running with identical parameters shall be idempotent at the registry level (same
   deterministic `experiment_id`).

## 2. Out of Scope

- Forcing torch/tf/jax installation in the default env or proving GPU training.
- Live front-end re-execution of experiments (static viz + CLI only this slice).
- Any production-tier serving/retraining/drift readiness (governed by E Tier3 gates).
- Any alpha claim, signal-quality verdict, or strategy recommendation.
