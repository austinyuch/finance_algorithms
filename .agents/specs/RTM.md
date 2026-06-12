# RTM.md — Requirements Traceability Matrix (Bridge)

> Cross-spec traceability and verification context only. **Not** a readiness
> authority — authoritative Live-Demo Readiness lives in each
> `.agents/specs/**/review.md`; the stable registry is
> [`SPECS.md`](./SPECS.md); rolling state is [`NEXT_STEPS.md`](./NEXT_STEPS.md).
> Generated docs ([`docs/manual/`](../../docs/manual/),
> [`docs/review/`](../../docs/review/)) consume this bridge for verification
> context, never to derive verdicts.

## Epic → requirement → implementation → test → review

| Epic | Core requirement (abridged) | Key implementation | Test / evidence anchor | Review verdict |
|---|---|---|---|---|
| A0 | Lookahead-safe vectorized backtest with OOS-net metrics, walk-forward, parallel run, tracking | `quantlab/{contracts,data,engine,parallel,tracking}` | `test_a0_0..5`; CR-A0 regime scheduling; current mutation spot checks 54/54 configured/killed | **PASSED** |
| A | TSMC hedge slice ranked vs baselines; optional PyTorch LSTM lane isolated from default runtime | `quantlab/strategies/`, `scripts/run_tsmc_hedge_slice.py`, `pyproject.toml`, `uv.lock` | `test_a_1,3,4,5`; optional `test_a_2_lstm`; `test_dependency_security.py`; `root-torch-default-dependency` mutation | **PASSED** (synthetic; `no_alpha_claim`; default env no Torch) |
| Governance | Current-state evidence freshness and false-green prevention | `tests/quantlab/test_governance_guards.py`; `scripts/run_mutation_spot_checks.py`; `.agents/specs/governance-evidence-refresh/`; `NEXT_STEPS.md`; `f-public-static-showcase/change-requests/cr-fps-001-hosting-manifest-proof-sync.md`; `f-public-static-showcase/change-requests/cr-fps-002-hosting-content-hash-proof.md`; `f-public-static-showcase/change-requests/cr-fps-003-hosting-manifest-contract-proof.md`; `f-public-static-showcase/change-requests/cr-fps-007-public-probe-parity-status.md`; `f-public-static-showcase/change-requests/cr-fps-008-public-probe-freshness-gate.md` | stale governance guard 13 passed; governance mutations killed, including `governance-stale-next-steps-alert`, `governance-stale-post-merge-sync-promotion`, `governance-stale-cron-proof-pending`, `governance-exhaustive-pr-ledger-regression`, `public-hosting-manifest-status-overclaim`, `public-hosting-probe-status-overclaim`, `review-public-hosting-probe-status-overclaim`, `public-hosting-manifest-hash-overclaim`, `public-hosting-probe-hash-overclaim`, `public-hosting-manifest-contract-regression`, `public-hosting-taxonomy-authority-regression`, `manual-showcase-payload-sync-regression`, `frontend-showcase-payload-sync-regression`, `review-pytest-gate-transcript-regression`, and `review-audit-gate-transcript-regression`; Dependabot #7 fixed; current registries use 241 suite evidence, public probe freshness status, and visual diff `1052 / 1,296,000` | **PASSED** (`governance-evidence-refresh` + promotion-boundary guard + CR-FPS-001 + CR-FPS-002 + CR-FPS-003 + CR-FPS-007 + CR-FPS-008) |
| B | PIT vintage loader, FRED proxies, as-of alignment, `pit_strictness`, source-health, snapshot run report + ops gate + scheduled run observer + scoped live write smoke + broad source-quorum gate + live quorum proof + Stooq fail-closed proof wrapper | `quantlab/data/`, `scripts/{daily_snapshot,snapshot_ops_gate,source_quorum_proof,stooq_contract_proof,scheduled_run_observer}.py`, `.github/workflows/daily-snapshot.yml` | `test_b_1..5`; `test_daily_snapshot.py` (42); CR-B5/B7..B20; Actions runs `27387041974` (`workflow_dispatch`) and `27392471359` (`schedule`); scheduled observation `status=proven`, `schedule_run_count=1`; CR-B12 live smoke `ok=1` then `skip=1`; CR-B19 live proof `status=proven`, `fail=0`, `skip=6` for FRED/Yahoo/NOAA quorum; CR-B20 live Stooq `spy.us` probe `status=not_proven` after HTTP 404; current-lane field stays stable `none`; promotion proof authority is GitHub PR state plus spec-local reports, not an exhaustive `NEXT_STEPS.md` ledger | **PASSED (repo-side + scoped live write smoke + workflow_dispatch + autonomous cron dry-run proof + fail-closed observer + source-quorum live proof + Stooq fail-closed proof wrapper + promotion-boundary guard)**; residual `ISSUE-B3-001` (Stooq availability) |
| C | Optimizer, multi-period allocation, regime rebalance selector, pyramid-entry adapter | `quantlab/portfolio/` | `test_c_1..5` (123) | **PASSED** |
| D | First-regime, return/risk forecast, robust optimizer, family evaluator — OOS-net baselines | `quantlab/models/`, `quantlab/research/` | `test_d_1,3,4,5,6`; real-data regime benchmark | **PASSED** (`no_alpha_claim`) |
| E | Experiment registry, config catalog, checksum snapshot durability, registry→dashboard bridge, Tier3 readiness gate, local serving/retraining/automated drift monitoring smoke evidence, production-tier evidence gate, governed production evidence probes, strict readiness proof CLI | `quantlab/mlops/`, `quantlab/showcase/`, `scripts/tier3_readiness_gate.py` | `test_e_1` (27); `test_tier3_readiness_gate_cli` (4); `e-tier3-readiness-gate`, `e-serving-smoke-health-gate`, `e-retraining-smoke-status-gate`, `e-tier3-production-tier-gate`, `e-automated-drift-status-gate`, `e-production-serving-endpoint-gate`, `e-production-retraining-status-gate`, and `e-tier3-cli-serving-validator` mutations killed; focused `experiment_registry` line coverage 100% | **PASSED** (local smoke only; production proof requires external payloads) |
| F | Showcase read API, Next.js dashboard, demo hardening, public/static showcase, canonical local result-store payload | `quantlab/showcase/`, `frontend/` | `test_f_1`; `frontend` npm test; static export; CR-FPS-006 source metadata guard; CR-FPS-007 committed probe parity-status guard; CR-FPS-008 probe freshness guard | **CONDITIONAL** · `local_demo_only` |
| F/B/E ops | Browser visual diff, public-hosting probe, deployment manifest/probe/content-hash/contract/freshness consistency, schedule run proof, scoped/live quorum snapshot proof, E drift report | `frontend/scripts/{browser-visual-smoke,probe-public-demo}.mjs`, `frontend/scripts/export-public-demo.tsx`, `docs/{deployment-manifest,public-hosting-probe}.json`, `frontend/visual-baselines/browser-visual.png`, `.github/workflows/daily-snapshot.yml`, `scripts/{daily_snapshot,source_quorum_proof,stooq_contract_proof}.py` | `browser-visual.png` `proven`; repo-baseline pixel diff `1052 / 1,296,000`; branch-local public-hosting proof and standalone probe are `configured_not_observed` after CR-FPS-006 until Pages serves the refreshed `dataHash`; standalone probe now records `freshnessStatus=fresh` / `maxAgeHours=24` and CR-FPS-008 guards stale observation overclaim; Actions `schedule` run `27392471359`; CR-B12 live write smoke; CR-B19 broad FRED/Yahoo/NOAA quorum proof; CR-B20 Stooq proof fails closed on HTTP 404; Python mutation includes `f-showcase-canonical-source`; frontend mutation includes `frontend-dashboard-source-regression` and `frontend-public-demo-probe-freshness-status-gate` | **PASSED** (ops-visual-drift-artifacts + f-browser-pixel-baseline + b-live-scheduled-snapshot-proof + promotion-boundary guard + CR-FPS-001 + CR-FPS-002 + CR-FPS-003 + CR-FPS-004 + CR-FPS-005 + CR-FPS-006 + CR-FPS-007 + CR-FPS-008 + CR-B19 + CR-B20) |
| G | Source-contract-first local alt-data loader (two optional slices) | `quantlab/data/` alt-data loader | `test_g_1` (7); PBT + mutation | **PASSED** (default-disabled) |
| Legacy | Arithmetic/geometric pyramid order sizing API | `invest_algorithms/` | `tests/test_algo_pyramid.py` | stable legacy baseline |

## Verification snapshot (2026-06-12)

| Gate | Command | Result |
|---|---|---|
| Python suite | `uv run pytest -q` | **241 passed** |
| Type check | `uv run mypy quantlab/ scripts/build_showcase_payload.py scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py scripts/source_quorum_proof.py scripts/stooq_contract_proof.py --ignore-missing-imports` | clean, 57 files |
| Architecture | `uv run lint-imports` | KEPT (74 files, 185 deps) |
| Frontend unit | `cd frontend && npm test` | 32 passed |
| Frontend supply chain | `npm audit --omit=dev` | 0 vulnerabilities |
| E registry line coverage | `uv run pytest --cov=quantlab.mlops.experiment_registry --cov-report=term-missing tests/quantlab/test_e_1_experiment_registry.py` | 27 passed; 100% line coverage |
| Python mutation | `uv run python scripts/run_mutation_spot_checks.py` | 54/54 configured mutations killed, including CR-B12 `snapshot-scoped-source-health`, CR-B19 `b-source-quorum-proof-exit-gate` / `b-source-quorum-proof-file-gate`, CR-B20 `b-stooq-proof-exit-gate` / `b-stooq-proof-file-gate`, governance `governance-stale-next-steps-alert`, `governance-stale-post-merge-sync-promotion`, `governance-stale-cron-proof-pending`, `governance-exhaustive-pr-ledger-regression`, CR-FPS-001 `public-hosting-manifest-status-overclaim`, CR-FPS-007 `public-hosting-probe-status-overclaim` / `review-public-hosting-probe-status-overclaim` / `public-hosting-probe-hash-overclaim`, CR-FPS-002 `public-hosting-manifest-hash-overclaim`, CR-FPS-003 `public-hosting-manifest-contract-regression`, `public-hosting-taxonomy-authority-regression`, `manual-showcase-payload-sync-regression`, `frontend-showcase-payload-sync-regression`, `review-pytest-gate-transcript-regression`, and `review-audit-gate-transcript-regression`; CR-FPS-008 is covered by the frontend mutation row |
| Frontend mutation | `cd frontend && npm run mutation` | 15/15 killed, including `frontend-public-demo-hosting-freshness-gate` and CR-FPS-008 `frontend-public-demo-probe-freshness-status-gate` |
| Browser visual | `cd frontend && npm run visual:browser` | `proven`; repo-baseline pixel diff `1052 / 1,296,000` at threshold `0.001` |
| Public-hosting probe | `cd frontend && npm run probe:public-demo` | HTTP 200 plus deployed manifest HTTP 200; after CR-FPS-006 the branch-local manifest and standalone probe record `status=configured_not_observed` / `hashStatus=mismatched` and the probe exits 2 until Pages serves the refreshed `dataHash` |

## Open verification gaps (owned elsewhere)

- No CI-managed visual baseline history beyond the committed repo baseline —
  residual in `f-browser-pixel-baseline/review.md`.
- GitHub Actions autonomous `event=schedule` dry-run proof exists
  (`27392471359`); scheduled observer artifact records `status=proven`,
  `schedule_run_count=1`. CR-B12 separately proves scoped local live
  append-only write/skip mechanics. CR-B19 proves broad FRED/Yahoo/NOAA source
  quorum for 2026-06-12. CR-B20 proves Stooq restoration attempts fail closed
  without positive finite live close rows; Stooq remains a source-contract gap.
- Real-data backtest — deferred until ≥2 price assets accumulate
  (`run_vintage_slice.py`).
- Stooq source contract — `ISSUE-B3-001` (folded into CR-B7/B8/B9/B20; still blocked/default-disabled).

> Resolved 2026-06-11/12: live chromium-headless browser screenshot
> (`browser-visual.png` `proven`) and public-hosting probe (HTTP 200 plus
> deployed manifest contract metadata) now exist. CR-FPS-005 confirms Pages now
> serves the CR-FPS-005 `docs/` artifact with matching `dataHash`. CR-FPS-006
> now generates the dashboard payload from a local `LocalResultStore` /
> `ExperimentRegistry` scenario; branch-local hosting parity is pending until
> Pages serves the refreshed `dataHash`, and dashboard readiness remains
> conservative as `local_demo_only`.

Doc reconciliation on 2026-06-12 surfaced **no new unowned issues**; all gaps
trace to an existing spec/CR/review or `ISSUE_LOG.md`.
