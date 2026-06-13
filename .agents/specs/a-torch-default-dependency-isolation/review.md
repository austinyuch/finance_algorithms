# Review

## Verdict

**Review PASSED for repo-side default dependency isolation.**

The default UAT/runtime dependency graph no longer carries Torch. The optional
PyTorch LSTM strategy remains available only through the dedicated PyTorch lane.

## Scores

| Dimension | Score |
|---|---:|
| Requirements fit | 9.3 |
| Design consistency | 9.1 |
| Code quality | 9.0 |
| Test/evidence quality | 9.2 |
| Overall | 9.15 |

## Requirement Acceptance

- `REQ-ATORCH-001`: **Accepted.** Root `pyproject.toml` and `uv.lock` no longer
  include Torch, and `root-torch-default-dependency` mutation is killed.
- `REQ-ATORCH-002`: **Accepted.** The TSMC hedge script runs without Torch and
  labels the missing PyTorch lane explicitly; LSTM tests skip with an explicit
  optional-lane reason in the default env.

## Security-Review Summary

- Changed trust boundary: dependency supply chain / default runtime artifact.
- Main attack path considered: unpatched optional ML framework ships in the
  default lock even though it is not needed for UAT smoke paths.
- Confirmed issue addressed: root dependency reachability to unpatched `torch`
  advisory #7.
- External security state verified after merge: Dependabot alert #7 fixed on
  GitHub (`fixed_at=2026-06-12T01:19:57Z`).
- Acceptable with rationale: optional `quantlab/envs/pytorch.txt` still permits
  PyTorch research work outside the default runtime; this is explicitly isolated.

## Verification Coverage

- `uv sync` removed Torch/CUDA transitive dependencies.
- `uv run pytest -q` -> 288 passed.
- `uv run mypy quantlab/ scripts/build_showcase_payload.py scripts/run_tsmc_hedge_slice.py scripts/run_vintage_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py scripts/source_quorum_proof.py scripts/stooq_contract_proof.py --ignore-missing-imports`
  -> clean over 58 files.
- `uv run lint-imports` -> KEPT.
- `uv run python scripts/run_mutation_spot_checks.py --only root-torch-default-dependency`
  -> KILLED.
- `uv run python scripts/run_tsmc_hedge_slice.py` -> non-LSTM leaderboard with
  explicit PyTorch-lane skip notice.

## Live-Demo Readiness

**CONDITIONAL / hybrid.** The default CLI smoke path is real and no longer
requires Torch. The showcase dashboard now uses the CR-FPS-006 generated
canonical local result-store payload (`local_result_store`) and keeps
`local_demo_only` labels, so this lane does not upgrade the dashboard to live
backend/live market-data readiness.

## Residual Risk

- Dependabot alert #7 fixed on the default branch after GitHub rescan; future
  dependency work should continue to keep Torch out of the default runtime lock.
- LSTM-specific proof is no longer part of the default root test pass; it belongs
  to the optional PyTorch lane.
- Autonomous cron `event=schedule` proof remains a separate B-lane residual.
