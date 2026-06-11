# Tasks — D Return/Risk Forecast Model

References: [requirements.md](./requirements.md), [design.md](./design.md).

- [x] 1. RED: add D2 forecast, allocation, PBT, integration, smoke, and coverage tests
  - [x] 1.1 Add `tests/quantlab/test_d_4_return_risk_forecast.py` before implementation.
    - _Requirements: [REQ-D-FORECAST-001], [REQ-D-ALLOC-001], [REQ-D-BENCH-001]_
    - _Eval: targeted pytest fails before implementation._

- [x] 2. GREEN: implement deterministic return/risk model slice
  - [x] 2.1 Add `quantlab/models/return_risk.py` and export it from `quantlab.models`.
    - _Requirements: [REQ-D-FORECAST-001], [REQ-D-ALLOC-001], [REQ-D-BENCH-001]_
    - _Eval: `uv run pytest -q tests/quantlab/test_d_4_return_risk_forecast.py`._

- [x] 3. REFACTOR: clarify status/fallback and benchmark helpers
  - [x] 3.1 Refactor forecast validation and strategy metadata without behavior drift.
    - _Requirements: [REQ-D-FORECAST-001], [REQ-D-ALLOC-001]_
    - _Eval: targeted tests remain green._

- [x] 4. Quality gates
  - [x] 4.1 Run D2 line coverage.
    - _Eval: `uv run pytest --cov=quantlab.models.return_risk --cov-report=term-missing tests/quantlab/test_d_4_return_risk_forecast.py` >= 80%._
  - [x] 4.2 Extend mutation spot checks for D2 fallback/claim behavior.
    - _Eval: mutation check killed._
  - [x] 4.3 Run integration and smoke tests through the A0 result store.

- [x] 5. Review and governance closeout
  - [x] 5.1 Refresh `quantlab/TESTS.md`, `.agents/specs/TESTS.md`, `SPECS.md`, and `NEXT_STEPS.md`.
  - [x] 5.2 Create `review.md` with no-alpha claim and Tier3 deferral preserved.
