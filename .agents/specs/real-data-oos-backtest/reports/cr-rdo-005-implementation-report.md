# CR-RDO-005 — Implementation Report

> Multi-cycle, multi-asset OOS-net evaluation across D model families. Repo-side
> closure evidence. `no_alpha_claim` throughout. Branch lane:
> `cr/rdo-005-multi-cycle-multi-asset-oos`.

## What was built (additive overlay — no baseline behavior changed)

| Artifact | Path |
|---|---|
| Spec / CR | `change-requests/cr-rdo-005-multi-cycle-multi-asset-oos.md` |
| Contract (SSOT) | `contract/multi-cycle-family-oos.schema.json` |
| New module | `quantlab/research/multi_cycle_oos.py` |
| Shared helper (refactor) | `quantlab/research/oos_artifact.py` |
| CLI | `scripts/run_multi_cycle_oos_backtest.py` |
| Unit/PBT/chaos tests | `tests/quantlab/test_multi_cycle_oos.py` (23) |
| CLI integration/e2e/smoke tests | `tests/test_multi_cycle_oos_cli.py` (5) |
| Mutation specs (+4) | `scripts/run_mutation_spot_checks.py` |
| Committed real artifact | `reports/multi-cycle-family-oos-artifact.json` |

## Headline real result (the actual Cluster 1 deliverable)

`uv run python scripts/run_multi_cycle_oos_backtest.py` over the CR-B21 deep
backfill (`data/vintage/raw/backfill-1990-01-01`, `approximate_availability=True`)
produced a **computed** leaderboard:

- **Co-temporal universe (5 assets):** `2330.TW, SPY, ^GSPC, ^IXIC, ^TWII`
- **As-of window:** `2000-01-04 → 2026-06-12` (**317.2 months**, ~26 years)
- **Cycles covered:** `dot_com, gfc, covid, rate_shock_2022` (all four)
- **Cadence:** daily, homogeneous (no oversampling); availability `approximate_event_date`
- **Leaderboard (OOS-net Sharpe, desc; baseline visible):**

  | model_family | strategy | oos_net_sharpe | baseline |
  |---|---|---|---|
  | regime | RegimeAllocationStrategy | 0.6811 | no |
  | baseline | BuyAndHold | 0.6569 | yes |
  | return_risk | ForecastAllocationStrategy | 0.3540 | no |
  | robust | RobustOptimizationStrategy | 0.3208 | no |

- Checksum validates. **Boundary:** mechanism + comparability evidence on
  approximate-availability deep history — **not** true PIT, **not** a strategy
  verdict, **no alpha claim**.

## Test-tier evidence (repo-side, default env)

| Tier | Result |
|---|---|
| Unit (+ line coverage of new module) | green (`test_multi_cycle_oos.py`) |
| Property-based (hypothesis) | green — cycles subset/monotone; checksum key-reorder invariance |
| Integration | committed-artifact validation (multi-asset, ≥300mo, 4 cycles, ranked) |
| e2e | CLI exit codes: computed=0; insufficient/oversampled/degenerate=2 w/ reason |
| Smoke | minimal computed run writes schema-valid artifact |
| Chaos | empty/NaN/missing-symbol/regime-degraded → fail-closed, never crash |
| VRT | backend CR has no UI surface; the evidence-count re-pin is part of the deferred consolidated refresh (see below) |
| Mutation (+4) | `multi-cycle-oos-{ranking-order,overclaim-gate,degeneracy-gate,approximate-mode-marker}` — all **KILLED** in-session |
| Static | `mypy` clean (3 files); `lint-imports` **KEPT** (framework isolation) |
| Refactor safety-net | `real-data-oos-artifact.json` checksum **unchanged** after extracting `oos_artifact.py` |

Full default-env suite: **398 passed** with the optional PyTorch LSTM lane skipped
as designed (370 prior default-env baseline + 28 new). All 28 new tests green.

## Repo-side closure vs external execution

- **`completed-local` (repo-side):** all code, tests, mutations, refactor, real
  artifact, mypy, import-linter — done and green in the default env.
- **`external-blocked` (UAT capture env):** the *canonical* governance evidence
  refresh — the **no-skip** pytest gate transcript bump (374 → **402**, torch
  lane runs in the UAT env so there is no skip), the mutation count bump
  (111 → **115**, JSON regen), the coupled dashboard `dataHash` regeneration, and
  the browser-visual VRT re-pin — must be produced in the **torch-enabled UAT/runtime
  env**. The default dev env excludes torch (a-torch-default-dependency-isolation),
  so it can only produce a `… passed, <torch-lane skipped>` transcript, which the
  governance stale-marker guard forbids. Committed evidence is therefore left at
  the green `374`/`111` baseline; this CR's count/dashboard refresh is the
  next step, gated on the UAT capture env. Regenerate with:
  `uv run python scripts/capture_pytest_gate.py` and
  `uv run python scripts/run_mutation_spot_checks.py --report-json docs/review/assets/gate-python-mutation.json`
  in the torch-enabled env, then sync the count surfaces + regenerate the dashboard payload.

## Findings surfaced (routed to ISSUE_LOG)

1. **`build_model_family_evaluation` cannot score the canonical dumb baseline** —
   `quantlab/models/evaluation.py::_claim_boundary` hard-raises unless
   `strategy_metadata.claim_boundary == "no_alpha_claim"`, but `BuyAndHold.metadata`
   omits the key. CR-RDO-005 sidesteps this by rejecting only *explicit* overclaims.
2. **Regime family degraded over the deep backfill** — `T10Y2Y` (yield-curve
   feature) is one of the 6 CR-B21-throttled FRED series, so the regime family
   runs price-trend-only. Ties to the CR-B21 FRED residual (Cluster 2).
3. **Published default-env pytest count drift** — surfaces publish `374 passed`
   (a torch-enabled, no-skip capture), but the default (torch-excluded) env yields
   370 + the optional lane skipped. Pre-existing; reconciled by the UAT-capture refresh above.
