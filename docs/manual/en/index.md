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

## Getting started / starter assets

```bash
uv sync                      # install Python 3.13 deps
uv run pytest -q             # sanity: expect 223 passed
cd frontend && npm install   # frontend deps (Next.js)
```

Canonical seed/sample data already committed:

- `data/vintage/raw/2026-06-09/`, `data/vintage/raw/2026-06-11/` — append-only
  point-in-time FRED + NOAA snapshots (immutable).
- `frontend/lib/showcase-fixture.ts` — the dashboard demo payload.
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
npm run smoke                  # local HTTP smoke on 127.0.0.1 (needs governed port)
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

> - Evidence Source: `live_screenshot` (chromium-headless) + `static_export`
> - Coverage Tier: `hybrid` · Readiness State: `CONDITIONAL` (`f-demo-hardening/review.md`); browser visual + public-hosting probe `PASSED` (`ops-visual-drift-artifacts/review.md`)
> - `MOCK_DOMINANT_EVIDENCE` — dashboard data is fixture-driven (`no_alpha_claim`).
> - Resolved: visual diff is repo-baseline pixel-backed (`505 / 1,296,000`
>   mismatched pixels at threshold `0.001`); GitHub Actions autonomous
>   `event=schedule` dry-run proof exists as run `27392471359`. Public-hosting
>   probe is `proven` HTTP 200, but the export's embedded readiness panel
>   remains conservative (`not_proven`) by contract.

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

## Visual gap inventory

**Gaps resolved since last check (2026-06-11 → 2026-06-12):**

- Test suite is now **223 passed** after moving PyTorch LSTM proof to the optional lane and adding current-governance stale-evidence guards; mypy is clean over **53** files; mutation spot checks are **40/40 configured/killed**, including root Torch dependency, stale governance evidence mutations through CR-B15 promotion drift, and CR-B12 scoped source-health overclaim protection.
- First committed manual/review documentation set under `docs/`.
- **Live browser screenshot now captured** (chromium-headless, `browser-visual.png`, status `proven`) — closes the prior "no browser screenshot" gap.
- **Public-hosting probe now proven** HTTP 200 (`public-hosting-probe.json`) — closes the prior `configured_not_observed` gap.
- **Visual diff now repo-baseline pixel-backed** (`browser-visual-diff.json`: `505 / 1,296,000` mismatched pixels at threshold `0.001`) — closes the prior hash-equality residual while allowing small text-rendering drift under the gate.

**Open visual gaps:**

| Gap | Severity | Source |
|---|---|---|
| No CI-managed visual baseline history beyond the repo baseline | Low | `f-browser-pixel-baseline/review.md` |
| Live append-only snapshot writes remain separate from dry-run schedule proof | Low | `b-live-scheduled-snapshot-proof/review.md` |
| Static export's readiness panel remains conservative (`not_proven`) by dashboard contract | Low | `frontend/out/index.html` |
| Vintage real-data backtest still deferred (<2 price assets) | Low | `run_vintage_slice.py` output |
| Stooq source blocked (`ISSUE-B3-001`) | Low | `ISSUE_LOG.md` |

See [`docs/review/index.html`](../../review/index.html) for the executive gap
analysis.
