# Finance Algorithms — User Manual (English)

> Operating manual for the QuantLab research platform and the legacy pyramid
> calculator. Product surface: **Backend / Tool / CLI-dominant Hybrid**.
> Readiness verdicts are copied from `.agents/specs/**/review.md`; see
> [`EVIDENCE_METADATA_CONTRACT`](../../EVIDENCE_METADATA_CONTRACT.md).
>
> ⚠️ **Claim cap:** This is a personal, paper-only research lab. Every model
> slice declares `no_alpha_claim`. Nothing here is alpha-generating or
> production-deployed.

## Audience quick-nav

| You are… | Start at |
|---|---|
| A researcher running backtests | [Flow 1 — Run the hedge slice](#flow-1--run-the-tsmc-hedge-slice) |
| A data operator capturing snapshots | [Flow 2 — Daily vintage snapshot](#flow-2--daily-vintage-snapshot) |
| A reviewer reading the dashboard | [Flow 3 — Showcase dashboard](#flow-3--showcase-dashboard) |
| A legacy API user | [Flow 4 — Pyramid calculator API](#flow-4--legacy-pyramid-calculator-api) |
| A researcher running a real-data OOS-net backtest | [Flow 5 — Real-data OOS-net backtest](#flow-5--real-data-oos-net-backtest) |
| A researcher studying multiple business cycles | [Flow 6 — Historical backfill & multi-cycle study](#flow-6--historical-backfill--multi-cycle-study-cr-b21) |
| A researcher training a deep model (real PyTorch) | [Flow 7 — Deep-learning experiment](#flow-7--deep-learning-experiment-epic-h-real-pytorch) |

## Getting started / starter assets

```bash
uv sync                      # install Python 3.13 deps
uv run pytest -q             # sanity: expect 432 passed, 2 skipped
cd frontend && npm install   # frontend deps (Next.js)
```

Canonical seed/sample data already committed:

- `data/vintage/raw/2026-06-09/`, `data/vintage/raw/2026-06-11/` — append-only
  point-in-time FRED + NOAA snapshots (immutable).
- `frontend/lib/showcase-payload.json` — generated dashboard payload with `sourceMetadata.source=local_result_store`.
- `frontend/out/showcase.json` — exported dashboard payload (downloadable).

---

## Flow 1 — Run the TSMC hedge slice

**Who/when:** A researcher wants a reproducible OOS-net leaderboard comparing a
hedge strategy against dumb baselines.

```bash
uv run python scripts/run_tsmc_hedge_slice.py
```

Live output (`assets/backend-hedge-slice-01-leaderboard.txt`):

```
strategy          OOS net Sharpe
--------------------------------
BuyAndHold                0.3911
HedgeStrategy             0.3528
StaticWeights             0.2759
RandomStrategy           -0.0092
```

**How to read it:** strategies are ranked by **out-of-sample net** Sharpe (after
costs). `RandomStrategy` is the sanity floor. In the default UAT/runtime env the
optional PyTorch LSTM lane is not installed, so this transcript contains hedge
and baseline strategies only. The slice runs on **synthetic** cointegrated data —
it proves the pipeline is correct, not that the hedge earns money.

> - Evidence Source: `live_command_output`
> - Coverage Tier: `hybrid` · Readiness State: `PASS` (`a-tsmc-hedge-slice/review.md`)
> - `MOCK_DOMINANT_EVIDENCE` — synthetic data; `no_alpha_claim`.

---

## Flow 2 — Daily vintage snapshot

**Who/when:** A data operator captures today's point-in-time macro/price data
without overwriting prior days (snapshots are immutable).

Preview the jobs without writing or hitting the network:

```bash
uv run python scripts/daily_snapshot.py --dry-run
```

Live output (`assets/backend-daily-snapshot-01-dryrun.txt`, truncated):

```
[snapshot] available_date=2026-06-11  out=.../data/vintage/raw/2026-06-11  jobs=22  (DRY-RUN)
  DRY  fred_FEDFUNDS
  DRY  fred_SP500
  DRY  yahoo_2330.TW
  DRY  yahoo_idx_TWII
  DRY  noaa_oni
[snapshot] done. ok=0 skip=0 fail=0
```

Capture for real (writes append-only files, degrades per source):

```bash
uv run python scripts/daily_snapshot.py
uv run python scripts/daily_snapshot.py --report-json > report.json   # CR-B11 machine-readable
uv run python scripts/snapshot_ops_gate.py report.json                # validate the run
```

**How to read it:** 22 jobs span FRED series, Yahoo fallback tickers, and NOAA
ONI. A single failing source must not corrupt the others. **Stooq is
opt-in/blocked** (`ISSUE-B3-001`); Yahoo fallback is live-proven for `2330.TW`
and `^TWII`.

> - Evidence Source: `live_command_output`
> - Coverage Tier: `hybrid` · Readiness State: `PASS` repo-side (`b-data-platform/review.md`)
> - `CROSS_SPEC_DEMO_DEPENDENCY` — external sources; Stooq blocked by default.

### Vintage readiness check

```bash
uv run python scripts/run_vintage_slice.py
```

```
macro series : 4  ['CPIAUCSL', 'FEDFUNDS', 'GDPC1', 'UNRATE']
price assets : 1  ['SP500']
[readiness] price assets < 2 → backtest skipped; proxies accumulate from next snapshot.
```

This is honest readiness reporting: until ≥2 real price assets accumulate, the
real-data backtest defers rather than fabricating a result.

---

## Flow 3 — Showcase dashboard

**Who/when:** A reviewer inspects the QuantLab leaderboard, allocation/regime,
rebalance dates, and experiment registry in a browser.

Regenerate the static export and (optionally) serve locally:

```bash
cd frontend
npm run export:public-demo     # writes frontend/out/{index.html,showcase.json,...}
npm run smoke                  # local HTTP smoke on an auto-selected 127.0.0.1 port
```

The committed export renders five panels: **Leaderboard** (OOS-net Sharpe,
ForecastAllocationStrategy 1.21 vs StaticWeights baseline 0.74), **Allocation /
Regime** (risk_on, conf 0.60; GROWTH 62% / STEADY 38%), **Rebalance** (3 dates),
**Experiment Registry** (`registry_only`, `no_alpha_claim`), and **Evidence**
(`local_demo_only`).

Downloadable payload: [`frontend/out/showcase.json`](../assets/showcase.json).

A real chromium-headless screenshot is captured at desktop-1440×900
(`frontend/out/browser-visual.png`, status `proven`). Note the static export
ships semantic HTML **without** the app stylesheet, so the screenshot is
intentionally unstyled — it proves render + content, not visual polish. The live
`npm run dev` app applies `app/globals.css`.

> - Evidence Source: `live_screenshot` (chromium-headless) + `static_export` + `canonical_local_result_store`
> - Coverage Tier: `hybrid` · Readiness State: `CONDITIONAL` (`f-demo-hardening/review.md`); browser visual `PASSED`; current branch-local public hosting is `configured_not_observed` at expected `dataHash 5d742c80…` until Pages serves the refreshed artifact (`docs/public-hosting-probe.json`)
> - Source Ref: `.agents/specs/f-demo-hardening/review.md`, `.agents/specs/f-public-static-showcase/review.md`, `docs/deployment-manifest.json`
> - Dashboard data is generated from a local `LocalResultStore` / `ExperimentRegistry` scenario (`no_alpha_claim`, `local_demo_only`), not a live backend service.
> - Resolved: visual diff is repo-baseline pixel-backed (`0 / 1,296,000`
>   mismatched pixels at threshold `0.001`) and the export readiness panel now
>   reports `visualRegression=proven` (CR-FPS-009). Public-hosting probe currently
>   observes HTTP 200 plus manifest-contract metadata but a mismatched deployed hash
>   (`status=configured_not_observed`, expected `dataHash 5d742c80…`); freshness is
>   deterministic and stale evidence downgrades rather than crashing (CR-FPS-011).
>   The dashboard payload's own `publicHosting` self-claim **stays `not_proven`**
>   by design — a static artifact cannot self-claim its deployment; the `proven`
>   status lives only in the observed probe/manifest and is point-in-time.

---

## Flow 4 — Legacy pyramid calculator API

**Who/when:** A user sizes arithmetic/geometric investment-pyramid orders.

```bash
cd invest_algorithms
uv run uvicorn api:app --host 127.0.0.1 --port 2224
```

Endpoints:

- `GET /api/pyramidArithmetic`
- `GET /api/pyramidGeometric`

Both accept budget, price range, transaction count, minimum unit, sizing
parameter, initial unit, and `toCsv`. This module is the **immutable legacy
baseline** — preserved unchanged.

> - Evidence Source: `report_artifact` (`tests/test_algo_pyramid.py`)
> - Coverage Tier: `hybrid` · Readiness State: stable legacy baseline.

---

## Flow 5 — Real-data OOS-net backtest

**Who/when:** A researcher runs a backtest on **real point-in-time vintage
data** (not synthetic), comparing a candidate against a dumb baseline, ranked by
out-of-sample **net** Sharpe. Since the CR-B21 deep backfill (see Flow 6), the
default approximate run now selects a **12-asset co-temporal universe** instead
of the prior SP500-only slice.

```bash
uv run python scripts/run_real_data_oos_backtest.py --out /tmp/rdo-demo.json
```

Live output (`assets/real-data-oos-demo-01-run.txt`; full artifact in
`assets/real-data-oos-demo-02-artifact.json`):

```
EXIT=0
status            = computed
asset_set         = 12 co-temporal assets
                    (^GSPC, ^IXIC, SPY, AGG, TLT, GLD, DBC, BTC-USD, 2330.TW, ^TWII, TWD=X, SP500)
availability_mode = approximate_event_date   (NOT true PIT)
metric_authority  = out_of_sample_net_only
asof_window       = 2016-06-13 .. 2026-06-12   (co-temporal window; deep 1990+ history
                    is available — see Flow 6 — but the shared window is pinned by the
                    youngest asset, BTC-USD)
rows (ranked OOS-net Sharpe):
  BuyAndHold        1.2664   (baseline)
  RandomStrategy    1.0860
```

**How to read it:** this composes the existing A0 engine + PIT vintage provider
over **real** multi-asset data. The candidate (a cross-sectional `RandomStrategy`
when ≥2 assets qualify) does not beat buy-and-hold net of cost. This is
**mechanism evidence on real source data — not a strategy verdict and not an
alpha claim**. The CLI uses `approximate_event_date` availability (vintage made
visible to historical as-ofs); the artifact records that mode explicitly because
it is **NOT true PIT** and may introduce lookahead.

### Fail-closed honesty guards

The CLI never emits a misleading `computed`. Two guards fail closed (exit 2,
`status=insufficient_data`):

```
# CR-RDO-004 sampling-frequency oversampling (mixed daily+monthly universe,
# monthly rebalance would forward-fill stale prices into fabricated flat returns)
[fail-closed] oversampled real-data OOS: rebalance cadence 'monthly' is finer ...
  → reason=oversampled_vs_native_frequency   EXIT=2

# Degeneracy (true-PIT single-capture data invisible to historical as-ofs → flat OOS)
[fail-closed] degenerate real-data OOS: all strategy OOS net return series are flat ...
  → reason=degenerate_flat_oos   EXIT=2
```

The default run's 12 co-temporal assets are all daily-native
(`coarsest_cadence=daily`, `rebalance=monthly`), so it passes both guards and
stays `computed`.

> - Evidence Source: `live_command_output` + `report_artifact` (live 12-asset
>   capture `assets/real-data-oos-demo-02-artifact.json`; the spec's earlier
>   single-index canonical run is committed at
>   `.agents/specs/real-data-oos-backtest/reports/real-data-oos-artifact.json`,
>   checksum `421c7fd2…`)
> - Coverage Tier: `hybrid` · Readiness State: `PASS` — *Implemented · Review
>   PASSED* (`real-data-oos-backtest/review.md`); live-demo readiness `not_assessed`
>   (CLI/library slice, no served surface)
> - Source Ref: `.agents/specs/real-data-oos-backtest/review.md`,
>   `.../change-requests/cr-rdo-003-market-index-availability.md`,
>   `.../change-requests/cr-rdo-004-sampling-frequency-guard.md`,
>   `.../b-data-platform/change-requests/cr-b21-historical-backfill.md`
> - Captured: live CLI re-execution on 2026-06-15 over real vintage data — the
>   computed 12-asset co-temporal run (universe widened from SP500-only by the
>   CR-B21 backfill) plus both fail-closed paths (degeneracy, CR-RDO-004
>   sampling-frequency).
> - `MOCK_DOMINANT_EVIDENCE` — real CLI output over real but local-only vintage
>   data with `availability_mode=approximate_event_date` (not true PIT)
>   availability (not true PIT); `no_alpha_claim`, mechanism not strategy verdict.

---

## Flow 6 — Historical backfill & multi-cycle study (CR-B21)

**Who/when:** A researcher wants to study **multiple business cycles** (the
2000 dot-com crash, 2008 GFC, COVID, 2022) — coverage the few real-time daily
snapshots can't provide. CR-B21 backfills deep history (Yahoo `period1=1990`,
full FRED series, NOAA ONI) into `data/vintage/raw/backfill-1990-01-01/`.

```bash
uv run python scripts/backfill_history.py --since 1990-01-01   # idempotent
```

**Honesty boundary (non-negotiable):** history fetched today is **NOT true
point-in-time** — every record is `is_approximate=true` + `backfill=true`
(`available_date`=capture date; FRED macro is latest-*revised*). **Strict PIT
mode excludes the backfill entirely**; only `approximate_availability=True`
(research mode) exposes it, under `no_alpha_claim`. It never makes anything
true-PIT and never asserts alpha.

Manifest + deep multi-cycle backtest (`assets/backend-historical-backfill-01-demo.txt`):

```
_backfill_manifest.json : approximate=true, claim_boundary=no_alpha_claim,
                          since=1990-01-01, ok+skip=24/24, fail=0
residual completed (idempotent re-run, 2026-06-16) — the 6 FRED rate/FX
series captured: DGS10, DGS2, T10Y2Y, NASDAQCOM, DCOILWTICO, DEXTAUS
  → T10Y2Y available, so the regime family now runs full-feature

deep {^GSPC, ^IXIC} 1990-01-02 → 2026-06-12 (437 months), status=computed:
  BuyAndHold         oos_net_sharpe = 0.7007  (baseline)
  SmaTimingStrategy  oos_net_sharpe = 0.2264
```

**Data validation** (`assets/backend-historical-backfill-02-drawdowns.txt`) — the
backfilled history is not just *present* but historically *correct*; peak-to-trough
drawdowns match the real record:

| Regime | Index | Max drawdown |
|---|---|---|
| Dot-com crash | `^GSPC` / `^IXIC` | −49.1% / −77.9% |
| Global Financial Crisis | `^GSPC` | −56.8% |
| COVID crash | `^GSPC` | −33.9% |
| 2022 rate-hike bear | `^GSPC` | −25.4% |

`^GSPC` coverage: **9,179 daily rows, 1990-01-02 → 2026-06-12**.

> - Evidence Source: `report_artifact` (`_backfill_manifest.json`,
>   `cr-b21-deep-cycle-1990-oos-artifact.json`) + `live_command_output`
> - Coverage Tier: `hybrid` · Readiness State: `PASS` — *Implemented · Review
>   PASSED (repo-side + live run)* (`b-data-platform/review.md`, CR-B21)
> - Source Ref: `.agents/specs/b-data-platform/change-requests/cr-b21-historical-backfill.md`,
>   `.agents/specs/b-data-platform/review.md`
> - Captured: live CLI run on 2026-06-15, residual completed by idempotent re-run
>   2026-06-16; all 24/24 sources captured, fail=0 (the 6 previously FRED-throttled
>   rate/FX series, incl. `T10Y2Y`, are now present → regime family full-feature).
> - `MOCK_DOMINANT_EVIDENCE` — real fetched history but `is_approximate=true`
>   research data (NOT true PIT), strict-excluded; `no_alpha_claim`.

---

## Flow 7 — Deep-learning experiment (Epic H, real PyTorch)

**Who/when:** A researcher wants to train a deep model end-to-end through the
backtest engine and compare it to a dumb baseline on out-of-sample net metrics —
the "set parameters → run → see results" mechanism.

```bash
uv run python scripts/run_dl_experiment.py --backend pytorch \
  --symbols '^GSPC' '^IXIC' --hidden-units 8 --lookback 6 --epochs 40 --seed 0 \
  --out out/dl-demo/exp-torch-gspc-ixic.json --viz out/dl-demo/exp-torch-gspc-ixic.svg
```

Live output (`assets/backend-dl-experiment-01-demo.txt`):

```
status=computed  backend=pytorch  experiment_id=1e893d7d…
learning curve : 0.9997 → 0.9975  (40 epochs, monotone decreasing → model trained)

OOS-net leaderboard (ranked OOS-net only; baseline visible):
  StaticWeights (buy & hold)        oos_net_sharpe = +0.1292   maxDD = −65.4%   [baseline]
  DeepForecastAllocationStrategy    oos_net_sharpe = +0.0919   maxDD = −71.0%   [model]
```

**How to read it:** with PyTorch installed, the `pytorch` backend trains the MLP
for real (torch autograd, float64) behind a lazy backend boundary — the
engine/data core never imports a framework. The trained model honestly
**under-performs** buy-and-hold on OOS-net Sharpe: that is the point —
`no_alpha_claim`, mechanism evidence, not a strategy verdict. Without torch the
same call degrades to the deterministic `reference` backend (never raises). The
deep history is the CR-B21 approximate backfill (NOT true PIT; strict mode
excludes it; research mode only). A self-contained performance-report SVG is
written alongside the artifact.

> - Evidence Source: `report_artifact` (`out/dl-demo/exp-torch-gspc-ixic.json`,
>   checksum `b73b21e9…`) + `live_command_output`
> - Coverage Tier: `hybrid` · Readiness State: `PASS` — *Implemented · Review
>   PASSED (repo-side + torch UAT)* (`h-deep-learning-real-training/review.md`)
> - `MOCK_DOMINANT_EVIDENCE` — real torch training over `is_approximate=true`
>   research data (NOT true PIT); optional torch lane; `no_alpha_claim`.

---

## Visual gap inventory

**Render validation (2026-06-15, headless chromium `1440×2600`):** this manual
(en/zh) and the executive review render cleanly — sidebar nav, hero, terminal
code blocks, evidence captions and warning badges (`PASS`,
`MOCK_DOMINANT_EVIDENCE`) all intact, no broken CSS or missing assets. The
review's UX-flow diagram is now a **self-contained inline SVG** (renders offline
/ `file://`, no CDN or client-side JS, with an accessible text-equivalent
caption), so there is no remaining visual residual.

**Gaps resolved since last check (CR-B21 / CR-RDO-004 / CR-FBP-001 / CR-FPS-009/010/011, as of 2026-06-15):**

- **Deep historical backfill landed (CR-B21) — NEW Flow 6.** The research vintage
  now reaches **1990** (Yahoo deep indices + full FRED + NOAA, `is_approximate=true`,
  strict-excluded, 24/24 sources, fail=0). It enables a real multi-cycle backtest (deep
  {^GSPC,^IXIC} 1990→2026, 437 months, `computed`) and validates against the real
  record (dot-com −49%/−78%, GFC −57%, COVID −34%, 2022 −25%). Flow 5's default run
  consequently widened from SP500-only to a 12-asset co-temporal universe.
  `no_alpha_claim`; the residual 6 FRED rate/FX series (incl. `T10Y2Y`) were
  captured by an idempotent re-run → regime family now full-feature.

- **Front + back services live-verified (2026-06-15).** The Next.js dashboard
  smoke passed against an ephemeral `next start` (served `/` and the real
  `/api/showcase` payload — see `assets/frontend-smoke-01.txt`), and the legacy
  FastAPI pyramid calculator returned a real arithmetic-pyramid response (see
  `assets/legacy-api-01.txt`), so the "started services" evidence is now
  live_command_output rather than only the committed payload.

- **Sampling-frequency honesty gap closed (CR-RDO-004).** The real-data OOS
  library now estimates each asset's native cadence and **fails closed**
  (`reason=oversampled_vs_native_frequency`) when the rebalance cadence is finer
  than the coarsest selected asset, instead of silently forward-filling stale
  prices into fabricated flat returns that inflate Sharpe. The default run (now
  12 co-temporal daily-native assets) is unaffected and stays `computed` (see Flow 5).
- **Browser pixel baseline now real and re-pin-tolerant (CR-FBP-001).** The
  stale-baseline-hash guard fires only when `baselineHash != currentHash`, so a
  legitimate deterministic re-pin (`baselineHash == currentHash`,
  `mismatchedPixels == 0`) no longer blocks honest UI changes; the tolerant
  pixel-diff threshold gate is unchanged.
- **Dashboard visual readiness wired through (CR-FPS-009).** The export's
  readiness panel now reports `visualRegression=proven` from repo-side browser
  visual diff evidence (previously unwired).
- **Public hosting remains deploy-gated for the refreshed artifact.**
  The current committed manifest expects `dataHash 5d742c80…`, while the live
  probe still observes an older deployed hash (`16486e36…`), so branch-local
  parity is `configured_not_observed` / `mismatched`
  (`docs/deployment-manifest.json`, `docs/public-hosting-probe.json`, observed
  `2026-06-18T02:52Z`). Older CR-B21 hosting proof at `0f170441…` remains
  historical point-in-time evidence only. The dashboard payload's own
  `publicHosting` self-claim stays `not_proven` by design.
- **Hosting-freshness time-bomb removed (CR-FPS-011).** Freshness is now
  classified deterministically against an injected `asof` (no hidden wall-clock);
  stale committed evidence **downgrades** to `configured_not_observed` rather than
  crashing the build/suite ~24h after a re-prove.

**Gaps resolved earlier (2026-06-11 → 2026-06-13):**

- Default-root test suite is now **432 passed, 2 skipped**; the **430 passed** count remains only the H-2 torch-enabled UAT / optional-lane evidence. Mypy is clean over the current scoped `quantlab/` source set, and mutation spot checks remain **118/118 configured/killed**, including the CR-RDO-004 sampling-frequency guard, root Torch dependency, stale governance evidence mutations plus the non-self-staling promotion-boundary guard, local-first CI default and skill-body guards, governance refresh review stale-evidence regression, CR-FPS public-hosting drift guards, stakeholder and app payload copy drift, import-linter count/formalization drift, governance registry row-count drift, E production evidence gates, CR-B12 scoped source-health overclaim protection, CR-B18 broad source-quorum overclaim protection, CR-B19 proof replay protection, and CR-B20 Stooq proof exit/file replay protection. Frontend mutation is now **26/26 killed**, including `frontend-smoke-html-api-parity-regression`, so local smoke covers HTML/API payload parity instead of only API payload validity.
- First committed manual/review documentation set under `docs/`.
- **Live browser screenshot now captured** (chromium-headless, `browser-visual.png`, status `proven`) — closes the prior "no browser screenshot" gap.
- **Public-hosting probe records HTTP 200 and deployed manifest contract metadata** (`public-hosting-probe.json`); after CR-FPS-006 the regenerated local result-store payload has a new `dataHash`, so branch-local deployment parity is intentionally `configured_not_observed` until Pages serves the refreshed artifact.
- **Visual diff now repo-baseline pixel-backed** (`browser-visual-diff.json`: `0 / 1,296,000` mismatched pixels at threshold `0.001`) — closes the prior hash-equality residual while allowing small text-rendering drift under the gate.

**Open visual gaps:**

| Gap | Severity | Source |
|---|---|---|
| No CI-managed visual baseline history beyond the repo baseline | Low | `f-browser-pixel-baseline/review.md` |
| Stooq source contract remains separate from FRED/Yahoo/NOAA source-quorum proof | Low | `b-data-platform/change-requests/cr-b19-source-quorum-live-proof.md` |
| Dashboard payload `publicHosting` self-claim stays `not_proven` by contract; current committed probe/manifest parity is `configured_not_observed` until Pages serves `dataHash 5d742c80…` | Low | `frontend/out/index.html`, `docs/public-hosting-probe.json` |
| Real-data OOS uses `approximate_event_date` (not true PIT); a co-temporal multi-asset default universe with true vintage history is the follow-up | Low | `real-data-oos-backtest/review.md` |
| Vintage co-temporal multi-asset readiness still accumulating (single-capture FRED; daily-vintage backtest deferred) | Low | `run_vintage_slice.py` output |
| Stooq source blocked (`ISSUE-B3-001`) | Low | `ISSUE_LOG.md` |

See [`docs/review/index.html`](../../review/index.html) for the executive gap
analysis.
