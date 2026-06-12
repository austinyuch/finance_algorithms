# Design — E Tier3 Readiness Proof CLI

## Overview

`scripts/tier3_readiness_gate.py` is a strict operational wrapper around the existing E production validators. It accepts four JSON inputs:

- Tier3 manifest
- production serving evidence
- production retraining evidence
- production automated drift monitoring evidence

The CLI validates every input and only then calls `build_tier3_readiness_gate`.

## Test Coverage Declaration

- Unit/smoke tests exercise successful file-to-file gate generation.
- Negative tests exercise local-smoke evidence rejection and invalid JSON chaos behavior.
- Mutation tests cover validator bypass risk.

## Repo-side Closure vs External Execution Boundary

- Repo-side closure: CLI, deterministic output, fail-closed validation, tests, mutation target, governance.
- External execution: real production services/jobs/monitors producing proof JSON.
- Residual: no external production proof exists in this repo yet.

## Components

| Component | Responsibility |
|---|---|
| `_read_json` | Load JSON from a path and reject invalid or non-object payloads. |
| `build_gate_from_files` | Validate manifest and three production evidence artifacts, then build a gate artifact. |
| `main` | CLI argument parsing, stdout/file output, and fail-closed nonzero error handling. |

## Failure Mode and Effects Analysis

| Risk ID | Failure Mode | Effect | Control | Task Trace |
|---|---|---|---|---|
| FMEA-E-CLI-001 | CLI accepts local-smoke evidence | Production false green | Always call production validators before gate creation | Task 1 |
| FMEA-E-CLI-002 | Invalid JSON leaves stale success artifact | Review consumes old green output | Read inputs first; write output only after full validation succeeds | Task 2 |
| FMEA-E-CLI-003 | CLI output omits claim boundary or evidence | Downstream docs overstate readiness | Use `build_tier3_readiness_gate` output directly | Task 3 |

## EDD

- `uv run pytest -q tests/test_tier3_readiness_gate_cli.py`
- `uv run python scripts/run_mutation_spot_checks.py --only e-tier3-cli-serving-validator`
- `uv run pytest -q`
- `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py --ignore-missing-imports`
- `uv run lint-imports`

## Traceability References

- `REQ-E-CLI-001` -> successful gate artifact generation.
- `REQ-E-CLI-002` -> local-smoke and malformed input rejection.
- `REQ-E-CLI-003` -> claim boundary and evidence preservation.
