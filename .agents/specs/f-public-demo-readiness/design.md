# Design — F Public Demo Readiness

## Classification

CR/continuation against completed F demo hardening.

## Design

- Use npm `overrides.postcss=^8.5.10` to remediate the transitive PostCSS advisory without accepting npm audit's unsafe Next major downgrade recommendation.
- Add `npm run smoke` backed by `scripts/public-demo-smoke.mjs`.
- Keep dashboard contract literals conservative for hosting and visual evidence.

## FMEA

| Risk ID | Failure Mode | Effect | Control |
|---|---|---|---|
| FPUB-FM-01 | Clean local audit is described as public deployment | Overclaim | Contract keeps `publicHosting=not_proven` |
| FPUB-FM-02 | Smoke checks only HTML and misses API payload | False green | Smoke validates `/` and `/api/showcase` |
| FPUB-FM-03 | Dependency advisory reappears silently | Demo hygiene regression | Frontend test and mutation guard `dependencyAudit=clean` |
