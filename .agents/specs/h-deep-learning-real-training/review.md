# Review — H Deep-Learning Real Training (slice H-2)

> SDD Phase 5. Verdict authority.
> Default env (torch excluded): `uv run pytest -q` → 421 passed, 2 skipped (1 pre-existing
> flaky F PBT, see Residual); `uv run mypy quantlab/models/dl_forecaster.py
> quantlab/models/dl/torch_trainer.py quantlab/models/dl/backends.py --ignore-missing-imports`
> → clean (3 files); `uv run lint-imports` → KEPT (88 files / 242 deps, 2 contracts).
> Torch-enabled UAT (torch==2.12.0+cpu, transient): `uv run pytest -q` → **430 passed, 0
> skipped**; H-2 torch lane 4 passed; H-2 mutations both KILLED. Full evidence:
> [reports/h2-torch-uat-capture.md](./reports/h2-torch-uat-capture.md).

## Verdict: PASSED (slice H-2, repo-side + torch UAT) — governance count resync pending (deploy-coupled)

H-2 makes the resolved PyTorch backend *actually train* the deep forecaster. `train_mlp_torch`
realizes the same one-hidden-`tanh`-layer MLP via torch autograd (float64, identical seed-init),
reached only through the unchanged `DeepForecastAllocationStrategy` dispatch; it agrees with the
framework-free reference within the documented `1e-3` tolerance, is deterministic, and emits the
identical OOS-net report shape — all `no_alpha_claim`. The framework-isolation invariant is
preserved (lazy torch import confined to `quantlab/models/dl/`; import-linter KEPT; lazy-import
guard test). Real training runs in an optional default-skipped lane mirroring the LSTM lane,
proven in a torch-enabled UAT; when torch is absent it degrades honestly to `reference` and the
default build stays green. JAX/TensorFlow real backends, GPU/larger/native models, a live UI, and
production Tier3 remain deferred.

## Scores

| Dimension | Score | Notes |
|---|---:|---|
| Requirements fit | 9.0 | REQ-H2-TORCHTRAIN/PARITY/DETERMINISM/ISOLATION/OPTLANE-001 each covered by tests. |
| Design consistency | 9.0 | Additive backend dispatch; H-1 baseline immutable; no engine/data/report/CLI shape change. |
| Code quality | 8.9 | Small lazy torch trainer mirroring the reference math; seed-init parity; float64. |
| Code convention | 9.0 | Optional lane mirrors `test_a_2_lstm` `importorskip`; mutation harness pattern reused. |
| Test quality | 8.9 | Real-train + parity (with anti-masking) + determinism + report-shape + isolation + 2 mutations KILLED. |
| Overall | 8.9 | PASS (repo-side + torch UAT). |

## Live-Demo Readiness

Not a port-bound UI slice. Repo-side: default suite green (lane skipped), lint/mypy/dep-security
clean. Torch evidence: the optional lane + 2 mutations validated under torch==2.12.0+cpu and
captured in `reports/h2-torch-uat-capture.md`. No new live service; the static dashboard and
hosting posture are unaffected by the code (only the governance *count* surfaces change at
closeout — see below).

## Verification Coverage

- `uv run pytest -v tests/quantlab/test_h2_torch_training.py` (torch env) → 4 passed.
- `uv run pytest -q tests/quantlab/test_h2_backend_isolation.py` → 2 passed (both envs).
- `run_mutation_spot_checks.py --only h2-torch-real-training --only h2-torch-reference-parity-seed`
  (torch env) → both KILLED (no-op GD; seed-init drift → `0.0026 > 1e-3`).
- H-1 regression (reference path) → 17 passed.
- `uv run lint-imports` → KEPT incl. "Backtest core does not reach the DL backend boundary".

## FMEA Coverage

| Risk | Mitigation evidence |
|---|---|
| FMEA-H2-01 torch leak into core | import-linter DL-backend-boundary KEPT; subprocess lazy-import guard test (torch not in `sys.modules`). |
| FMEA-H2-02 torch non-determinism | `torch.manual_seed` + float64 full-batch GD; determinism test (identical forecasts + trace). |
| FMEA-H2-03 silent divergence from reference | `1e-3` parity test; mutation `h2-torch-reference-parity-seed` (seed drift) KILLED. |
| FMEA-H2-04 loose tolerance masks no-op | trained-not-noop assert; mutation `h2-torch-real-training` (zeroed update) KILLED. |
| FMEA-H2-05 torch absent breaks default env | honest `reference` fallback + `importorskip` lane; default suite green. |
| FMEA-H2-06 alpha-claim leakage | report-shape parity asserts `no_alpha_claim`; inherits H-1 boundary mutations. |
| FMEA-H2-07 torch re-added to default lock | optional lane only; `uv sync` removes torch; `test_dependency_security` green; lock untouched. |

## Residual Risk

- Parity is asserted within a documented `1e-3` absolute tolerance, not bit-identity (float/
  optimizer differences are expected); the anti-masking assert guards against a degenerate pass.
- The torch backend is CPU, small-model, identical-architecture parity. GPU, larger/native
  architectures (LSTM/transformer), and JAX/TensorFlow real backends are deferred to later slices.
- `no_alpha_claim` throughout — H-2 proves the harness trains for real, not model efficacy.
- **Pre-existing, unrelated:** the default-suite intermittent failure is `test_pbt_hosting_freshness_window`
  (F hosting-freshness boundary flake at `age_hours≈24.0`), logged as `ISSUE-FPS-FRESH-001`. It is
  independent of H-2 (no hosting code touched) and passes in isolation / in the 430-passed torch run.

## Closeout Pending (deploy-coupled — not yet done)

- Governance count resync: pytest no-skip **424→430**, Python mutation **118→120**. This regenerates
  the dashboard payload (→ new `dataHash`) and flips committed hosting to `configured_not_observed`
  until Pages serves it — intrinsically deploy-coupled, and it rides the **same deploy** as the
  Tier-1 CR-B21 hosting re-prove. Hand `TESTS.md` rollup to `test-registry-manager`; `SPECS.md` row
  to `spec-registry-manager`; then integrate `spec/h-deep-learning-real-training` → dev → main.
