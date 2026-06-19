# Review — H Live Backend Rerun API (slice H-4)

> SDD Phase 5. Scope: [requirements.md](./requirements.md) · [design.md](./design.md) ·
> [tasks.md](./tasks.md) · [contract](./contract/live-rerun.schema.json).
> Verdict authority for the repo-side live-rerun slice. `no_alpha_claim`.

## Verdict: **Implemented (repo-side) · Review PASSED for the local live-rerun slice**

The live backend rerun capability deferred by H-3 is delivered repo-side: a real Python
backend recomputes an Epic H experiment from validated parameters through the existing
`run_experiment` pipeline and returns a checksummed `live_compute` artifact; a Next.js proxy
route drives it with an honest static-replay fallback; the UI exposes an explicit lifecycle
(`idle/computing/computed/fail_closed/error`); and a **real-backend dynamic-port smoke**
proves the result is freshly computed, not a fixture. Public deployment of the live API
remains out of scope (static export only), as specified.

## REQ / AC → Evidence

| Item | Evidence | Status |
|---|---|---|
| REQ-H4-001 live rerun endpoint | `quantlab/showcase/rerun_service.py` (`run_rerun` + ASGI `make_app`/`app`, `POST /api/experiment/rerun`); `test_h4_live_rerun` ASGI 200 | ✅ |
| REQ-H4-002 / AC-H4-01 determinism | `test_h4_live_rerun::test_run_rerun_is_deterministic`; smoke determinism | ✅ determinism; ⏸ **static byte-parity** with the H-3 block is deploy-coupled (see Residual 1) |
| REQ-H4-003 fail-closed inputs | validation fail-closed unit cases (backend/step/range/symbols); ASGI 422 | ✅ |
| REQ-H4-004 / AC-H4-03 async lifecycle | `frontend/lib/live-rerun.ts` reducer + bounded `AbortController` client; timeout→`error`; `LiveRerunStatus` 5 states | ✅ |
| REQ-H4-005 static-replay fallback | `app/api/experiment/rerun/route.ts` returns `static_replay`/`static_fallback` when `QUANTLAB_RERUN_BACKEND_URL` unset | ✅ |
| REQ-H4-006 lineage & honesty on live path | `build_live_payload` (no_alpha_claim, OOS-net sorted, baseline visible, approximate provenance); one shared contract validator (`assertInteractiveResearch`) on both modes | ✅ |
| REQ-H4-007 / AC-H4-05 public provider accessor | `provider.symbols/event_span/price_panel`; all `_prices` reach-ins migrated; grep guard; `ISSUE-DDD-PROVIDER-PRIVATE-001` resolved | ✅ |
| REQ-H4-008 / AC-H4-06 no actionable signal | `test_payload_carries_no_actionable_signal`; no allocation/recommendation field in the contract | ✅ |
| AC-H4-02 real-backend smoke (false-green guard) | `tests/test_h4_rerun_smoke.py`: uvicorn dynamic-port, fresh-checksum freshness proof + negative stub-fails-freshness | ✅ |
| AC-H4-04 component coverage | `tests/live-rerun-status.test.tsx` renders all 5 lifecycle states + panel wiring | ✅ |

## Test bar coverage

- **Unit:** TS reducer/client/contract; Python validation + payload mapping.
- **PBT:** Python valid-grid compute/fail-closed + provider usable-close (`test_h4_provider_view`); TS client mapping.
- **Integration:** in-process ASGI 200/422/404/405/400; provider-view migration under the green real_data_oos/multi_cycle suites.
- **Smoke:** real uvicorn dynamic-port backend, fresh-compute proof (`@smoke`).
- **Chaos-adjacent:** fail-closed on invalid params / insufficient data / unreachable backend / timeout; NaN-poisoned asset drops from the universe (carried from CR-A0-CHAOS-001).
- **Mutation:** Python `h4-rerun-validation-fail-closed-gate` KILLED; provider usable-close filter guard KILLED.
- **VRT / e2e (browser):** deferred — deploy/browser-coupled (Residual 2/3).

## Residual / deliberately deferred (non-blocking for the repo-side slice)

1. **Static byte-parity (AC-H4-01.1).** The H-3 static block is a hand-authored synthetic
   replay (`GROWTH/STEADY`), not a `run_experiment` output, so byte-parity with a live
   compute is not achievable without regenerating the committed static artifact from a real
   run. That re-pin changes the dashboard payload/`dataHash` and is **deploy-coupled** — bundle
   it with the `dev`→`main` deploy. Determinism (AC-H4-01.2) is proven now.
2. **Browser e2e (`npm run e2e:rerun`) + VRT (H4-11).** The Python socket smoke already proves
   FMEA-H4-01 (no stubbed false-green). The browser-driven `idle→computing→computed` VRT
   baselines are browser/deploy-coupled; the new live UI controls also require the static
   export + visual baseline re-pin (`ISSUE-VRT-EXPORT-STALE-DEV-001`).
3. **Published count bumps (H4-12).** pytest and Python/frontend mutation totals + the static
   export/`dataHash`/visual re-pin live in the deploy-coupled `docs/showcase.json` payload;
   they are bundled with the user-gated deploy (mirrors CR-RDO-005), not flipped mid-branch.
4. **Layering (`ISSUE-DDD-QUANTLAB-IMPORTS-SCRIPTS-001`).** `rerun_service` imports
   `scripts.run_dl_experiment`; lift `run_experiment` into `quantlab/research/` when next edited.

## Boundary

Local/repo-side live rerun only. No public deployment of the live API, no JAX/TF/GPU real
training, no production Tier3, and — by REQ-H4-008 — **no current-asof allocation /
recommendation surface** (the charter-gated Lane 2 stays deferred). `no_alpha_claim`; the
dashboard self-claim stays `not_proven` by the static-artifact contract.
