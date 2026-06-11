# Requirements — F Public Demo Readiness

## Boundary

Improve the local production-demo path and dependency hygiene while keeping actual public hosting and visual regression marked `not_proven` until external evidence exists.

#### AC-FPUB-01 — Dependency Hygiene
1. Frontend dependency audit must report zero vulnerabilities.
2. Dashboard readiness payload must expose `dependencyAudit=clean`.
3. Tests must reject dependency-audit regressions.

#### AC-FPUB-02 — Production Smoke
1. A repeatable script starts the built Next.js app and checks `/`.
2. The script checks `/api/showcase` and validates conservative readiness fields.
3. Smoke evidence must not claim public hosting without deployed URL evidence.

#### AC-FPUB-03 — Readiness Honesty
1. `publicHosting` remains `not_proven`.
2. `visualRegression` remains `not_proven`.
3. `claim` remains `local_demo_only`.
