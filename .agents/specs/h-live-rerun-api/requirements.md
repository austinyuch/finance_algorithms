# Requirements — H Live Backend Rerun API (slice H-4)

> SDD Phase 1 draft. Spec: `h-live-rerun-api`.
> Upstream: h-interactive-research-ui (H-3, static-replay UI), h-deep-learning-research-lab
> (H-1 experiment CLI / report / registry), h-deep-learning-real-training (H-2 optional
> torch backend), f-showcase-read-api-dashboard, f-public-static-showcase, e-mlops-tier3-lite,
> real-data-oos-backtest.

## 0. Governance

- **Work classification:** `continue active spec` — the next Epic H slice. H-3
  (`h-interactive-research-ui`) is **Implemented · Review PASSED** as *static replay only*
  and explicitly deferred "live backend rerun API" to a later slice. This slice delivers
  exactly that deferred capability. It is authored as a new spec dir with an explicit
  `[Impacts: h-interactive-research-ui]` overlay rather than editing the completed H-3 baseline.
- **Depends On:** h-interactive-research-ui (UI shell, parameter contract, fail-closed
  selection), h-deep-learning-research-lab (`scripts/run_dl_experiment.py`, report/viz,
  `ExperimentRegistry` lineage, deterministic `experiment_id`), h-deep-learning-real-training
  (optional torch backend + honest reference fallback), f-public-static-showcase (public
  hosting proof/freshness contract), e-mlops-tier3-lite (registry lineage), real-data-oos-backtest
  (OOS-net + fail-closed discipline).
- **Impacts:**
  - `[Impacts: h-interactive-research-ui]` — upgrades its `interactiveResearch.mode` from
    `static_replay` to support a live `compute` path **additively**; the static-replay
    fail-closed contract must remain intact as the fallback, not be removed.
  - `[Impacts: b-data-platform]` — requires a **public** PIT-provider accessor to replace the
    `provider._prices` private-attribute access used by research/scripts (see REQ-H4-007);
    this is an additive read API on the provider, no behavior change. Split into a
    `b-data-platform` CR if design shows the provider contract must change.
- **Open Change Requests:** none at requirements time. If design requires changing the H
  report schema, the F public manifest semantics, or the E registry contract, that change
  must be split into the appropriate CR before implementation.
- **First-slice boundary:** a **local/repo-side** backend rerun API that recomputes an Epic H
  experiment from user-selected parameters through the existing deterministic pipeline,
  returns a checksummed artifact + OOS-net rows + lineage, and drives the H-3 UI live —
  **with a real-backend smoke path** that fails closed against a stubbed backend. Public Pages
  deployment stays static-export only and is a separate point-in-time proof, not a precondition.
- **Explicitly deferred (later slices / Lane 2, NOT this one):** JAX/TF real training, GPU/native
  models, production serving/retraining/drift (Tier3), user accounts, shared/persistent
  multi-user experiment storage, and — critically — **any actionable "what to allocate now" /
  current-asof investment-recommendation surface**. That surface would cross the
  `Key Locked Decisions` (`成功=方法論誠實度…非 alpha`) and is the deferred, charter-gated
  Lane 2; it must not be introduced here.
- **Honesty posture:** every rerun result is `no_alpha_claim`, ranks on OOS-net only, keeps the
  dumb baseline visible, distinguishes approximate CR-B21 research data from strict PIT, and
  fails closed (never renders stale/proven-looking or fabricated evidence). The dashboard
  self-claim stays `not_proven` by the static-artifact contract.

## 1. Dependencies, Impacts & CRs

- [Depends On: h-interactive-research-ui, h-deep-learning-research-lab, h-deep-learning-real-training, f-public-static-showcase, e-mlops-tier3-lite, real-data-oos-backtest]
- [Impacts: h-interactive-research-ui, b-data-platform]
- [Open Change Requests: none]

## 2. Repo-side Closure vs External Execution

- **Repo-side Closure:** the rerun API, its parameter validation, deterministic recompute,
  artifact/lineage assertions, and unit/PBT/integration/e2e/smoke/VRT coverage — including a
  **real-backend smoke path** — are all provable in this repo. Any port-bound local service
  needed for evidence must go through `local-infra-registry-governance` or the repo's governed
  dynamic-port smoke helpers (mirroring `frontend/tests/smoke-port.test.ts`).
- **External Execution:** GitHub Pages remains a static export of the last computed artifact;
  the live rerun API is **not** deployed publicly in this slice. Public parity proof stays the
  same deploy-coupled step owned by F.
- **External Blockers:** torch evidence remains optional/default-skipped; the reference backend
  must produce a deterministic result when torch is absent.

## 3. Functional Requirements

- **REQ-H4-001 — Live rerun endpoint.** Provide a backend endpoint (e.g. `POST
  /api/experiment/rerun`) that accepts validated `InteractiveResearchParameters` and recomputes
  the Epic H experiment through the existing `run_dl_experiment` pipeline, returning a
  checksummed artifact, OOS-net leaderboard rows (baseline visible), and registry lineage.
- **REQ-H4-002 — Deterministic recompute.** For identical parameters the endpoint returns an
  identical `reportChecksum` / `experiment_id`; the live `compute` result for the committed
  parameter set must equal the H-3 static-replay artifact (`c7347264…`) byte-for-byte.
- **REQ-H4-003 — Fail-closed inputs.** Out-of-range, unsupported-backend, non-integer-step, or
  otherwise invalid parameters return a structured fail-closed response (no computation, no
  partial/garbage rows), reusing the H-3 validation contract.
- **REQ-H4-004 — Async/compute lifecycle.** The UI and API expose explicit lifecycle states —
  at minimum `idle` / `computing` / `computed` / `fail_closed` / `error` — with a bounded
  timeout; a slow or dead backend degrades to a visible error state, never a spinner-forever or
  a silently stale "computed" panel.
- **REQ-H4-005 — Static-replay fallback preserved.** When no live backend is configured/reachable
  (e.g. the public static export), the UI falls back to the H-3 deterministic static-replay
  contract and shows the honest "no live backend" boundary, rather than appearing live.
- **REQ-H4-006 — Lineage & honesty surfaced.** Every live result carries `experimentId`,
  `reportChecksum`, `artifactPath`, approximate-vs-strict-PIT provenance, and `no_alpha_claim`;
  OOS-net-only ranking and visible baseline are enforced on the live path identically to static.
- **REQ-H4-007 — Public provider accessor (kills private access).** Add a public PIT-provider
  read API for event-date/price series so the rerun path (and existing research/scripts) stop
  reaching into `provider._prices`; consolidate the duplicated cotemporal-date logic onto it.
  (Resolves `ISSUE-DDD-PROVIDER-PRIVATE-001`.)
- **REQ-H4-008 — No actionable-signal surface.** The API and UI must not emit any current-asof
  allocation/recommendation or "buy now" output; results are historical OOS-net mechanism
  evidence only. (Charter guard for the deferred Lane 2.)

## 4. Acceptance Criteria

### AC-H4-01 — Live recompute matches static baseline
1. Given the committed parameter set, when the client calls the rerun endpoint, then the
   returned `reportChecksum` equals the H-3 static-replay artifact checksum.
2. Given the same parameters twice, then both responses are byte-identical (deterministic).

### AC-H4-02 — Real-backend smoke path (false-green guard)
1. A smoke test starts the **real** backend (governed dynamic port) and asserts a live rerun
   returns a freshly computed, checksum-verified artifact — not a replayed fixture.
2. The e2e/integration suite includes a negative test that **fails closed when the rerun
   endpoint is stubbed/mocked**, so a stub can never produce a green "live" result.
3. Mock/`page.route`/fixture usage in any UI test that exercises the live path is explicitly
   labeled and cannot satisfy AC-H4-02.1.

### AC-H4-03 — Async lifecycle is honest
1. A slow backend (beyond timeout) drives the UI to a visible `error` state, never an infinite
   spinner or a stale `computed` panel.
2. Invalid parameters yield `fail_closed` with no rendered metric rows.

### AC-H4-04 — Component-level coverage exists
1. The interactive components (`InvestmentCharts`, `InteractiveResearchPanel`) have direct
   component tests for `idle`/`computing`/`computed`/`fail_closed`/`error` rendering, closing the
   current zero-component-test gap; frontend coverage stays ≥ the existing thresholds.

### AC-H4-05 — Provider encapsulation
1. After this slice, no `quantlab` module or `scripts/` file reads `provider._prices`; the rerun
   path and existing callers use the public accessor (grep guard in tests).

### AC-H4-06 — Honesty boundaries preserved
1. Live results rank OOS-net only with the baseline visible and carry `no_alpha_claim`.
2. No endpoint or UI element emits a current-asof allocation/recommendation.
3. The public static export still falls back to static replay with `publicHosting` semantics
   unchanged; dashboard self-claim stays `not_proven`.

## 5. Seed Risk Register (full lightweight FMEA authored in Phase 2 design)

| Risk ID | Failure Mode | Effect | Planned Response (Prevent/Detect/Contain) |
|---|---|---|---|
| FMEA-H4-01 | e2e passes against a stubbed backend | **false-green**: "live demo works" but backend is mock (Global Constraint #11) | Detect: mandatory real-backend smoke (AC-H4-02) + negative stub-fails-closed test |
| FMEA-H4-02 | Slow/dead backend → infinite spinner or stale panel | user sees stale/fake "computed" result | Prevent: bounded timeout + explicit lifecycle states (REQ-H4-004) |
| FMEA-H4-03 | Live path bypasses OOS-net/baseline/no_alpha_claim guards | overclaim / alpha implication on dashboard | Prevent: shared validation on live + static paths (REQ-H4-006) |
| FMEA-H4-04 | Scope creep into current-asof recommendation | crosses locked no-alpha charter (Lane 2) | Contain: REQ-H4-008 guard + charter-gated deferral |
| FMEA-H4-05 | Non-deterministic recompute | checksum drift, public parity breaks | Detect: AC-H4-01 determinism + parity-with-static checksum |
| FMEA-H4-06 | Provider public accessor leaks lookahead | PIT violation on rerun | Prevent: accessor honors `available_date <= asof`; reuse A0 PIT guards |

## 6. Out of Scope

JAX/TF real backends, GPU/native models, production Tier3 serving/retraining/drift, multi-user
persistence, public deployment of the live API, and any actionable investment-recommendation
surface (deferred Lane 2, charter-gated).
