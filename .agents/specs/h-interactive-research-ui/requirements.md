# Requirements — H Interactive Research UI (slice H-3)

> SDD Phase 1 draft. Spec: `h-interactive-research-ui`.
> Upstream: h-deep-learning-research-lab (H-1), h-deep-learning-real-training
> (H-2), f-public-static-showcase, f-showcase-read-api-dashboard,
> e-mlops-tier3-lite, real-data-oos-backtest.

## 0. Governance

- **Work classification:** `new spec` (new Epic H user-facing capability slice).
  Resolved via spec-master: H-1 and H-2 are completed baselines that explicitly
  deferred live interactive UI; F owns static/public hosting mechanics, and E owns
  Tier3 proof gates. This slice composes those completed capabilities without
  changing their closed behavior.
- **Depends On:** h-deep-learning-research-lab (reference forecaster, report/viz,
  parameterized experiment CLI, ExperimentRegistry lineage), h-deep-learning-real-training
  (optional PyTorch backend and honest fallback), f-showcase-read-api-dashboard
  (read surface and dashboard patterns), f-public-static-showcase (public-hosting
  proof/freshness and browser visual gates), e-mlops-tier3-lite (registry lineage),
  real-data-oos-backtest (OOS-net and fail-closed comparison discipline).
- **Impacts:** expected future work under `frontend/`, `quantlab/showcase/`, and
  `scripts/` only. No change to `quantlab.engine` / `quantlab.data` framework
  isolation, no change to legacy `invest_algorithms/`, and no production Tier3
  readiness claim.
- **First-slice boundary:** deliver a local/repo-side interactive research UI for
  tuning Epic H experiment parameters, running or selecting deterministic
  experiment artifacts, displaying OOS-net/statistical evidence with lineage, and
  preserving the static public-demo honesty contract. Public Pages deployment is a
  point-in-time proof step, not a precondition for repo-side requirements approval.
- **Explicitly deferred (later slices, not this one):** JAX/TF real training
  backends, GPU/larger/native architectures, production serving/retraining/drift,
  user accounts, shared experiment storage, and any live trading/investment
  recommendation workflow.
- **Honesty posture:** every UI result remains `no_alpha_claim`, ranks on
  out-of-sample net metrics only, keeps baselines visible, distinguishes approximate
  CR-B21 research data from strict PIT data, and fails closed rather than rendering
  stale/proven-looking evidence.

## 1. Dependencies, Impacts & CRs

- [Depends On: h-deep-learning-research-lab, h-deep-learning-real-training, f-showcase-read-api-dashboard, f-public-static-showcase, e-mlops-tier3-lite, real-data-oos-backtest]
- [Impacts: none] — this slice composes completed H/F/E/RDO surfaces through a new
  UI/read boundary and must not rewrite their completed-baseline behavior.
- [Open Change Requests: none] — no completed spec contract is changed at
  requirements time. If design later requires changing H report schema, F public
  manifest semantics, or E registry contracts, that change must be split into the
  appropriate CR before implementation.

## 2. Repo-side Closure vs External Execution

- **Repo-side Closure:** requirements, design, tests, local UI/API execution,
  deterministic artifact generation, registry lineage assertions, unit/PBT/
  integration/e2e/smoke/visual coverage, and static export evidence are provable
  in this repo. Port-bound local services, if needed for evidence, must go through
  `local-infra-registry-governance` or the repo's governed dynamic-port smoke
  helpers.
- **External Execution:** GitHub Pages deployment and live public probe refresh are
  external proof steps after a `main` deploy. They can prove public parity but must
  not be used as the only evidence for repo-side UI correctness.
- **External Blockers / Constraints:** optional PyTorch evidence remains optional
  and default-skipped; the default root environment must not re-add torch. Any
  production Tier3 readiness remains governed by existing E proof validators and is
  outside this slice.

## 3. Functional Requirements

### Requirement 1 [REQ-H3-PARAM-001]

**User story:** As a QuantLab researcher, I want interactive controls for Epic H
experiment parameters, so that I can explore model and backtest settings without
editing command-line arguments by hand.

#### Acceptance Criteria

1. When the UI loads, it shall expose controls for at least backend, hidden units,
   lookback, epochs, seed, rebalance cadence, and output/artifact selection while
   showing the resolved default values from the existing H experiment contract.
2. When a parameter is invalid or outside the supported research range, the UI shall
   fail closed with an actionable validation state and shall not start an experiment.
3. When `backend="pytorch"` is selected in an environment without torch, the UI shall
   surface the same honest `reference` fallback reason as the H backend registry
   rather than implying a PyTorch run occurred.

### Requirement 2 [REQ-H3-EXEC-001]

**User story:** As a researcher, I want the UI to run or select deterministic Epic H
experiment artifacts, so that the visible result is traceable to the same lineage as
the CLI.

#### Acceptance Criteria

1. When a valid parameter set is submitted, the repo-side execution path shall call
   the existing H experiment/report/registry surfaces or a thin wrapper around them,
   not a duplicate calculation path.
2. When an experiment succeeds, the returned payload shall include the deterministic
   experiment id, report checksum, input parameters, data window, backend/fallback
   status, and artifact paths needed to reproduce the run.
3. If data is insufficient, stale, non-finite, or otherwise unsafe, the execution
   path shall return a fail-closed status (`insufficient_data` or equivalent) and
   the UI shall render that state without producing leaderboard or chart claims.

### Requirement 3 [REQ-H3-EVIDENCE-001]

**User story:** As a research reviewer, I want every interactive result to preserve
OOS-net, baseline, data-lineage, and claim-boundary evidence, so that the UI remains
honest under rapid parameter exploration.

#### Acceptance Criteria

1. Every result view shall display `claim_boundary="no_alpha_claim"` and shall avoid
   strategy recommendation, alpha, or production-readiness wording.
2. Leaderboards shall rank only on out-of-sample net metrics and shall keep the dumb
   baseline visible.
3. Results using CR-B21 approximate backfill data shall visibly state that the data is
   research-mode approximate availability, strict-PIT excluded, and not a strategy
   verdict.
4. The UI shall show the source artifact timestamp/checksum and shall fail closed if
   the displayed artifact no longer matches the expected checksum.

### Requirement 4 [REQ-H3-VISUAL-001]

**User story:** As a stakeholder, I want interactive visualizations for the H report,
so that parameter changes are legible without losing the self-contained evidence
discipline from H-1 and F.

#### Acceptance Criteria

1. The result view shall show at least OOS-net leaderboard, equity or relative
   performance, drawdown, return distribution, and learning-curve panels using the
   existing H report fields.
2. When no successful result exists, charts shall render an explicit empty/fail-closed
   state rather than placeholder performance.
3. Browser visual evidence shall cover the loaded state, successful result state, and
   fail-closed/insufficient-data state with a stable pixel or screenshot contract.

### Requirement 5 [REQ-H3-TEST-001]

**User story:** As a maintainer, I want the interactive UI covered by local-first tests,
so that hosted GitHub Actions are confirmation rather than the primary CI queue.

#### Acceptance Criteria

1. The slice shall define unit tests for parameter validation and payload mapping,
   PBT coverage for supported parameter ranges, integration tests for the H execution
   wrapper, e2e/smoke coverage for the UI flow, and browser visual regression for the
   core states.
2. Tests shall include stale artifact/checksum mismatch, insufficient data, optional
   torch fallback, and no-alpha overclaim negative cases.
3. Folder-level `quantlab/TESTS.md` and the workspace test rollup shall be refreshed
   before review if new tests or evidence rows are added.

### Requirement 6 [REQ-H3-PUBLIC-001]

**User story:** As a portfolio viewer, I want the public static/demo surface to stay
truthful after the interactive UI is added, so that a deployed demo never overclaims
live execution or production readiness.

#### Acceptance Criteria

1. If the public demo exports any H interactive artifact, the export shall make clear
   whether it is a static replay, local demo, or live local execution path.
2. Public-hosting proof shall remain `proven` only after a fresh live probe observes
   matching deployed manifest/data hashes; otherwise it shall downgrade to
   `configured_not_observed` or an equivalent non-proven status.
3. The dashboard/public UI shall continue to report production Tier3 as not ready
   unless the existing E production proof CLI accepts real external proof payloads.

## 4. Out of Scope

- JAX/TensorFlow real-training implementation, GPU acceleration, larger/native neural
  architectures, or any performance target.
- Production serving, production retraining orchestration, production automated drift
  monitoring, or user/account management.
- Hosted-only evidence as the primary correctness proof.
- Any alpha claim, investment advice, strategy recommendation, or live-trading workflow.
