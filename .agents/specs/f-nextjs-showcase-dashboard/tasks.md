# Tasks — F Next.js Showcase Dashboard

References: [requirements.md](./requirements.md), [design.md](./design.md).

- [x] 1. RED: frontend contract/component/API tests
  - [x] 1.1 Add Vitest tests for dashboard render, API route payload, PBT leaderboard order, and claim-boundary preservation before implementation.
    - _Requirements: [REQ-FNX-DASH-001], [REQ-FNX-API-001]_
    - _Eval: `cd frontend && npm test -- --run` fails before source modules exist._

- [x] 2. GREEN: implement Next.js dashboard
  - [x] 2.1 Add Next.js app/page, route handler, typed contract, generated local `local_result_store` payload consumption, and dashboard component.
    - _Requirements: [REQ-FNX-DASH-001], [REQ-FNX-API-001]_
    - _Eval: frontend tests pass._

- [x] 3. REFACTOR: stabilize dashboard structure
  - [x] 3.1 Refactor duplicated formatting helpers and keep output sections stable.
    - _Requirements: [REQ-FNX-DASH-001]_
    - _Eval: frontend tests and coverage remain green._

- [x] 4. Quality gates
  - [x] 4.1 Run line coverage.
    - _Eval: `cd frontend && npm run coverage` >=80%._
  - [x] 4.2 Add and run frontend mutation check.
    - _Eval: mutation killed._
  - [x] 4.3 Run `npm run build` and local HTTP smoke with `next start`.
    - _Eval: `/` returns dashboard HTML with required sections._

- [x] 5. Review and governance closeout
  - [x] 5.1 Update `quantlab/TESTS.md`, `.agents/specs/TESTS.md`, `SPECS.md`, `NEXT_STEPS.md`, and mirrors.
  - [x] 5.2 Create `review.md` with live-demo readiness limited to local runtime proof.
