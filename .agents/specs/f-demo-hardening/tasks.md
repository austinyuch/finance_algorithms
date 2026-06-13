# Tasks — F Demo Hardening

References: [requirements.md](./requirements.md), [design.md](./design.md).

Current dashboard payloads are generated from the CR-FPS-006 local result-store scenario, not from the retired inline fixture source.

- [x] 1. RED: demo readiness tests
  - [x] 1.1 Add dashboard/API/negative tests for public hosting and visual-regression overclaims.
    - _Requirements: [REQ-F-DEMO-001], [REQ-F-DEMO-002]_
    - _Eval: frontend tests fail before contract fields exist._

- [x] 2. GREEN: implement demo readiness contract
  - [x] 2.1 Extend `ShowcaseDashboard`, generated payload, and validator.
    - _Eval: frontend tests pass._

- [x] 3. REFACTOR: render evidence in dashboard
  - [x] 3.1 Add evidence-panel display for local-demo, public-hosting, and browser-visual readiness fields.
    - _Eval: frontend tests remain green._

- [x] 4. Quality gates
  - [x] 4.1 Run frontend coverage >=80%.
  - [x] 4.2 Extend and run frontend mutation checks.
  - [x] 4.3 Run build and local HTTP smoke.

- [x] 5. Review and governance closeout
  - [x] 5.1 Update test/spec registries and mirrors.
  - [x] 5.2 Create `review.md`.
