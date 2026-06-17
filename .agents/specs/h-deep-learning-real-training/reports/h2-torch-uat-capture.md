# H-2 Torch-Enabled UAT Capture

> SDD Phase 4 evidence for `h-deep-learning-real-training` (Epic H slice H-2).
> The real-training lane is `pytest.importorskip("torch")` and is **skipped** in the
> default (torch-excluded) environment. This capture was produced by transiently
> installing CPU-only PyTorch into the venv — the same mechanism the repo uses for the
> canonical no-skip pytest gate (see `ISSUE-RDO5-001`). `uv pip install` is imperative and
> does **not** modify `pyproject.toml` / `uv.lock`; the default lock stays torch-excluded
> (verified by `test_dependency_security`).

## Environment

- Transient: `uv pip install torch --index-url https://download.pytorch.org/whl/cpu`
  → `torch==2.12.0+cpu` (CPU-only).
- Restored afterwards with `uv sync` (default env, torch excluded).

## Repo-side evidence (default torch-excluded env)

| Gate | Command | Result |
|---|---|---|
| New H-2 default-env tests | `uv run pytest -q tests/quantlab/test_h2_backend_isolation.py` | 2 passed |
| Torch lane (default env) | `uv run pytest -q tests/quantlab/test_h2_torch_training.py` | 1 skipped (importorskip) |
| Import architecture | `uv run lint-imports` | KEPT — 88 files / 242 deps; "Backtest core does not reach the DL backend boundary" KEPT |
| Type check | `uv run mypy quantlab/models/dl_forecaster.py quantlab/models/dl/torch_trainer.py quantlab/models/dl/backends.py --ignore-missing-imports` | clean, 3 files |
| Dependency isolation | `uv run pytest -q tests/test_dependency_security.py` | 2 passed (torch stays out of default lock) |
| H-1 regression | `uv run pytest -q tests/quantlab/test_h_dl_forecaster.py tests/quantlab/test_h_model_performance_report.py` | 17 passed (reference path unchanged) |

## Torch-enabled evidence (torch==2.12.0+cpu installed)

| Gate | Command | Result |
|---|---|---|
| Real-training lane | `uv run pytest -v tests/quantlab/test_h2_torch_training.py` | **4 passed** |
| — resolves + trains | `test_pytorch_backend_actually_resolves_and_trains` | PASSED (`backend=="pytorch"`, trace len 30, loss decreased) |
| — parity within tol | `test_pytorch_matches_reference_within_documented_tolerance` | PASSED (torch vs reference < `1e-3`; trained-not-noop) |
| — report-shape parity | `test_pytorch_benchmark_report_shape_parity` | PASSED (same keys/ranking/`no_alpha_claim`, `backend=="pytorch"`) |
| — determinism | `test_pytorch_training_is_deterministic` | PASSED (identical forecasts + trace for equal seed) |
| Isolation (torch present) | `uv run pytest -q tests/quantlab/test_h2_backend_isolation.py` | 2 passed |
| Torch mutations | `... run_mutation_spot_checks.py --only h2-torch-real-training --only h2-torch-reference-parity-seed` | **both KILLED** |
| — `h2-torch-real-training` | no-op GD update (`p -= 0.0 * p.grad`) | KILLED (parity diverges; loss flat) |
| — `h2-torch-reference-parity-seed` | seed-init drift (`default_rng(seed+1)`) | KILLED (parity 0.0026 > `1e-3`) |

## Parity observation

With identical seed-init and float64, the torch run agreed with the framework-free
reference to within the documented `1e-3` absolute tolerance (well under it for the
unmutated path). The `seed+1` mutation produced a `0.0026` gap — confirming the tolerance
is tight enough to detect a genuine init/architecture divergence, not a rubber stamp.

## Honesty boundary

- Everything `no_alpha_claim`; the torch path proves the harness trains for real, not that
  the model has alpha.
- Deferred (later H slices): JAX/TensorFlow real backends, GPU/larger models, native
  architectures (LSTM/transformer), live UI, production Tier3.
- Reproduction: install CPU torch as above, run the lane + mutations, then `uv sync` to
  restore the default env.
