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
  | regime | RegimeAllocationStrategy | 0.6694 | no |
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
- **Mutation evidence refresh (DONE, torch-free):** the full Python mutation suite
  now regenerates end-to-end at **115/115** (`gate-python-mutation.json` + the 6
  mutation-sync surfaces synced). This first required **repairing 5 pre-existing
  stale hosting-mutation anchors** — `public-hosting-{manifest,probe}-{status,hash}-overclaim`
  and the review-probe copy were pinned to `configured_not_observed`/`mismatched`
  from *before* the CR-B21 deploy re-pinned the committed manifest/probe to
  `proven`/`matched`, which had silently blocked any end-to-end mutation re-run
  (the committed 111 JSON predated the breakage). Each repaired mutation flips the
  legitimately-`proven`/`matched` value to the broken one the hosting-proof guard
  catches; all 5 verified KILLED, plus the 4 CR-RDO-005 mutations.
- **Pytest evidence refresh (DONE):** the canonical **no-skip** pytest gate was
  captured by transiently installing torch into the venv (`uv pip install torch`,
  not committed to pyproject/uv.lock) so the PyTorch LSTM lane runs → `gate-pytest.txt`
  **402 passed** (no skip). The review-gate count surfaces (TESTS.md, both generation
  guides, `docs/review/index.html`, manuals, registry) are synced to 402; torch was
  then removed (`uv sync`) to restore the honest torch-free default env (which runs
  398 passed + the optional lane skipped). The committed transcript is the canonical
  torch-enabled count, exactly as the prior `374` was captured.
- **`deploy-gated` (remaining):** only the committed dashboard payload
  (`docs/**/showcase.json`, `dataHash 0f170441…`) + its manifest/probe + the
  browser-visual VRT re-pin still lag at 374/111. Regenerating the payload flips
  committed hosting `proven`→`configured_not_observed` until Pages serves the new
  `dataHash` (mirrors CR-RDO-004), so this re-pin is intrinsically part of the deploy
  flow and is left for it. Regenerate with:
  `uv run python scripts/capture_pytest_gate.py` and
  `uv run python scripts/run_mutation_spot_checks.py --report-json docs/review/assets/gate-python-mutation.json`
  in the torch-enabled env, then sync the count surfaces + regenerate the dashboard payload.

## Findings surfaced (routed to ISSUE_LOG)

1. **`build_model_family_evaluation` cannot score the canonical dumb baseline** —
   `quantlab/models/evaluation.py::_claim_boundary` hard-raises unless
   `strategy_metadata.claim_boundary == "no_alpha_claim"`, but `BuyAndHold.metadata`
   omits the key. CR-RDO-005 sidesteps this by rejecting only *explicit* overclaims.
2. **Regime family un-degraded (CR-B21 residual closed)** — `T10Y2Y` (yield-curve
   feature) was one of the 6 CR-B21-throttled FRED series; it has since been
   backfilled (idempotent re-run, manifest `fail=0`), so the regime family now
   runs **full-feature** (price-trend + yield-curve). The committed multi-cycle
   artifact was regenerated: regime OOS-net Sharpe `0.6811→0.6694`, still edges
   BuyAndHold (0.6569), ranking order unchanged; integration test still green.
3. **Published default-env pytest count drift** — surfaces publish `374 passed`
   (a torch-enabled, no-skip capture), but the default (torch-excluded) env yields
   370 + the optional lane skipped. Pre-existing; reconciled by the UAT-capture refresh above.
