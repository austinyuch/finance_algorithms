# Tasks — H Live Backend Rerun API (slice H-4)

> SDD Phase 3. Requirements: [requirements.md](./requirements.md). Design:
> [design.md](./design.md). Contract: [contract/live-rerun.schema.json](./contract/live-rerun.schema.json).
> All tasks are TDD (RED → GREEN → REFACTOR). Sequencing follows design §5 (REFACTOR with a
> green safety-net first), then backend, then frontend, then the load-bearing real-backend
> smoke, then closeout.

## Task Matrix

### H4-1 — Public PIT-provider view + kill `_prices` reach-ins (REQ-H4-007, AC-H4-05) ✅ DONE

- [x] **RED:** `tests/quantlab/test_h4_provider_view.py` — unit/PBT for `symbols()`,
  `event_span(symbols)`, `price_panel(symbols, *, usable_only)`: copy-safe, **never** returns
  non-finite/non-positive closes when `usable_only`, plus a grep guard that no
  `quantlab`/`scripts` file reads `provider._prices` (only the provider's own `self._prices`).
- [x] **GREEN:** Added the public view to `quantlab/data/provider.py`; migrated
  `real_data_oos` (`estimate_sampling_frequencies`, `_asset_spans`, `assess_data_sufficiency`,
  `_window`), `run_dl_experiment` (`_cotemporal_dates` + symbol membership), and
  `run_vintage_slice` onto it. (`multi_cycle_oos` already routes through `real_data_oos`.)
- [x] **REFACTOR:** Usable-close filter now lives once in `price_panel(usable_only=True)`;
  the as-of fetch path (`get`/`history`, `available_date<=asof`) is untouched (FMEA-H4-06).
  Repointed mutation `a0-chaos-asset-span-usable-close-filter` to the provider; KILLED.
- [x] **Evidence:** H4 view + all `real_data_oos*` + `multi_cycle_oos` **88 passed**; demo
  tempstores + governance green; mypy clean (64 files); `lint-imports` KEPT. Grep guard green
  → **`ISSUE-DDD-PROVIDER-PRIVATE-001` resolved**.

### H4-2 — Python rerun backend service (REQ-H4-001/002/003) ✅ DONE

- [x] **RED:** `tests/quantlab/test_h4_live_rerun.py` (18 tests) — validation fail-closed
  cases, computed-payload contract shape (OOS-net sorted, baseline visible, no_alpha_claim,
  64-hex checksum), determinism, insufficient-data fail-closed, charter guard (no actionable
  wording), and the dependency-free ASGI transport (200/422/404/405/400).
- [x] **GREEN:** `quantlab/showcase/rerun_service.py` — `validate_parameters`, `run_rerun`
  (wraps `run_experiment` in a `TemporaryDirectory`, no repo pollution; temp artifact paths
  are not leaked), `build_live_payload` (reuses the run_experiment report as the sole
  calculation authority — derives `returnDistribution` from equity ratios, CAGR/maxDD from
  the curve), and a dependency-free ASGI `make_app`/`app`. Added resolved `backend`/
  `parameters`/`data_window` to `run_experiment`'s return (additive). No torch/tf/jax import.
- [x] **REFACTOR:** `PARAMETER_RANGES` SSOT mirrors the H-3 contract ranges; service stays thin.
- [x] **Evidence:** `test_h4_live_rerun.py` **18 passed**; mypy clean (`quantlab/` 63 files);
  `lint-imports` KEPT (framework isolation); mutation `h4-rerun-validation-fail-closed-gate` KILLED.

### H4-3 — Next.js proxy route + static-replay fallback (REQ-H4-005, FMEA-H4-07) ✅ DONE

- [x] **RED/GREEN:** `frontend/app/api/experiment/rerun/route.ts` — proxies to
  `QUANTLAB_RERUN_BACKEND_URL` when set; returns the honest `static_replay` /
  `computeSource=static_fallback` "no live backend" response (HTTP 200) when unset; bounded
  `AbortController` → `error` lifecycle (504) on unreachable/timeout; malformed JSON → 400;
  unreadable upstream → 502. No experiment math in TS.
- [x] **REFACTOR:** Single env-handling helper; reuses the contract's fail-closed/error shapes.
- [x] **Evidence:** lifecycle/proxy behaviour is exercised by `live-rerun.test.ts` (client
  side) and will get a server-route + real-backend assertion in H4-7. (The route is a thin
  adapter; its branches are pure env/fetch mapping.)

### H4-4 — TS lifecycle reducer + bounded client (REQ-H4-004, AC-H4-03) ✅ DONE

- [x] **RED:** `frontend/tests/live-rerun.test.ts` — reducer transitions
  `idle→computing→{computed|fail_closed|error}`, `submit` clears a stale `computed`, `reset`;
  `requestLiveRerun` maps computed/fail_closed/error responses, **timeout/abort → error**
  (never spinner-forever), and network rejection → error.
- [x] **GREEN:** `frontend/lib/live-rerun.ts` — pure `liveRerunReducer` + `requestLiveRerun`
  with a bounded `AbortController` timeout; never throws (all failures map to an `error` action).
- [x] **REFACTOR:** Reuses contract types; reducer is pure/dispatch-testable.
- [x] **Evidence:** `tests/live-rerun.test.ts` lifecycle + client cases pass.

### H4-5 — Contract widen `mode=live_compute` + shared validator (REQ-H4-006, FMEA-H4-03) ✅ DONE

- [x] **RED:** `live-rerun.test.ts` contract block — a dashboard whose `interactiveResearch`
  is `live_compute` passes `assertDashboardPayload`; a `live_compute` payload that drops
  `no_alpha_claim` is rejected (same guards as static).
- [x] **GREEN:** Widened `InteractiveResearchPayload.mode` to `static_replay | live_compute`,
  added optional `lifecycle`/`computeSource`, and relaxed `assertInteractiveResearch` to accept
  both modes — all honesty literals enforced by the one shared validator.
- [x] **REFACTOR:** No mode-specific validation duplicated.
- [x] **Evidence:** `tests/live-rerun.test.ts` + `tests/dashboard.test.tsx` + `interactive-research.test.ts` **28 passed** together.

### H4-6 — Component tests (AC-H4-04) ✅ DONE

- [x] **RED:** `frontend/tests/live-rerun-status.test.tsx` — direct render tests for all five
  lifecycle states (`idle`/`computing`/`computed`/`fail_closed`/`error`) via
  `renderToStaticMarkup` (vitest `node` env, no RTL), closing the zero-component-test gap, plus
  a panel test asserting the live control + idle lifecycle render without breaking static replay.
- [x] **GREEN:** Extracted a pure presentational `components/LiveRerunStatus.tsx` (state →
  markup, no async/effects so every state is render-testable) and wired it additively into
  `InteractiveResearchPanel` (a `useReducer` + a "Run live rerun" button calling
  `requestLiveRerun`). `computing` shows an `aria-busy` spinner and never a stale result;
  `error` shows a visible message, never a spinner.
- [x] **REFACTOR:** Async orchestration stays in the panel; the view is pure/SSR-testable.
- [x] **Evidence:** `live-rerun-status.test.tsx` 6 + dashboard regression + live-rerun lib
  **29 passed** together; full frontend suite **67 passed** (only the pre-existing
  deploy-coupled `ISSUE-VRT-EXPORT-STALE-DEV-001` is red). NOTE: the new live controls change
  the rendered Dashboard HTML, so the static-export/visual baseline re-pin at deploy (H4-11/
  H4-12) must capture them.

### H4-7 — Real-backend smoke + negative stub-fails-closed (AC-H4-02, FMEA-H4-01) — load-bearing

- [ ] **RED:** A smoke (`frontend/scripts/rerun-e2e.mjs`, `npm run e2e:rerun`) that starts the
  **real** Python backend on a governed dynamic port (`selectSmokePort`/`findAvailablePort`),
  drives `idle→computing→computed`, and asserts a *freshly computed* checksum differing from
  the committed fixture for a perturbed seed. Plus a **negative** test pointing the route at a
  stub backend asserting `fail_closed`/`error`.
- [ ] **GREEN:** Wire the smoke script + npm script; label any `page.route`/fixture mock so it
  cannot satisfy AC-H4-02.1.
- [ ] **REFACTOR:** Reuse the dynamic-port helper; deterministic teardown.
- [ ] **Evidence:** `cd frontend && npm run e2e:rerun`; evidence JSON records a real-backend, fresh-checksum run.

### H4-8 — Determinism + static parity (AC-H4-01, FMEA-H4-05)

- [ ] **RED:** Integration test that the committed parameter set's live `reportChecksum`
  equals the H-3 static artifact, and that two identical requests are byte-identical.
- [ ] **GREEN:** Ensure temp-path/seed/ordering never leak into the checksum.
- [ ] **REFACTOR:** Centralize artifact normalization shared by static + live.
- [ ] **Evidence:** `uv run pytest -q tests/quantlab/test_h4_live_rerun.py -k parity_or_determinism`.

### H4-9 — Charter guard: no actionable-signal surface (REQ-H4-008, FMEA-H4-04)

- [ ] **RED:** Negative test that no endpoint/UI element emits a current-asof allocation /
  "buy now" / recommendation; results are historical OOS-net mechanism evidence only.
- [ ] **GREEN:** Enforce via contract literals + a wording grep guard.
- [ ] **Evidence:** `uv run pytest -q tests/quantlab/test_governance_guards.py -k charter`; `cd frontend && npm test -- --run`.

### H4-10 — Mutation (Python + frontend)

- [ ] **RED/GREEN:** Register Python mutations in `scripts/run_mutation_spot_checks.py` for
  the rerun fail-closed gate and the provider usable-close filter; add frontend mutations for
  the lifecycle `error`/timeout gate and the `live_compute` claim-boundary/baseline gate.
- [ ] **REFACTOR:** Keep published mutation counts consistent with governance artifacts.
- [ ] **Evidence:** `uv run python scripts/run_mutation_spot_checks.py --only <h4 guards>`; `cd frontend && npm run mutation`.

### H4-11 — VRT for new lifecycle states (FMEA-H4-02)

- [ ] **RED:** Observe browser visual baselines for `computing` and `error` states.
- [ ] **GREEN:** Pin the new VRT baselines (computed-state baseline reused) via the existing scripts only.
- [ ] **Evidence:** `cd frontend && npm run visual:browser`; `npm run e2e:rerun` VRT.

### H4-12 — Governance, review, and local-first closeout

- [ ] Refresh `quantlab/TESTS.md`, `SPECS.md`, `RTM.md`, `ISSUE_LOG.md` (close
  `ISSUE-DDD-PROVIDER-PRIVATE-001`), `NEXT_STEPS.md`, `docs/FEATURES.md`, and generated
  proof surfaces affected by any new payload hash (deploy-coupled bump bundled with the
  F-owned deploy, mirroring CR-RDO-005).
- [ ] Author `review.md` capped to repo-side/local demo; public hosting stays `not_proven`
  unless a fresh live probe proves the new deployed hash.
- [ ] Run the local-first matrix or record explicit hosted-only gaps.
- [ ] **Evidence:** `uv run pytest -q`; `uv run mypy quantlab/ --ignore-missing-imports`;
  `uv run lint-imports`; `git diff --check`; full frontend test/coverage/build/smoke/visual/
  mutation + `e2e:rerun` gates.

## FMEA Trace

| Risk | Tasks |
|---|---|
| FMEA-H4-01 stubbed-backend false-green | H4-7 |
| FMEA-H4-02 slow/dead backend spinner/stale | H4-4, H4-8, H4-11 |
| FMEA-H4-03 live path bypasses honesty guards | H4-5, H4-10 |
| FMEA-H4-04 actionable-signal scope creep | H4-9 |
| FMEA-H4-05 non-deterministic recompute | H4-8 |
| FMEA-H4-06 provider view leaks lookahead | H4-1 |
| FMEA-H4-07 static export appears live | H4-3 |

## Completion Rule

The slice is not review-ready until all RED/GREEN/REFACTOR tasks are closed, the
**real-backend smoke (H4-7) proves a freshly computed checksum** (a stub can never go green),
the local-first evidence matrix has run, no `provider._prices` reach-in remains, and
public-hosting status is either freshly `proven` for the new data hash or explicitly
documented as non-proven pending the F-owned deploy. `no_alpha_claim`; no actionable-signal
surface (Lane 2 stays charter-gated).
