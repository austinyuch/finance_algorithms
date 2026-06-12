# FEATURES.md — Finance Algorithms Feature Catalog

> Stable feature inventory consumed by `docs/manual/` and `docs/review/`
> generation. Readiness columns are **copied** from the owning
> `.agents/specs/**/review.md`; they are never derived from task counts or
> `NEXT_STEPS.md` hints. See [`SPECS.md`](../.agents/specs/SPECS.md) for the
> dependency map and [`EVIDENCE_METADATA_CONTRACT.md`](./EVIDENCE_METADATA_CONTRACT.md)
> for evidence semantics.

Product shape: **Backend / Tool / CLI-dominant Hybrid** — a personal,
paper-only quant research lab. Success is defined as *methodology honesty +
experimentation capability*, **not** alpha. Every model slice declares
`no_alpha_claim`.

## Feature inventory

| # | Feature | Epic | Surface | Live-Demo Readiness | Evidence Source | Key boundary |
|---|---|---|---|---|---|---|
| 1 | **Vectorized backtest foundation** (PIT data, engine, metrics, walk-forward, parallel run, local tracking) | A0 | CLI / library | PASSED | unit tests + mutation | Framework-agnostic; MLflow backend deferred |
| 2 | **TSMC hedge slice** (hedge strategy, LSTM adapter, baselines, leaderboard) | A | CLI demo | PASSED | `scripts/run_tsmc_hedge_slice.py`, 83 tests | Synthetic data only; no real alpha |
| 3 | **Data platform** (vintage PIT loader, FRED price proxies, as-of alignment, `pit_strictness`, source-health, snapshot run report + ops gate) | B | CLI / data | PASSED (repo-side) | `scripts/daily_snapshot.py`, `snapshot_ops_gate.py` | Stooq opt-in/blocked (`ISSUE-B3-001`); Yahoo fallback live-proven for `2330.TW`/`^TWII` |
| 4 | **Portfolio core** (optimizer, multi-period allocation, regime rebalance selector, pyramid-entry adapter) | C | library | PASSED | `test_c_1..5` | maxDD bound is ex-post; additive to legacy `algo_pyramid` |
| 5 | **Model families** (first-regime classifier, return/risk forecaster, robust optimizer, family evaluator) | D | library / CLI | PASSED | `test_d_*`, OOS-net baselines | Deterministic methodology slices; `no_alpha_claim` |
| 6 | **MLOps E-lite** (experiment registry, config catalog, checksum snapshot durability, registry→dashboard bridge) | E | library / read API | PASSED | `test_e_1`, registry JSONL | Registry-only; no serving/retraining/drift |
| 7 | **Showcase read API + dashboard** (ShowcaseReadAPI, dashboard summary, HTML render, Next.js app, `/api/showcase`, demo hardening, static showcase) | F | read API + Web UI | CONDITIONAL · `local_demo_only` | `frontend/` static export, `npm test` | Fixture-driven; see ops-visual-drift residuals below |
| 7b | **Ops visual drift artifacts** (chromium-headless browser screenshot, browser visual diff gate, public-hosting probe, schedule run proof, E drift report) | F/B/E ops | Web UI + ops | PASSED | `browser-visual.png`, `browser-visual-diff.json`, probe HTTP 200 | Visual diff is repo-baseline pixel-backed (`0 / 1,296,000` pixels mismatched at threshold `0.001`); no live *scheduled* run artifact yet |
| 8 | **Alt-data slices** (source-contract-first local CSV loader, two optional slices) | G | library | PASSED | `test_g_1` | Optional, default-disabled, `available_date <= asof` |
| 9 | **Legacy pyramid calculator** (arithmetic + geometric order sizing) | — | FastAPI | stable legacy baseline | `tests/test_algo_pyramid.py` | Immutable; preserved unchanged |

## Latest authoritative gate evidence (2026-06-12)

- `uv run pytest -q` → **190 passed** (up from 163 at the prior memo)
- `uv run mypy quantlab/ --ignore-missing-imports` → clean, **50 source files**
- `uv run lint-imports` → engine/data framework-agnostic **KEPT** (71 files, 174 deps)
- `frontend` `npm test` → **23 passed**; `npm audit --omit=dev` → **0 vulnerabilities**
- Python mutation spot checks → **22/22 killed**; frontend coverage **91.42%**, mutation 9/9 killed
- `npm run visual:browser` → chromium-headless screenshot `proven`
  (`frontend/out/browser-visual.png`); `npm run probe:public-demo` → **HTTP 200 proven**
  (`frontend/out/public-hosting-probe.json`), per
  `.agents/specs/ops-visual-drift-artifacts/review.md`

These counts are the basis for the "gaps resolved since last check" sections of
the manual and review. Visual diff is now repo-baseline pixel-backed; the
remaining ops residual is that no live *scheduled* GitHub Actions run artifact
has been captured yet.
