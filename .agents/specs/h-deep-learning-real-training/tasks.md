# Tasks — H Deep-Learning Real Training (slice H-2)

References: [requirements.md](./requirements.md), [design.md](./design.md).

> Lane: `spec/h-deep-learning-real-training` (own branch, off the post-H-1 dev baseline).
> Mirrors the branch-spec Repo-side / Torch-enabled boundary from requirements §2 and
> design §5 — it does not invent governance boundaries.

- [ ] 1. RED: add failing H-2 tests before implementation
  - [ ] 1.1 Add `tests/quantlab/test_h2_torch_training.py` (optional lane,
        `pytest.importorskip("torch")`): real torch training → finite forecasts;
        torch-vs-reference parity within `1e-3` **and** trained-not-noop
        (loss decreased, trace length == epochs); report shape/keys/OOS-net ranking /
        `no_alpha_claim` parity with the reference run; same-seed determinism of forecasts
        + loss trace; no lookahead vs reference.
    - _Requirements: [REQ-H2-TORCHTRAIN-001], [REQ-H2-PARITY-001], [REQ-H2-DETERMINISM-001]_
    - _Eval: in a torch-enabled venv the targeted file fails (trainer absent); in the default
      env it is skipped._
  - [ ] 1.2 Add default-env tests (no torch): `backend="pytorch"` + torch absent resolves to
        `reference`, trains, records fallback reason, never raises; importing
        `quantlab.models.dl_forecaster` does not import torch (lazy-import guard).
    - _Requirements: [REQ-H2-OPTLANE-001], [REQ-H2-ISOLATION-001]_
    - _Eval: `uv run pytest -q tests/quantlab/...` fails (dispatch/guard absent)._

- [ ] 2. GREEN: implement the real PyTorch training path
  - [ ] 2.1 Add `quantlab/models/dl/torch_trainer.py` — lazy `import torch`, float64, seeded,
        full-batch GD mirroring the reference MLP math; pure numerics, no engine/data import.
    - _Requirements: [REQ-H2-TORCHTRAIN-001], [REQ-H2-DETERMINISM-001], [REQ-H2-ISOLATION-001]_
    - _Eval: torch lane training/determinism tests pass in a torch-enabled venv._
  - [ ] 2.2 Wire additive backend dispatch in `quantlab/models/dl_forecaster.py`
        (`self.backend == "pytorch"` → delegate to `train_mlp_torch`; default `reference`
        path and all public shapes unchanged); preserve honest fallback when torch absent.
    - _Requirements: [REQ-H2-TORCHTRAIN-001], [REQ-H2-OPTLANE-001]_
    - _Eval: default-env fallback + lazy-import tests pass; torch lane parity test passes._

- [ ] 3. Quality gates
  - [ ] 3.1 Confirm torch stays out of the default root env (`uv sync` excludes torch;
        `test_dependency_security` green); confirm `uv run lint-imports` KEPT (new module under
        the existing "DL backend boundary" contract); `uv run mypy ... --ignore-missing-imports`
        clean.
    - _Requirements: [REQ-H2-ISOLATION-001], [REQ-H2-OPTLANE-001]_
    - _Eval: lint-imports KEPT; mypy clean; dependency-security green._
  - [ ] 3.2 Add mutation specs (parity trained-not-noop authority; `pytorch`-absent
        fallback→raise) to `scripts/run_mutation_spot_checks.py`; confirm KILLED in the
        torch-enabled UAT.
    - _Requirements: [REQ-H2-PARITY-001], [REQ-H2-OPTLANE-001]_
    - _Eval: `uv run python scripts/run_mutation_spot_checks.py --only <names>` KILLED._
  - [ ] 3.3 Default suite green with the torch lane **skipped**; torch-enabled capture run
        (training + parity + determinism + mutations) recorded as
        `reports/h2-torch-uat-capture.md`; touched-line coverage ≥85% (torch-enabled).
    - _Requirements: [REQ-H2-OPTLANE-001], [REQ-H2-PARITY-001]_
    - _Eval: `uv run pytest -q` green (lane skipped); UAT transcript captured._

- [ ] 4. Review and governance closeout
  - [ ] 4.1 Refresh folder-level test rows then hand the workspace `TESTS.md` rollup to
        `test-registry-manager`; resync the canonical no-skip pytest count (+N torch-lane
        tests) and mutation count across the count-bearing surfaces; update `SPECS.md`
        (new row, hand to `spec-registry-manager`), `NEXT_STEPS.md`, `RTM.md`.
    - _Requirements: all_
    - _Eval: governance guard tests pass; counts consistent cross-surface._
  - [ ] 4.2 Create `review.md` (verdict, scores, FMEA-H2 closure, residual: JAX/TF real
        backends + GPU + live UI deferred). Record an `ISSUE_LOG.md` audit row. Decide the
        dashboard-payload impact (likely none — no payload/evidence-list change unless the
        no-skip count is surfaced) and integrate the branch dev→main.
    - _Requirements: all_
    - _Eval: dev==main, working tree clean, no false-green._

## Notes

- This slice changes no completed-baseline behavior; H-1 stays immutable. The only edit to an
  existing file is the additive dispatch branch in `dl_forecaster.py` (§6 design).
- Per AGENTS.md, code touching `quantlab/models` runs `uv run pytest -q` + `uv run mypy` +
  `uv run lint-imports`; the torch lane additionally requires a torch-enabled capture.
