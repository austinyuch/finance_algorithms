# Tasks — B Scheduled Run Observer

Lane classification: `new spec` for the B scheduled ops residual.

- [x] 1. TDD observer classification [Implements REQ-BSRO-001, REQ-BSRO-002]
  - [x] 1.1 RED: add manual-only pending and schedule-success tests.
    - _Eval: `uv run pytest -q tests/test_daily_snapshot.py -k scheduled_run_observer` fails before implementation._
  - [x] 1.2 GREEN: implement `scripts/scheduled_run_observer.py`.
    - _Eval: targeted observer tests pass._
  - [x] 1.3 REFACTOR: keep live GitHub access outside pure classification for deterministic tests.
    - _Eval: CLI accepts `--runs-json`._

- [x] 2. Mutation proof [Implements REQ-BSRO-003]
  - [x] 2.1 Add `b-scheduled-observer-manual-pending` mutation.
    - _Eval: mutation list smoke includes the new mutation._
  - [x] 2.2 Kill the targeted mutation.
    - _Eval: `uv run python scripts/run_mutation_spot_checks.py --only b-scheduled-observer-manual-pending`._

- [x] 3. Live observation and governance closeout [Implements REQ-BSRO-001, REQ-BSRO-002]
  - [x] 3.1 Run live `gh run list` observation through `--runs-json`.
    - _Eval: original artifact emitted `status=pending`, `schedule_run_count=0`, latest manual success `27387041974`; refreshed live artifact emits `status=proven`, `schedule_run_count=1`, latest schedule success `27392471359`._
  - [x] 3.2 Update test/spec/docs registries.
  - [x] 3.3 Run final verification.
