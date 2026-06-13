# Design — F Demo Hardening

References: [requirements.md](./requirements.md), [../f-nextjs-showcase-dashboard/review.md](../f-nextjs-showcase-dashboard/review.md).

## Overview

Extend the existing `ShowcaseDashboard` contract with `demoReadiness`. The field is intentionally conservative and local-runtime scoped.

## Architecture

```mermaid
flowchart LR
  Payload[canonical local result-store payload] --> Validator[assertDashboardPayload]
  Validator --> API[/api/showcase]
  Validator --> UI[Dashboard Evidence Panel]
  Mutation[frontend mutation script] --> Validator
```

## Test Coverage Declaration

- Unit/API/component: `frontend/tests/dashboard.test.tsx`.
- PBT: existing leaderboard sort property remains.
- Mutation: `frontend-public-hosting-overclaim` must be killed.
- Integration/smoke: Next build plus local HTTP smoke.
- Line coverage: frontend coverage must remain >=80%.

## FMEA

| Risk ID | Failure Mode | Effect | Control | Response | Task Trace |
|---|---|---|---|---|---|
| FMEA-F-DEMO-01 | Local demo described as public deployment | False readiness | explicit `not_proven` fields | contract rejection + UI rendering | F-1/F-3 |
| FMEA-F-DEMO-02 | Visual regression implied without browser visual evidence | Misleading review artifact | evidence-backed `visualRegression=proven` only after passed browser visual diff | negative test + underclaim mutation | F-1 / CR-FPS-009 |
| FMEA-F-DEMO-03 | Dependency audit hidden | public demo risk lost | rendered dependency audit status | review caveat | F-4 |

## EDD

- `cd frontend && npm test -- --run tests/dashboard.test.tsx`
- `cd frontend && npm run coverage`
- `cd frontend && npm run mutation`
- `cd frontend && npm run build`
- local HTTP smoke for `/` and `/api/showcase`

## Traceability References

- `REQ-F-DEMO-001` -> canonical payload/API/component render tests.
- `REQ-F-DEMO-002` -> validator negative tests and frontend mutation.
