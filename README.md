# Finance Algorithms

Finance Algorithms is a Python 3.13 research workspace with two related parts:

- `invest_algorithms/`: the legacy FastAPI service for arithmetic and geometric investment-pyramid order sizing.
- `quantlab/`: a portfolio-grade personal quant research lab with point-in-time data, vectorized backtesting, strategy comparison, local result tracking, and portfolio construction experiments.

The current product direction is tracked under `.agents/specs/`, with `SPECS.md` as the stable registry and `NEXT_STEPS.md` as the rolling handoff memo.

## Documentation

| Doc | Path | Audience |
|---|---|---|
| User manual (EN / 繁中) | `docs/manual/{en,zh-tw}/index.html` | Operators, researchers |
| Executive review | `docs/review/index.html` | Stakeholders |
| Feature catalog | `docs/FEATURES.md` | Everyone |
| Traceability bridge | `.agents/specs/RTM.md` | Verification context |

Regeneration steps live in `docs/MANUAL_GENERATION_GUIDE.md` and
`docs/REVIEW_GENERATION_GUIDE.md`. Readiness claims in these docs are copied from
`.agents/specs/**/review.md`; every model slice carries an explicit
`no_alpha_claim` boundary.

## Repository Map

| Path | Purpose |
|---|---|
| `invest_algorithms/` | Existing pyramid-calculation API and CSV output flow. Treat as the stable legacy baseline. |
| `quantlab/contracts/` | Protocols and generated Pydantic models used by the backtest foundation. |
| `quantlab/data/` | Point-in-time data providers, fixtures, and vintage snapshot loading. Must stay framework-agnostic. |
| `quantlab/engine/` | Vectorized backtest engine, metrics, and walk-forward logic. Must stay framework-agnostic. |
| `quantlab/strategies/` | Baselines, hedge strategy, buy-and-hold, and ML strategy adapters. |
| `quantlab/portfolio/` | Portfolio optimization and pyramid-entry adapter work from Epic C. |
| `quantlab/tracking/` | Local result store and leaderboard support. |
| `scripts/` | Reproducible demos and daily vintage data capture. |
| `data/vintage/raw/` | Append-only daily point-in-time snapshots. |
| `tests/` | Legacy API tests plus QuantLab spec tests and governance guards. |
| `.agents/specs/` | SDD artifacts, reviews, tasks, change requests, and program planning. |

## Setup

This repo uses `uv` and Python 3.13.

```bash
uv sync
```

If you are using an already-created virtualenv, the same commands below can be run through `uv run` without manually activating it.

## Run The API

The FastAPI app lives in `invest_algorithms/api.py`. Because that module uses legacy top-level imports, run Uvicorn from inside `invest_algorithms/`:

```bash
cd invest_algorithms
uv run uvicorn api:app --host 127.0.0.1 --port 2224
```

Useful environment variables:

| Variable | Default | Purpose |
|---|---:|---|
| `API_HOST` | `127.0.0.1` | Host reported by the root endpoint. |
| `API_PORT` | `2224` | Port reported by the root endpoint. |
| `API_CORS_ORIGINS` | empty | Comma-separated CORS allowlist. |
| `GLOBAL_LOG_LEVEL` | `INFO` | Python logging level. |

Main endpoints:

- `GET /api/pyramidArithmetic`
- `GET /api/pyramidGeometric`

Both endpoints accept budget, price range, transaction count, minimum unit, sizing parameter, initial unit, and `toCsv`.

## QuantLab Workflows

Run the synthetic TSMC hedge slice:

```bash
uv run python scripts/run_tsmc_hedge_slice.py
```

Inspect vintage data readiness and run the real-data OOS-net demo. Accumulated
vintage data is now sufficient, so the SP500 market-index slice runs a *computed*
candidate-vs-baseline comparison (fail-closed to `insufficient_data` / exit 2 on
thin, degenerate, or sampling-oversampled universes; `no_alpha_claim` throughout):

```bash
uv run python scripts/run_vintage_slice.py
uv run python scripts/run_real_data_oos_backtest.py   # SP500 index OOS-net comparison
```

Epic **H** adds a deep-learning research lab: a framework-free deterministic reference
MLP forecaster with a multi-framework backend registry (slice H-1) and a real **PyTorch**
training path (slice H-2, `scripts/run_dl_experiment.py --backend pytorch`) that degrades
honestly to the `reference` backend when torch is absent. Frameworks stay behind
`quantlab/models/dl/` (import-linter enforced); torch is an optional lane kept out of the
default lock; everything is `no_alpha_claim`.

A deep historical backfill (CR-B21) extends the research vintage back to **1990**,
so `approximate_availability=True` runs can span multiple business cycles
(dot-com, GFC, COVID, 2022). It is explicitly `is_approximate=true` research data
(NOT true point-in-time) and is **excluded by strict PIT mode**; `no_alpha_claim`
throughout:

```bash
uv run python scripts/backfill_history.py --since 1990-01-01   # idempotent; marks approximate
```

Capture today's append-only point-in-time snapshot:

```bash
uv run python scripts/daily_snapshot.py
```

Preview snapshot jobs without writing files:

```bash
uv run python scripts/daily_snapshot.py --dry-run
```

## Verification

Canonical test command:

```bash
uv run pytest -q
```

Type-check the QuantLab package:

```bash
uv run mypy quantlab/ --ignore-missing-imports
```

Check architecture contracts:

```bash
uv run lint-imports
```

The import-linter contract enforces that `quantlab.engine` and `quantlab.data` do not depend on `torch`, `tensorflow`, `jax`, or `flax`.

## Design Status

The implemented QuantLab foundation includes:

- A0 backtest foundation: contracts, PIT data provider, vectorized engine, metrics, walk-forward, parallel execution, and local tracking.
- Epic A TSMC hedge slice: hedge strategy, LSTM adapter, baselines, and leaderboard writeup.
- Epic B data platform: vintage snapshot loader, FRED price proxies, as-of alignment, and `pit_strictness`.
- Epic C portfolio core: optimizer, multi-period allocation, regime rebalance selector, pyramid-entry adapter, and integration leaderboard.
- Epic D first regime model: PIT-safe deterministic regime signal, OOS-net baseline comparison, and real-source-format benchmark helper with no-alpha claim boundary.

See `.agents/specs/SPECS.md` and `.agents/specs/NEXT_STEPS.md` before starting new feature work.
