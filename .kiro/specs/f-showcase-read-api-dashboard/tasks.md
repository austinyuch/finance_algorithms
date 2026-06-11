# Tasks — F Showcase Read API Dashboard

References: [requirements.md](./requirements.md), [design.md](./design.md).

- [x] 1. RED: add showcase API, dashboard, PBT, integration, smoke, and coverage test obligations
  - [x] 1.1 Add `tests/quantlab/test_f_1_showcase_api.py` with failing tests for leaderboard/read-detail, conservative dashboard defaults, HTML smoke, and PBT ordering invariants.
    - _Requirements: [REQ-F-SHOWCASE-001], [REQ-F-SHOWCASE-002], [REQ-F-SHOWCASE-003]_
    - _Eval: targeted pytest fails before implementation._

- [x] 2. GREEN: implement read API and deterministic dashboard render
  - [x] 2.1 Add `quantlab/showcase/api.py` and `quantlab/showcase/html.py`.
    - _Requirements: [REQ-F-SHOWCASE-001], [REQ-F-SHOWCASE-002], [REQ-F-SHOWCASE-003]_
    - _Eval: `uv run pytest -q tests/quantlab/test_f_1_showcase_api.py`._

- [x] 3. REFACTOR: stabilize view-model names and remove duplication
  - [x] 3.1 Refactor without changing behavior; keep tests green and public output stable.
    - _Requirements: [REQ-F-SHOWCASE-001], [REQ-F-SHOWCASE-002], [REQ-F-SHOWCASE-003]_
    - _Eval: targeted tests remain green; HTML snapshot-relevant sections remain deterministic._

- [x] 4. Quality gates
  - [x] 4.1 Run line coverage for `quantlab.showcase`.
    - _Eval: `uv run pytest --cov=quantlab.showcase --cov-report=term-missing tests/quantlab/test_f_1_showcase_api.py` >= 80% line coverage._
  - [x] 4.2 Extend mutation spot checks for showcase claim-boundary/default behavior.
    - _Eval: mutation check killed._
  - [x] 4.3 Record integration and smoke evidence in `reports/implementation-report.md`.

- [x] 5. Review and governance closeout
  - [x] 5.1 Refresh `quantlab/TESTS.md`, `.agents/specs/TESTS.md`, `SPECS.md`, and `NEXT_STEPS.md` from test/report truth.
  - [x] 5.2 Create `review.md` with live-demo readiness capped to `CONDITIONAL` / `hybrid`.
