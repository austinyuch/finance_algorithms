# Tasks

Lane classification: CR overlay against completed F visual/public-demo baseline.

- [x] 1. Pixel-backed browser visual gate [Implements REQ-FBP-001]
  - [x] 1.1 RED: add focused frontend unit/PBT tests for pixel mismatch ratio, threshold status, and dimension mismatch.
  - [x] 1.2 GREEN: implement pure pixel mismatch helper and wire `browser-visual-smoke.mjs` to a committed PNG baseline.
  - [x] 1.3 REFACTOR: keep JSON evidence construction separate from PNG decoding and rerun focused tests.
  - _Eval: `cd frontend && npm test -- --run tests/public-demo.test.tsx && npm run visual && npm run visual:browser`._

- [x] 2. Mutation, coverage, and smoke hardening [Implements REQ-FBP-001]
  - [x] 2.1 Update frontend mutation checks so a threshold bypass or ratio inversion is killed.
  - [x] 2.2 Run frontend coverage, mutation, build, and production smoke.
  - _Eval: `cd frontend && npm run coverage && npm run mutation && npm run build && npm run smoke`._

- [x] 3. Governance and stakeholder closeout [Implements REQ-FBP-002]
  - [x] 3.1 Refresh `quantlab/TESTS.md`, `.agents/specs/TESTS.md`, `SPECS.md`, `NEXT_STEPS.md`, and stakeholder docs to remove the stale hash-equality residual where evidence supports it.
  - [x] 3.2 Write implementation report and review with conservative residuals.
  - _Eval: `rg -n "hash-equality" .agents/specs docs frontend quantlab/TESTS.md` should only return historical source refs if any._
