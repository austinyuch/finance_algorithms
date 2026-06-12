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
| A0 | Lookahead-safe vectorized backtest with OOS-net metrics, walk-forward, parallel run, tracking | `quantlab/{contracts,data,engine,parallel,tracking}` | `test_a0_0..5`; CR-A0 regime scheduling; current mutation spot checks 40/40 configured/killed | **PASSED** |
| A | TSMC hedge slice ranked vs baselines; optional PyTorch LSTM lane isolated from default runtime | `quantlab/strategies/`, `scripts/run_tsmc_hedge_slice.py`, `pyproject.toml`, `uv.lock` | `test_a_1,3,4,5`; optional `test_a_2_lstm`; `test_dependency_security.py`; `root-torch-default-dependency` mutation | **PASSED** (synthetic; `no_alpha_claim`; default env no Torch) |
| Governance | Current-state evidence freshness and false-green prevention | `tests/quantlab/test_governance_guards.py`; `scripts/run_mutation_spot_checks.py`; `.agents/specs/governance-evidence-refresh/`; `b-data-platform/change-requests/cr-b13-post-live-write-governance-sync.md`; `b-data-platform/change-requests/cr-b14-post-crb13-governance-sync.md`; `b-data-platform/change-requests/cr-b15-post-crb14-governance-sync.md`; `b-data-platform/change-requests/cr-b16-post-crb15-governance-sync.md` | stale governance guard 10 passed; governance mutations killed, including `governance-stale-live-write-promotion`, `governance-stale-cr-b13-promotion`, `governance-stale-cr-b14-promotion`, and `governance-stale-cr-b15-promotion`; Dependabot #7 fixed; current registries use 223 suite evidence and visual diff `505 / 1,296,000` | **PASSED** (`governance-evidence-refresh` + CR-B13/CR-B14/CR-B15/CR-B16) |
| B | PIT vintage loader, FRED proxies, as-of alignment, `pit_strictness`, source-health, snapshot run report + ops gate + scheduled run observer + scoped live write smoke | `quantlab/data/`, `scripts/{daily_snapshot,snapshot_ops_gate,scheduled_run_observer}.py`, `.github/workflows/daily-snapshot.yml` | `test_b_1..5`; `test_daily_snapshot.py` (28); CR-B5/B7..B16; Actions runs `27387041974` (`workflow_dispatch`) and `27392471359` (`schedule`); scheduled observation `status=proven`, `schedule_run_count=1`; CR-B12 live smoke `ok=1` then `skip=1`; PR #61/#62, PR #63/#64, PR #65/#66, and PR #67/#68 promotion memos guarded; current-lane field stays stable `none` | **PASSED (repo-side + scoped live write smoke + workflow_dispatch + autonomous cron dry-run proof + fail-closed observer + post-promotion stale-resume guards)**; residual `ISSUE-B3-001` (Stooq and broad source availability) |
| C | Optimizer, multi-period allocation, regime rebalance selector, pyramid-entry adapter | `quantlab/portfolio/` | `test_c_1..5` (123) | **PASSED** |
| D | First-regime, return/risk forecast, robust optimizer, family evaluator — OOS-net baselines | `quantlab/models/`, `quantlab/research/` | `test_d_1,3,4,5,6`; real-data regime benchmark | **PASSED** (`no_alpha_claim`) |
| E | Experiment registry, config catalog, checksum snapshot durability, registry→dashboard bridge, Tier3 readiness gate, local serving/retraining/automated drift monitoring smoke evidence, production-tier evidence gate, governed production evidence probes, strict readiness proof CLI | `quantlab/mlops/`, `quantlab/showcase/`, `scripts/tier3_readiness_gate.py` | `test_e_1` (27); `test_tier3_readiness_gate_cli` (4); `e-tier3-readiness-gate`, `e-serving-smoke-health-gate`, `e-retraining-smoke-status-gate`, `e-tier3-production-tier-gate`, `e-automated-drift-status-gate`, `e-production-serving-endpoint-gate`, `e-production-retraining-status-gate`, and `e-tier3-cli-serving-validator` mutations killed; focused `experiment_registry` line coverage 100% | **PASSED** (local smoke only; production proof requires external payloads) |
| F | Showcase read API, Next.js dashboard, demo hardening, public/static showcase | `quantlab/showcase/`, `frontend/` | `test_f_1`; `frontend` npm test (23); static export | **CONDITIONAL** · `local_demo_only` |
| F/B/E ops | Browser visual diff, public-hosting probe, schedule run proof, scoped live snapshot write smoke, E drift report | `frontend/scripts/{browser-visual-smoke,probe-public-demo}.mjs`, `frontend/out/*`, `frontend/visual-baselines/browser-visual.png`, `.github/workflows/daily-snapshot.yml`, `scripts/daily_snapshot.py` | `browser-visual.png` `proven`; repo-baseline pixel diff `505 / 1,296,000`; probe HTTP 200; Actions `schedule` run `27392471359`; CR-B12 live write smoke; Python mutation 40/40 configured/killed + frontend 9/9 | **PASSED** (ops-visual-drift-artifacts + f-browser-pixel-baseline + b-live-scheduled-snapshot-proof + CR-B12/CR-B13/CR-B14/CR-B15/CR-B16) |
| G | Source-contract-first local alt-data loader (two optional slices) | `quantlab/data/` alt-data loader | `test_g_1` (7); PBT + mutation | **PASSED** (default-disabled) |
| Legacy | Arithmetic/geometric pyramid order sizing API | `invest_algorithms/` | `tests/test_algo_pyramid.py` | stable legacy baseline |

## Verification snapshot (2026-06-12)

| Gate | Command | Result |
|---|---|---|
| Python suite | `uv run pytest -q` | **223 passed** |
| Type check | `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py --ignore-missing-imports` | clean, 53 files |
| Architecture | `uv run lint-imports` | KEPT (72 files, 175 deps) |
| Frontend unit | `cd frontend && npm test` | 23 passed |
| Frontend supply chain | `npm audit --omit=dev` | 0 vulnerabilities |
| E registry line coverage | `uv run pytest --cov=quantlab.mlops.experiment_registry --cov-report=term-missing tests/quantlab/test_e_1_experiment_registry.py` | 27 passed; 100% line coverage |
| Python mutation | `uv run python scripts/run_mutation_spot_checks.py` | 40/40 configured mutations killed, including CR-B12 `snapshot-scoped-source-health`, CR-B13 `governance-stale-live-write-promotion`, CR-B14 `governance-stale-cr-b13-promotion`, CR-B15 `governance-stale-cr-b14-promotion`, and CR-B16 `governance-stale-cr-b15-promotion` |
| Browser visual | `cd frontend && npm run visual:browser` | `proven`; repo-baseline pixel diff `505 / 1,296,000` at threshold `0.001` |
| Public-hosting probe | `cd frontend && npm run probe:public-demo` | HTTP 200 `proven` |

## Open verification gaps (owned elsewhere)

- No CI-managed visual baseline history beyond the committed repo baseline —
  residual in `f-browser-pixel-baseline/review.md`.
- GitHub Actions autonomous `event=schedule` dry-run proof exists
  (`27392471359`); scheduled observer artifact records `status=proven`,
  `schedule_run_count=1`. CR-B12 separately proves scoped local live
  append-only write/skip mechanics, but broad default source availability
  remains unproven.
- Real-data backtest — deferred until ≥2 price assets accumulate
  (`run_vintage_slice.py`).
- Stooq source contract — `ISSUE-B3-001` (folded into CR-B7/B8/B9).

> Resolved 2026-06-11/12: live chromium-headless browser screenshot
> (`browser-visual.png` `proven`) and public-hosting probe (HTTP 200 `proven`)
> now exist; the earlier `not_proven` / `configured_not_observed` claims are
> superseded by `ops-visual-drift-artifacts/review.md`.

Doc reconciliation on 2026-06-12 surfaced **no new unowned issues**; all gaps
trace to an existing spec/CR/review or `ISSUE_LOG.md`.
