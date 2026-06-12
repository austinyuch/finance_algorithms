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
| A0 | Lookahead-safe vectorized backtest with OOS-net metrics, walk-forward, parallel run, tracking | `quantlab/{contracts,data,engine,parallel,tracking}` | `test_a0_0..5`; CR-A0 regime scheduling; current mutation spot checks 29/29 configured | **PASSED** |
| A | TSMC hedge slice ranked vs baselines; optional PyTorch LSTM lane isolated from default runtime | `quantlab/strategies/`, `scripts/run_tsmc_hedge_slice.py`, `pyproject.toml`, `uv.lock` | `test_a_1,3,4,5`; optional `test_a_2_lstm`; `test_dependency_security.py`; `root-torch-default-dependency` mutation | **PASSED** (synthetic; `no_alpha_claim`; default env no Torch) |
| Governance | Current-state evidence freshness and false-green prevention | `tests/quantlab/test_governance_guards.py`; `scripts/run_mutation_spot_checks.py`; `.agents/specs/governance-evidence-refresh/` | stale governance guard 7 passed; governance mutations killed; Dependabot #7 fixed; current registries use 200/1 and visual diff `505 / 1,296,000` | **PASSED** (`governance-evidence-refresh`) |
| B | PIT vintage loader, FRED proxies, as-of alignment, `pit_strictness`, source-health, snapshot run report + ops gate + scheduled run observer | `quantlab/data/`, `scripts/{daily_snapshot,snapshot_ops_gate,scheduled_run_observer}.py`, `.github/workflows/daily-snapshot.yml` | `test_b_1..5`; `test_daily_snapshot.py` (26); CR-B5/B7..B11; Actions run `27387041974`; scheduled observation `status=pending`, `schedule_run_count=0` | **PASSED (repo-side + workflow_dispatch + fail-closed observer)**; residual `ISSUE-B3-001` (Stooq), cron event proof pending |
| C | Optimizer, multi-period allocation, regime rebalance selector, pyramid-entry adapter | `quantlab/portfolio/` | `test_c_1..5` (123) | **PASSED** |
| D | First-regime, return/risk forecast, robust optimizer, family evaluator — OOS-net baselines | `quantlab/models/`, `quantlab/research/` | `test_d_1,3,4,5,6`; real-data regime benchmark | **PASSED** (`no_alpha_claim`) |
| E | Experiment registry, config catalog, checksum snapshot durability, registry→dashboard bridge, Tier3 readiness gate, local serving smoke evidence | `quantlab/mlops/`, `quantlab/showcase/` | `test_e_1` (17); `e-tier3-readiness-gate` and `e-serving-smoke-health-gate` mutations killed; trace 97.3% | **PASSED** (local smoke only; gate fail-closed) |
| F | Showcase read API, Next.js dashboard, demo hardening, public/static showcase | `quantlab/showcase/`, `frontend/` | `test_f_1`; `frontend` npm test (23); static export | **CONDITIONAL** · `local_demo_only` |
| F/B/E ops | Browser visual diff, public-hosting probe, schedule run proof, E drift report | `frontend/scripts/{browser-visual-smoke,probe-public-demo}.mjs`, `frontend/out/*`, `frontend/visual-baselines/browser-visual.png`, `.github/workflows/daily-snapshot.yml` | `browser-visual.png` `proven`; repo-baseline pixel diff `505 / 1,296,000`; probe HTTP 200; Actions `workflow_dispatch` run `27387041974`; Python mutation 29/29 configured + frontend 9/9 | **PASSED** (ops-visual-drift-artifacts + f-browser-pixel-baseline + b-live-scheduled-snapshot-proof) |
| G | Source-contract-first local alt-data loader (two optional slices) | `quantlab/data/` alt-data loader | `test_g_1` (7); PBT + mutation | **PASSED** (default-disabled) |
| Legacy | Arithmetic/geometric pyramid order sizing API | `invest_algorithms/` | `tests/test_algo_pyramid.py` | stable legacy baseline |

## Verification snapshot (2026-06-12)

| Gate | Command | Result |
|---|---|---|
| Python suite | `uv run pytest -q` | **200 passed, 1 skipped** |
| Type check | `uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py scripts/scheduled_run_observer.py --ignore-missing-imports` | clean, 52 files |
| Architecture | `uv run lint-imports` | KEPT (71 files, 174 deps) |
| Frontend unit | `cd frontend && npm test` | 23 passed |
| Frontend supply chain | `npm audit --omit=dev` | 0 vulnerabilities |
| Python mutation | `uv run python scripts/run_mutation_spot_checks.py --only e-serving-smoke-health-gate`; full suite configured in `scripts/run_mutation_spot_checks.py` | targeted E serving health-gate mutation killed; current suite contains 29/29 configured mutations |
| Browser visual | `cd frontend && npm run visual:browser` | `proven`; repo-baseline pixel diff `505 / 1,296,000` at threshold `0.001` |
| Public-hosting probe | `cd frontend && npm run probe:public-demo` | HTTP 200 `proven` |

## Open verification gaps (owned elsewhere)

- No CI-managed visual baseline history beyond the committed repo baseline —
  residual in `f-browser-pixel-baseline/review.md`.
- GitHub Actions `workflow_dispatch` proof exists (`27387041974`); scheduled
  observer artifact records `status=pending`, `schedule_run_count=0`; autonomous
  cron-triggered `event=schedule` proof remains pending.
- Real-data backtest — deferred until ≥2 price assets accumulate
  (`run_vintage_slice.py`).
- Stooq source contract — `ISSUE-B3-001` (folded into CR-B7/B8/B9).

> Resolved 2026-06-11/12: live chromium-headless browser screenshot
> (`browser-visual.png` `proven`) and public-hosting probe (HTTP 200 `proven`)
> now exist; the earlier `not_proven` / `configured_not_observed` claims are
> superseded by `ops-visual-drift-artifacts/review.md`.

Doc reconciliation on 2026-06-12 surfaced **no new unowned issues**; all gaps
trace to an existing spec/CR/review or `ISSUE_LOG.md`.
