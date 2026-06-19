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

### H4-2 — Python rerun backend service (REQ-H4-001/002/003)

- [ ] **RED:** Unit/integration for `quantlab/showcase/rerun_service.py`: valid params →
  `computed` artifact (checksum + OOS-net rows, baseline visible); invalid/out-of-range/
  unsupported-backend/non-integer-step → `fail_closed` (no rows); `run_experiment`
  `insufficient_data` → `fail_closed` with upstream reason.
- [ ] **GREEN:** Implement the ASGI app wrapping `run_experiment` into a temp workspace
  (no repo pollution; mirror `test_demo_script_tempstores`); normalize the artifact to the
  `live_compute` contract. No torch/tf/jax import (framework isolation; `lint-imports` KEPT).
- [ ] **REFACTOR:** Share parameter validation with the H-3 range contract; keep the service thin.
- [ ] **Evidence:** `uv run pytest -q tests/quantlab/test_h4_live_rerun.py`; `uv run lint-imports`.

### H4-3 — Next.js proxy route + static-replay fallback (REQ-H4-005, FMEA-H4-07)

- [ ] **RED:** Route tests for `POST app/api/experiment/rerun`: proxies to
  `QUANTLAB_RERUN_BACKEND_URL` when set; returns H-3 `static_replay` fallback (honest
  "no live backend") when unset; returns `error` lifecycle on unreachable/timeout.
- [ ] **GREEN:** Implement the route as a thin adapter (no experiment math in TS).
- [ ] **REFACTOR:** Reuse existing response/fail-closed shapes; single source of env handling.
- [ ] **Evidence:** `cd frontend && npm test -- --run tests/api-rerun.test.ts`.

### H4-4 — TS lifecycle reducer + bounded client (REQ-H4-004, AC-H4-03)

- [ ] **RED:** Unit tests for `frontend/lib/live-rerun.ts`: all transitions
  `idle→computing→{computed|fail_closed|error}`; timeout via `AbortController` → `error`
  (never spinner-forever); a stale prior `computed` is cleared on a new `computing`.
- [ ] **GREEN:** Implement the pure reducer + `requestLiveRerun(params, signal)` client.
- [ ] **REFACTOR:** Reuse `validateInteractiveResearchParameters`; keep the reducer pure/testable.
- [ ] **Evidence:** `cd frontend && npm test -- --run tests/live-rerun.test.ts`.

### H4-5 — Contract widen `mode=live_compute` + shared validator (REQ-H4-006, FMEA-H4-03)

- [ ] **RED:** Contract tests that `live_compute` payloads are validated by the **same**
  guards as `static_replay` (no_alpha_claim, OOS-net authority, visible baseline, approximate
  warning, sorted rows, checksum shape); a non-`no_alpha_claim` or hidden-baseline live
  payload is rejected.
- [ ] **GREEN:** Widen `InteractiveResearchPayload.mode` and add `lifecycle`/`computeSource`
  in `frontend/lib/showcase-contract.ts`; one validator covers both modes.
- [ ] **REFACTOR:** No duplicated mode-specific validation.
- [ ] **Evidence:** `cd frontend && npm test -- --run tests/showcase-contract.test.ts`.

### H4-6 — Component tests (AC-H4-04)

- [ ] **RED:** Co-located component tests for `InteractiveResearchPanel` and `InvestmentCharts`
  rendering `idle`/`computing`/`computed`/`fail_closed`/`error`, closing the current
  zero-component-test gap.
- [ ] **GREEN:** Add the `computing`/`error` render states to the components (idle/computed/
  fail_closed already exist).
- [ ] **REFACTOR:** Reuse quiet dashboard styling; stable control/chart dimensions.
- [ ] **Evidence:** `cd frontend && npm test -- --run tests/InteractiveResearchPanel.test.tsx tests/InvestmentCharts.test.tsx`; coverage ≥ existing thresholds.

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
