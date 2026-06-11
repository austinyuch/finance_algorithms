# Agent Guide

This file is the operating guide for coding agents working in this repository.

## First Reads

Start with these files before making non-trivial changes:

1. `.agents/specs/SPECS.md`
2. `.agents/specs/NEXT_STEPS.md`
3. The relevant spec folder under `.agents/specs/`
4. `quantlab/CORRECTNESS_CHECKLIST.md` for backtest correctness constraints
5. `quantlab/TESTS.md` for the test registry

## Project Shape

- `invest_algorithms/` is the legacy FastAPI pyramid calculator. Preserve existing behavior unless a task explicitly targets it.
- `quantlab/` is the newer research platform built through SDD specs.
- `.agents/specs/` is the source of truth for requirements, designs, reviews, and task history.
- `data/vintage/raw/` is append-only point-in-time data. Do not overwrite existing daily snapshots.

## Development Commands

Use `uv`:

```bash
uv sync
uv run pytest -q
uv run mypy quantlab/ --ignore-missing-imports
uv run lint-imports
```

Useful demo commands:

```bash
uv run python scripts/run_tsmc_hedge_slice.py
uv run python scripts/run_vintage_slice.py
uv run python scripts/daily_snapshot.py --dry-run
```

To run the legacy API:

```bash
cd invest_algorithms
uv run uvicorn api:app --host 127.0.0.1 --port 2224
```

## Architecture Rules

- `quantlab.engine` and `quantlab.data` must not import `torch`, `tensorflow`, `jax`, or `flax`.
- Keep ML framework code behind strategy adapters or environment-specific modules.
- Keep `quantlab/contracts/interfaces.py` structurally aligned with `.agents/specs/a0-backtest-foundation/contract/interfaces.py`.
- For schema changes, update the spec contract first, regenerate generated models if needed, and run tests plus mypy.
- Backtest results should report out-of-sample net metrics when used for leaderboard comparisons.
- PIT access must respect `available_date <= asof`; avoid any shortcut that can introduce lookahead.
- Preserve survivorship handling through listings data.
- Cost, tax, slippage, FX, and walk-forward behavior are correctness-sensitive. Add or update tests when touching them.

## Data Rules

- Vintage snapshots are immutable. If a daily file exists, skip it instead of overwriting it.
- `available_date` represents when the project captured or could have known a value.
- If historical data is reconstructed without a true vintage source, mark it approximate and keep strict/lenient behavior explicit.
- Snapshot fetching should degrade per source: one failed external source should not corrupt other captures.

## Testing Expectations

- For documentation-only edits, no full test run is required.
- For code touching `quantlab/engine`, `quantlab/data`, contracts, costs, metrics, or portfolio logic, run `uv run pytest -q`.
- For typed QuantLab changes, run `uv run mypy quantlab/ --ignore-missing-imports`.
- For imports involving `quantlab.engine` or `quantlab.data`, run `uv run lint-imports`.
- For legacy `invest_algorithms/` changes, run `uv run pytest -q tests/test_algo_pyramid.py` at minimum.

## Style Notes

- Prefer small, spec-aligned changes over broad refactors.
- Use existing local patterns before adding abstractions.
- Keep public behavior stable unless the relevant spec or user request calls for a change.
- Do not remove user-created files or untracked files unless explicitly asked.
- Keep docs and comments concise, but record decisions in the spec artifacts when they affect future work.
