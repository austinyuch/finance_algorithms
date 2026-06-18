# Tasks — H Interactive Research UI (slice H-3)

> SDD Phase 3. Requirements: [requirements.md](./requirements.md). Design:
> [design.md](./design.md).

## Task Matrix

### H3-1 — Contract and Payload Validation

- [x] **RED:** Add failing Python and TypeScript tests for the new
  `interactiveResearch` dashboard block: claim boundary, OOS-net authority, baseline
  visibility, approximate-data warning, checksum shape, and stale/malformed payload
  rejection.
- [x] **GREEN:** Extend the showcase payload contract and canonical scenario with a
  deterministic H replay payload that satisfies the schema.
- [x] **REFACTOR:** Keep validation helpers small and shared; avoid duplicating H report
  calculations in frontend code.
- [x] **Evidence:** `uv run pytest -q tests/quantlab/test_h3_interactive_showcase.py`;
  `cd frontend && npm test -- --run tests/dashboard.test.tsx`.

### H3-2 — Parameter Workflow and Replay Selection

- [x] **RED:** Add failing unit/PBT tests for valid ranges, invalid parameters, unsupported
  but valid replay combinations, checksum mismatch, and absent-torch fallback rendering.
- [x] **GREEN:** Implement pure validation/selection helpers in
  `frontend/lib/interactive-research.ts`.
- [x] **REFACTOR:** Separate public static replay selection from future live execution
  seams; keep function names domain-oriented.
- [x] **Evidence:** `cd frontend && npm test -- --run tests/interactive-research.test.ts`.

### H3-3 — Interactive Dashboard UI

- [x] **RED:** Add failing render tests that require `data-section="interactive-research"`,
  controls for backend/hidden/lookback/epochs/seed/rebalance/artifact, `no_alpha_claim`,
  static replay mode, fallback reason, and approximate warning.
- [x] **GREEN:** Add `InteractiveResearchPanel` and integrate it into `Dashboard`.
- [x] **REFACTOR:** Align with existing dashboard styling; stabilize layout dimensions for
  controls/charts.
- [x] **Evidence:** `cd frontend && npm test -- --run tests/dashboard.test.tsx
  tests/interactive-research.test.ts`.

### H3-4 — Static Export, API, Smoke, and Public Honesty

- [x] **RED:** Add failing tests/smoke assertions that the API and static HTML expose the
  H-3 section and that public proof remains non-proven unless live probe hashes match.
- [x] **GREEN:** Update public-demo section manifests, smoke assertions, and export output.
- [x] **REFACTOR:** Keep live-hosting proof logic unchanged except for the new data hash.
- [x] **Evidence:** `cd frontend && npm run visual`; `cd frontend && npm run build`;
  `cd frontend && npm run smoke`.

### H3-5 — Visual Regression and Browser Evidence

- [x] **RED:** Observe browser visual failure after HTML changes.
- [x] **GREEN:** Re-pin the committed static visual contract and browser screenshot
  evidence after verifying the rendered UI is nonblank and sections are visible.
- [x] **REFACTOR:** Update docs/review/manual visual artifacts only through the existing
  scripts.
- [x] **Evidence:** `cd frontend && npm run visual && QUANTLAB_BROWSER_VISUAL_UPDATE_DOCS=1
  npm run visual:browser`; rerun `cd frontend && npm run visual:browser` without update
  mode; `cd frontend && npm run e2e:interactive` for the real-browser fail-closed
  parameter workflow and VRT baseline.

### H3-6 — Mutation and Negative Evidence

- [x] **RED:** Add or extend frontend mutation probes for H-3 no-alpha/approximate warning
  gates and confirm the mutants are killed.
- [x] **GREEN:** Update the mutation runner and tests.
- [x] **REFACTOR:** Keep default mutation counts consistent with governance artifacts.
- [x] **Evidence:** `cd frontend && npm run mutation`.

### H3-7 — Governance, Review, and Local-First Closeout

- [x] Refresh `quantlab/TESTS.md`, `.agents/specs/SPECS.md`, `RTM.md`, `ISSUE_LOG.md`,
  `NEXT_STEPS.md`, `docs/FEATURES.md`, and generated docs/proof surfaces affected by the
  new payload hash.
- [x] Create `review.md` with readiness capped to repo-side/local demo unless a fresh live
  public probe proves the new deployed hash.
- [x] Run the local-first matrix or record explicit hosted-only gaps.
- [x] **Evidence:** `uv run pytest -q`; `uv run mypy quantlab/ --ignore-missing-imports`;
  `uv run lint-imports`; `git diff --check`; frontend test/coverage/build/smoke/visual/
  mutation gates.

## FMEA Trace

| Risk | Tasks |
|---|---|
| FMEA-H3-01 public live overclaim | H3-3, H3-4, H3-7 |
| FMEA-H3-02 duplicate TS calculation | H3-1, H3-2 |
| FMEA-H3-03 alpha wording leakage | H3-1, H3-3, H3-6 |
| FMEA-H3-04 approximate data hidden | H3-1, H3-3, H3-4, H3-6 |
| FMEA-H3-05 stale checksum | H3-1, H3-2 |
| FMEA-H3-06 backend fallback overclaim | H3-2, H3-3 |
| FMEA-H3-07 stale visual baseline | H3-5, H3-7 |

## Completion Rule

The slice is not review-ready until all RED/GREEN/REFACTOR tasks are closed, the
local-first evidence matrix has run, and public-hosting status is either freshly
`proven` for the new data hash or explicitly documented as non-proven pending deploy.
