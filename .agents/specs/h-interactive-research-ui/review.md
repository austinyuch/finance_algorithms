# Review — H Interactive Research UI (slice H-3)

Date: 2026-06-18

## Verdict

**PASSED (repo-side/local static replay).**

H-3 is implemented as a local/static-replay interactive research UI over the existing
Epic H artifacts. It preserves `no_alpha_claim`, OOS-net-only ranking, visible baseline
comparison, deterministic lineage, approximate-data warnings, and fail-closed behavior
for unsupported parameter sets or stale checksums.

Public Pages parity is now **proven** for this branch artifact. After the dev lane was
squash-merged to `main` (`49a4510`), GitHub Pages built that commit and the live probe
observes deployed `dataHash c33da57d11c48945abcee36f2c78eb377f793536f769ddb10b87e8e4b3c7462a`,
matching the committed expected hash (`npm run probe:public-demo` → `proven`, HTTP 200 /
manifest 200 / hash `matched`, observed `2026-06-18T07:47Z`). The earlier deployed
`e57942605fd39fe21a5910164aad9e4af79d2d8aad9e28d7b04e858d01475953` is now historical
point-in-time evidence only. The dashboard self-claim remains `publicHosting=not_proven`
by contract — a static artifact cannot self-claim its deployment; the `proven` status
lives only in the observed probe/manifest.

## Acceptance Review

| Requirement | Result | Evidence |
|---|---|---|
| REQ-H3-PARAM-001 parameter workflow | PASS | `frontend/lib/interactive-research.ts`; `frontend/tests/interactive-research.test.ts` |
| REQ-H3-EXEC-001 deterministic artifact selection | PASS | `quantlab/showcase/scenario.py`; committed `interactiveResearch` payload with `mode=static_replay` |
| REQ-H3-EVIDENCE-001 no-alpha/OOS-net/lineage boundary | PASS | `frontend/lib/showcase-contract.ts`; `tests/quantlab/test_h3_interactive_showcase.py`; H-3 mutation gates |
| REQ-H3-VISUAL-001 result visualization | PASS | `frontend/components/InteractiveResearchPanel.tsx`; browser visual diff `1077 / 1,296,000` below threshold `0.001` |
| REQ-H3-TEST-001 local-first coverage | PASS | Python, mypy, import-linter, frontend test/coverage/build/smoke/visual/mutation gates |
| REQ-H3-PUBLIC-001 public honesty | PASS | Probe records `proven` / `matched` for deployed==expected `dataHash c33da57d…` after the `main` deploy; dashboard self-claim stays `not_proven` by contract; no production Tier3 claim |

## Evidence

- `uv run pytest -q` → 435 passed, 2 skipped.
- `uv run mypy quantlab/ --ignore-missing-imports` → success over 62 source files.
- `uv run lint-imports` → KEPT over 89 files / 248 dependencies.
- `cd frontend && npm test -- --run` → 52 passed.
- `cd frontend && npm run coverage` → 84.12% line coverage.
- `cd frontend && npm audit --json` → 0 vulnerabilities.
- `cd frontend && npm run visual` → passed.
- `cd frontend && npm run visual:browser` → passed; screenshot hash
  `365bb4b6558ab9e3fc430b61e09ce76634b45b24774b8a12618678bb00a10637`; pixel diff
  `1077 / 1,296,000`, threshold `0.001`.
- `cd frontend && npm run build` → passed.
- `cd frontend && npm run smoke` → passed.
- `cd frontend && npm run e2e:interactive` → passed; real Chromium/Next.js browser
  flow changes the seed parameter, observes `computed` → `fail_closed`, and compares
  the fail-closed screenshot against the committed VRT baseline with 0 mismatched pixels.
- `cd frontend && npm run mutation` → 29/29 killed, including
  `frontend-h3-interactive-claim-boundary`, `frontend-h3-approximate-warning-gate`, and
  `frontend-h3-e2e-failclosed-status-gate`.
- Public probe: HTTP 200 plus manifest 200, exit 0 — deployed `dataHash` now matches
  expected `c33da57d…` after the `main` deploy (`status=proven`, observed `2026-06-18T07:47Z`).

## Residuals

- **Deploy-coupled public proof — CLOSED (2026-06-18):** after the `main` deploy
  (`49a4510`) Pages served the refreshed artifact; the public probe re-ran `proven` /
  `matched` for `dataHash c33da57d…` and the committed proof was refreshed via
  `scripts/refresh_public_hosting_proof.py --live`. Reopen only if a later payload refresh
  changes `dataHash` without a matching Pages re-proof.
- **Future H slices:** live rerun API, JAX/TF real training, GPU/native models, shared
  experiment storage, and production Tier3 proof remain explicitly out of scope.
