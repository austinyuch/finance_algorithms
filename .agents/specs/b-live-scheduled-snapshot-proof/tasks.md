# Tasks

Lane classification: CR overlay against completed B scheduled ops proof.

- [x] 1. Fix Actions timestamp proof [Implements REQ-BLSP-001]
  - [x] 1.1 RED: add workflow guard rejecting `github.run_started_at`.
  - [x] 1.2 GREEN: generate timestamps in the runner shell and upload artifacts with `if: always()`.
  - [x] 1.3 REFACTOR: keep schedule proof command readable and rerun targeted tests.
  - _Eval: `uv run pytest -q tests/test_daily_snapshot.py -k "workflow_records_report or schedule_run_proof"`._

- [ ] 2. Capture external workflow evidence [Implements REQ-BLSP-001, REQ-BLSP-002]
  - [ ] 2.1 Push branch and dispatch `daily-snapshot.yml`.
  - [ ] 2.2 Inspect run conclusion and download `snapshot-schedule-proof` artifact.
  - [ ] 2.3 Record run metadata and artifact contents without overclaiming cron proof.
  - _Eval: `gh run view <run> --json ...` plus artifact JSON readback._

- [ ] 3. Governance closeout [Implements REQ-BLSP-002]
  - [ ] 3.1 Update `NEXT_STEPS.md`, `SPECS.md`, `TESTS.md`, `RTM.md`, and stakeholder docs if the external proof succeeds.
  - [ ] 3.2 Write implementation report and review.
  - _Eval: stale scheduled-run residual should only remain for missing autonomous cron proof._
