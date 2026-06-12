# CR-A0 — Low-Frequency Event-Driven Replay

> Owner spec: [a0-backtest-foundation](../)
> Type: additive engine overlay; no Strategy/DataProvider contract break
> Status: Implemented(repo-side)
> Date: 2026-06-13

## Problem

A0 kept `config.engine="event_driven"` in the public backtest config but the engine raised `NotImplementedError`. That was an honest first-slice stub, but it became a stub-heavy surface once later specs depended on the A0 engine contract.

## Scope

This CR implements a low-frequency event replay path inside `VectorizedEngine`:

- `engine="event_driven"` is accepted.
- Optional `event_dates` selects explicit decision events.
- `event_dates` are sorted, deduplicated, and constrained to `start <= date <= end`.
- If `event_dates` is omitted, behavior falls back to the existing rebalance cadence.
- Existing cost, PIT, metric, walk-forward, and `rebalance_policy` behavior is reused.

This is not an intraday, tick, order-book, or execution simulator. Those remain future high-frequency scope.

## Evidence

- RED: `uv run pytest -q tests/quantlab/test_a0_2_engine.py -k event_driven` failed on the prior `NotImplementedError`.
- GREEN/REFACTOR: `uv run pytest -q tests/quantlab/test_a0_2_engine.py` -> 10 passed.
- Focused registry smoke: `uv run pytest -q tests/quantlab/test_a0_2_engine.py tests/test_mutation_spot_checks.py` -> 19 passed.
- Mutation: `uv run python scripts/run_mutation_spot_checks.py --only engine-event-driven-date-gate` -> killed. The mutation bypasses explicit `event_dates` and is rejected by the event replay example/PBT tests.

## Contract Updates

- `.agents/specs/a0-backtest-foundation/contract/schemas/backtest_config.json` now documents `event_dates`.
- `quantlab/contracts/_generated/backtest_config.py` includes optional `event_dates: list[date]`.

## Boundary

Readiness claim is limited to low-frequency event-date replay under the existing A0 backtest semantics. Production-grade high-frequency event simulation remains unimplemented and must be covered by a future spec/CR before being claimed.
