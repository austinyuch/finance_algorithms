# Design — Ops Visual Drift Artifacts

## Overview

This is a CR overlay against completed B/F/E/D baselines. It strengthens evidence surfaces without changing the core backtest engine, data loader semantics, or dashboard runtime claims.

## Architecture

- B scheduled ops proof extends `scripts/snapshot_schedule_report.py` with a proof object over existing report validation.
- F visual diff thresholding extends `frontend/lib/public-demo.ts` and `browser-visual-smoke.mjs`.
- E drift monitoring first slice extends `quantlab/mlops/experiment_registry.py`.
- B source-contract restoration evidence extends `quantlab/data/source_health.py`.
- D evaluation artifacts extend `quantlab/models/evaluation.py`.

## Test Coverage Declaration

- Python unit + PBT: `tests/test_daily_snapshot.py`, `tests/quantlab/test_e_1_experiment_registry.py`, `tests/quantlab/test_d_6_model_family_evaluation.py`.
- Frontend unit + PBT: `frontend/tests/public-demo.test.tsx`.
- Mutation: `scripts/run_mutation_spot_checks.py` and `frontend/scripts/run-mutation-checks.mjs`.
- Integration/smoke: scheduled report CLI smoke, frontend visual/browser visual/probe/smoke, full `uv run pytest -q`.

## Repo-side Closure vs External Execution Boundary

- Repo-side complete when deterministic proof builders, validators, scripts, tests, mutation checks, and governance docs are green.
- External execution remains the future scheduled GitHub Actions run and any live Stooq reopen probe after merge.

## Contracts

No generated contract is introduced. The local contract surface is structured JSON artifacts:

- `snapshot_schedule_run_proof`
- `browser_visual_diff`
- `drift_assessment_report`
- `source_contract_reopen_evidence`
- `model_family_evaluation_artifact`

## Components

- `scripts.snapshot_schedule_report.build_schedule_run_proof`: validates schedule report and records trigger/command/exit status.
- `frontend/lib/public-demo.buildBrowserVisualDiffEvidence`: validates hash evidence and threshold pass/fail.
- `quantlab.mlops.build_drift_assessment_report`: compares metrics and preserves non-serving boundary.
- `quantlab.data.source_health.build_source_contract_reopen_evidence`: normalizes live close-row proof.
- `quantlab.models.evaluation.build_model_family_evaluation_artifact`: writes deterministic D report artifacts.

## FMEA

| Risk ID | Failure Mode | Effect | Current Control | Planned Response | Task Trace |
|---|---|---|---|---|---|
| FMEA-OVD-1 | Scheduled config described as executed | false ops readiness | report-only gates | proof status separates smoke/live/degraded | Task 1 |
| FMEA-OVD-2 | Screenshot hash mistaken for visual diff | weak visual regression claim | browser hash evidence | threshold diff artifact with failure path | Task 2 |
| FMEA-OVD-3 | Drift report implies serving/retraining | Tier3 overclaim | manifest non-serving validation | assessed-not-automated status | Task 3 |
| FMEA-OVD-4 | Stooq re-enabled by status alone | broken daily source defaults | blocked/default-disabled gate | require live close rows and opt-in review | Task 4 |
| FMEA-OVD-5 | D evaluation artifact drifts from report | dashboard/history stale evidence | in-memory evaluator | checksumed artifact validation | Task 5 |

## Risk Response and Mitigation

- Prevent: reject overclaimed statuses and malformed evidence in validators.
- Detect: PBT for thresholds/counts/order and mutation checks for gates.
- Contain: external/live readiness remains downgraded unless evidence is produced.

## Error Handling

All validators raise `ValueError` on malformed artifacts or overclaim attempts. CLI smoke commands exit nonzero on failed validation.

## EDD

- RED tests must fail before implementation.
- GREEN tests must pass after minimal implementation.
- REFACTOR keeps existing helper boundaries and avoids duplicate validation logic.
- Full closeout gates include Python, mypy, import-linter, frontend coverage/build/visual/browser/probe/smoke/audit, and mutation checks.

## Traceability References

- `REQ-OVD-B-SCHEDULE` → `scripts/snapshot_schedule_report.py`, `tests/test_daily_snapshot.py`
- `REQ-OVD-F-VISUAL-DIFF` → `frontend/lib/public-demo.ts`, `frontend/tests/public-demo.test.tsx`
- `REQ-OVD-E-DRIFT` → `quantlab/mlops/experiment_registry.py`, `tests/quantlab/test_e_1_experiment_registry.py`
- `REQ-OVD-B-SOURCE` → `quantlab/data/source_health.py`, `tests/test_daily_snapshot.py`
- `REQ-OVD-D-ARTIFACTS` → `quantlab/models/evaluation.py`, `tests/quantlab/test_d_6_model_family_evaluation.py`
