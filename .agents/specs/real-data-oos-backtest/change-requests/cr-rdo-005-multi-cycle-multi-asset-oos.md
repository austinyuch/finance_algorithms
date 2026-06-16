# CR-RDO-005 — Multi-cycle, multi-asset OOS-net evaluation across D model families

> CR overlay against the **completed** baselines `real-data-oos-backtest`
> (Implemented · Review PASSED) and `d-model-family-evaluation` (Implemented ·
> Review PASSED). Both baselines remain immutable; this overlay is **purely
> additive** (new module + new CLI + new artifact kind) and changes no existing
> engine / loader / cost / metric / ranking semantics.

## Dependencies, Impacts & CRs

- **[Depends On:** a0-backtest-foundation (VectorizedEngine, Strategy protocol),
  b-data-platform CR-B21 (1990+ approximate historical backfill +
  `approximate_availability` vintage loader), real-data-oos-backtest CR-RDO-001
  (co-temporal universe), CR-RDO-003 (degeneracy guard), CR-RDO-004
  (sampling-frequency guard), d-first/return-risk/robust model families.**]
- **[Impacts:** real-data-oos-backtest (a new sibling research composition reuses
  its sufficiency / cadence / degeneracy guards — additive, no behavior change),
  d-model-family-evaluation (the D families are now rankable on a *real* deep
  co-temporal universe, not synthetic only), RTM "Real-data backtest" gap (the
  single-window proxy comparison is extended to a multi-cycle, multi-family
  leaderboard — still mechanism evidence, not a strategy verdict).**]
- **[Open Change Requests:** none upstream block this; CR-B21 left a residual (6
  throttled FRED rate/FX series, incl. `T10Y2Y`) that constrained the regime
  family to a price-trend-only degraded mode — **now RESOLVED**: the residual was
  backfilled (idempotent re-run, manifest `fail=0`), so the regime family runs
  full-feature (artifact regenerated, regime Sharpe `0.6811→0.6694`). See FMEA RISK-RDO5-04.**]

## Problem

Every real-data comparison to date is single-window and single-family:
CR-RDO-003 trades **one** market index (`SP500`) over **2016→2026**;
CR-B21 proved **one** family-agnostic pair (`{^GSPC, ^IXIC}`, BuyAndHold vs
SmaTiming) over 1990→2026. The D model families
(`RegimeAllocationStrategy`, `ForecastAllocationStrategy`,
`RobustOptimizationStrategy`) have only ever been ranked on **synthetic** data
(`d-model-family-evaluation`). The platform's stated success criterion is
*methodology honesty + experiment capability*, and the highest-value remaining
experiment is to finally run **all D families together** through a **single,
shared, real, multi-cycle, multi-asset** OOS-net comparison against a dumb
baseline — spanning dot-com (2000), GFC (2008), COVID (2020), and the 2022
drawdown — now that CR-B21's deep approximate backfill exists.

This is a `no_alpha_claim` **mechanism + comparability** artifact, not a strategy
validation. It must inherit every honesty guard the single-window path already
enforces (PIT/availability marking, co-temporal universe, sampling-frequency
oversampling, flat-OOS degeneracy) and fail closed — never green — when the deep
data cannot support an honest comparison.

## Requirements

### REQ-RDO5-001 — shared-universe, multi-family real OOS-net leaderboard

**User story:** As a researcher, I want every D model family and a dumb baseline
run through the **same** real co-temporal universe and as-of window in one pass,
so their OOS-net Sharpe is directly comparable on real multi-cycle data.

#### Acceptance Criteria

1. When a provider exposes ≥`min_assets` real price assets sharing a window
   ≥`min_history_months`, then the report shall resolve the co-temporal universe
   and as-of window **once** and run the baseline plus each registered family
   over that identical universe/window, producing one ranked leaderboard.
2. When the leaderboard is built, then rows shall be sorted by out-of-sample
   **net** Sharpe descending, the baseline row shall always be present and
   flagged `is_baseline=true`, and each row shall carry `model_family`,
   `strategy_name`, `oos_net_sharpe`, `run_id`.
3. When any registered family or the baseline produces a run record whose
   `claim_boundary != "no_alpha_claim"`, then the build shall fail closed
   (`ValueError`) rather than emit a leaderboard.

### REQ-RDO5-002 — multi-cycle provenance is recorded

**User story:** As a correctness reviewer, I want the artifact to state exactly
which market cycles and assets the comparison actually spanned, so a reader
cannot mistake a short window for a multi-cycle result.

#### Acceptance Criteria

1. When a `computed` report is built, then `data_provenance` shall record the
   co-temporal `universe`, `overlap_start`/`overlap_end`/`overlap_months`, the
   `availability_mode`, the reused `sampling_frequency` block, and a
   `cycles_covered` list naming each canonical market-stress episode whose date
   falls inside the as-of window.
2. When a family runs in a degraded mode (a feature input is unavailable in the
   loaded vintage), then the report shall record that family's
   `feature_status`/metadata verbatim from the strategy, never silently treating
   degraded as healthy.
3. When `cycles_covered` is computed, then it shall be a deterministic function
   of the window only (no engine state), and shall be a subset of the canonical
   episode set.

### REQ-RDO5-003 — every single-window honesty guard is inherited

**User story:** As a maintainer, I want the multi-cycle path to reuse — not
re-implement — the existing PIT, co-temporal, sampling-frequency, and degeneracy
guards, so the deep-history path cannot drift to a weaker honesty bar.

#### Acceptance Criteria

1. When the rebalance cadence is meaningfully finer than the coarsest selected
   asset's native cadence, then the build shall fail closed with
   `SamplingFrequencyError` (reusing `real_data_oos.is_oversampled`), and the
   CLI shall map it to `status=insufficient_data`,
   `reason=oversampled_vs_native_frequency`, exit 2.
2. When any strategy's out-of-sample net return series is degenerate-flat
   (max OOS annualized vol `< 1e-6`), then the build shall fail closed and the
   CLI shall map it to `reason=degenerate_flat_oos`, exit 2 — never `computed`.
3. When fewer than `min_assets` co-temporal assets exist or the shared window is
   below `min_history_months`, then the build shall emit
   `status=insufficient_data` (empty rows) and the CLI shall exit 2.

### REQ-RDO5-004 — checksummed, deterministic, self-validating artifact

**User story:** As an auditor, I want a tamper-evident artifact identical in
discipline to the single-window one, so the multi-cycle result is verifiable.

#### Acceptance Criteria

1. When the artifact is built, then it shall carry
   `artifact_kind="multi_cycle_family_oos_artifact"`,
   `claim_boundary="no_alpha_claim"`,
   `metric_authority="out_of_sample_net_only"`, `row_count`, `generated_at`,
   `artifact_uri`, and a SHA256 `checksum` over canonical JSON of
   `{artifact_uri, generated_at, report}`.
2. When `validate_multi_cycle_artifact` runs, then it shall reject a tampered
   checksum, a wrong claim_boundary/metric_authority, a `computed` artifact with
   no baseline row, a `row_count` mismatch, and an unknown `artifact_kind`.
3. When an output path is given, then the CLI shall write deterministic
   sorted JSON (validated first); when omitted, it shall print to stdout.

### REQ-RDO5-005 — CLI runs the real deep backfill and stays research-only

**User story:** As a researcher, I want a one-command run over the CR-B21 deep
backfill that is explicitly approximate-availability and strict-PIT-excluded.

#### Acceptance Criteria

1. When the CLI runs, then it shall load the `backfill-1990-01-01` vintage with
   `approximate_availability=True`, record `availability_mode="approximate_event_date"`,
   and the result shall be **excluded** from any `strict=True` (true-PIT) load.
2. When the deep backfill has ≥2 co-temporal assets over ≥`min_history_months`,
   then the CLI shall exit 0 and write a `computed` multi-cycle leaderboard whose
   `cycles_covered` includes at least the dot-com, GFC, COVID, and 2022 episodes.
3. When any emitted artifact (computed or insufficient) is read, then it shall
   never describe the run as validated, production, or alpha-bearing.

## Design

### DDD boundary

The `quantlab/research` bounded context owns *composition of honest comparisons*.
This CR adds a sibling composition module beside `real_data_oos.py`; the
`engine`, `data`, `models`, and `tracking` contexts are untouched.

### Contract (artifact schema — SSOT in `contract/multi-cycle-family-oos.schema.json`)

```
multi_cycle_family_oos_artifact
├─ artifact_kind="multi_cycle_family_oos_artifact"
├─ status: "computed" | "insufficient_data"
├─ claim_boundary="no_alpha_claim"
├─ metric_authority="out_of_sample_net_only"
├─ artifact_uri, generated_at, row_count, checksum(sha256)
└─ report
   ├─ status, claim_boundary, metric_authority
   ├─ rows: [{model_family, strategy_name, oos_net_sharpe, is_baseline, run_id}]  # desc by oos_net_sharpe
   ├─ families: [sorted unique family names]
   ├─ baseline_run_ids: [...]
   ├─ asset_set, asof_window:{start,end}, availability_mode, cost_config
   └─ data_provenance
      ├─ universe, overlap_start/end/months, asset_count, history_span_months
      ├─ availability_mode
      ├─ sampling_frequency:{by_symbol, coarsest_cadence, coarsest_native_days, rebalance, rebalance_days, homogeneous}
      ├─ cycles_covered: [{name, date} ...]   # subset of canonical episodes within window
      └─ family_status:{family_name -> strategy.metadata}   # degraded-mode honesty
```

### Module `quantlab/research/multi_cycle_oos.py`

- `CANONICAL_CYCLES: tuple[tuple[str,str],...]` — `("dot_com","2000-03-10")`,
  `("gfc","2008-09-15")`, `("covid","2020-03-23")`, `("rate_shock_2022","2022-06-16")`
  (descriptive provenance only; no engine logic depends on these).
- `cycles_in_window(start, end) -> tuple[dict,...]` — deterministic subset.
- `@dataclass(frozen=True) FamilyRun` — internal (family, run_id, result).
- `build_multi_cycle_family_oos_report(provider, *, families: Mapping[str, Callable[[tuple[str,...]], Any]], baseline_build: Callable[[tuple[str,...]], Any], config, min_assets=2, min_history_months=240.0, store=None, availability_mode="approximate_event_date") -> dict`
  - Reuses `real_data_oos.assess_data_sufficiency` → fail closed if not sufficient.
  - Reuses `real_data_oos.rebalance_cadence_days` + `is_oversampled` on
    `suff.coarsest_cadence_days` → `SamplingFrequencyError`.
  - Builds baseline + each family over `suff.cotemporal_universe`; runs each via
    `quantlab.runner.run_and_log` (engine + optional store).
  - Reuses the degeneracy check (max OOS-net vol `< _DEGENERATE_VOL_EPS`).
  - Ranks via the **same** OOS-net extraction semantics as
    `d-model-family-evaluation` (`build_model_family_evaluation`-compatible rows);
    validates baseline-present + all-`no_alpha_claim`.
- `build_multi_cycle_insufficient_report(suff, *, config=None) -> dict`.
- Artifact: `build_multi_cycle_artifact` / `validate_multi_cycle_artifact` /
  `write_multi_cycle_artifact`.

### REFACTOR (with test safety-net)

Extract the duplicated canonical-JSON + SHA256 checksum helper used by
`real_data_oos.py` into `quantlab/research/oos_artifact.py`
(`canonical_json(value) -> str`, `artifact_checksum(uri, generated_at, report) ->
str`). Re-point `real_data_oos._canonical_json` at it (delegation, identical
output) and have `multi_cycle_oos.py` consume it. Safety-net: the existing
real-data-oos suite (36+ tests) plus the new suite must stay green and the
committed `real-data-oos-artifact.json` checksum must be **unchanged**.

### CLI `scripts/run_multi_cycle_oos_backtest.py`

- Loads `data/vintage/raw/backfill-1990-01-01` with
  `fred_price_series={"SP500"}`, `approximate_availability=True`.
- Families: `regime` → `RegimeAllocationStrategy(FirstRegimeClassifier(price_symbol="^GSPC"), risk_on={^IXIC tilt}, defensive={^GSPC tilt})`;
  `return_risk` → `ForecastAllocationStrategy(ReturnRiskForecaster(universe))`;
  `robust` → `RobustOptimizationStrategy(RobustPortfolioModel(universe))`.
  Baseline: `BuyAndHold(universe)`.
- `min_history_months=240` (force multi-cycle), monthly rebalance, net,
  walk-forward 12/6/6. Writes
  `.agents/specs/real-data-oos-backtest/reports/multi-cycle-family-oos-artifact.json`.

### Lightweight FMEA (design-phase; verified in review)

| Risk ID | Failure Mode | Effect | Cause | Current Control | Sev | Occ | Det | Planned Response (Prevent/Detect/Contain) | Task Trace |
|---|---|---|---|---|---|---|---|---|---|
| RISK-RDO5-01 | Approximate backfill read as true PIT | Lookahead-inflated comparison reads as validated | `approximate_availability=True` sets `available_date=event_date` | strict-mode exclusion exists | High | Med | Med | **Prevent**: hard-pin `availability_mode="approximate_event_date"` in artifact + assert strict load excludes it (REQ-RDO5-005.1) | T4, T-chaos |
| RISK-RDO5-02 | Families ranked on different windows/universes | Incomparable Sharpe presented as a leaderboard | per-family independent universe resolution | n/a (new) | High | Med | Hard | **Prevent**: resolve universe/window **once**, reuse for all (REQ-RDO5-001.1); **Detect**: unit asserts identical `asof_window` across rows | T2, T-unit |
| RISK-RDO5-03 | Oversampled/degenerate slips to `computed` | Fabricated-flat Sharpe overclaim | deep universe may include coarse assets | reuse CR-RDO-003/004 guards | High | Med | Med | **Detect**: reuse `is_oversampled` + degeneracy guard, fail closed (REQ-RDO5-003); mutation guard | T3, T-mut |
| RISK-RDO5-04 | Regime degraded (T10Y2Y missing) hidden | Reader thinks regime ran full-feature | CR-B21 throttled 6 FRED series | family_status records degraded honestly | Med | High | Med | **Contain**: record `family_status` verbatim (REQ-RDO5-002.2). **RESOLVED**: CR-B21 FRED residual backfilled (`T10Y2Y` available), regime now full-feature; artifact regenerated | T2, ISSUE_LOG (closed) |
| RISK-RDO5-05 | Evidence-count drift breaks governance/dashboard | Red suite / stale dataHash / VRT mismatch | new tests move pytest+mutation totals; embedded in `_FALLBACK_EVIDENCE_TESTS` | governance guards enforce sync | Med | High | Low | **Detect+Contain**: closeout resync all ~12 surfaces + regen dashboard payload + re-pin browser-visual (0-pixel, CR-FBP-001) | T-closeout |
| RISK-RDO5-06 | Multi-asset breadth silently traded for window | Reader thinks many assets over many cycles | more assets ⇒ shorter shared window | co-temporal resolver picks largest qualifying set | Med | Med | Med | **Contain**: record exact `universe` + `overlap_months` + `cycles_covered`; note breadth/depth tradeoff in review | T2, review |

## Tasks (TDD)

- **T1 (RED→GREEN)**: `oos_artifact.py` shared checksum helper + refactor
  `real_data_oos._canonical_json` to delegate; prove existing artifact checksum
  unchanged (refactor safety-net).
- **T2**: `cycles_in_window` + provenance assembly (unit + PBT: subset & window-monotone).
- **T3**: `build_multi_cycle_family_oos_report` ranking/baseline/no_alpha_claim +
  inherited guards (sufficiency, oversampling, degeneracy) — unit + fail-closed.
- **T4**: artifact build/validate/write + checksum roundtrip + tamper rejection (unit + PBT).
- **T5**: CLI `run_multi_cycle_oos_backtest.py` exit-code paths (integration/e2e + smoke).
- **T-chaos**: empty/missing dir, NaN closes, missing symbols, regime degraded → fail-closed/degrade not crash.
- **T-mut**: mutation specs `multi-cycle-oos-min-window-gate`,
  `multi-cycle-oos-baseline-visibility`, `multi-cycle-oos-ranking-order`,
  `multi-cycle-oos-approximate-mode-marker`.
- **T-closeout**: run real deep backfill → commit artifact; refresh folder
  `quantlab/TESTS.md` row; resync pytest+mutation counts across all governance
  surfaces; regen dashboard payload (`build_canonical_dashboard_artifact`) → new
  `dataHash`; re-pin browser-visual (VRT, 0-pixel expected); hand workspace
  `TESTS.md` rollup to `test-registry-manager`; single-snapshot SPECS.md/RTM.md;
  update NEXT_STEPS.md; author `review.md` verdict section.

### Test-tier obligations (explicit)

| Tier | Coverage |
|---|---|
| Unit (line coverage ≥90% of new module) | cycles, ranking, baseline-visible, no_alpha_claim reject, provenance, artifact validate/tamper, all fail-closed reasons |
| Property-based (hypothesis) | ranking is desc permutation; baseline always present; checksum invariant under key reorder; `cycles_in_window` ⊆ canonical & window-monotone |
| Integration | CLI over real `backfill-1990-01-01` → exit 0 computed, ≥2 assets, ≥240 months, families ranked, artifact validates |
| e2e | CLI `main()` exit codes: computed=0, insufficient/oversampled/degenerate=2 with correct reason |
| Smoke | minimal fast computed run writes a schema-valid artifact |
| Chaos | malformed/empty vintage, NaN closes, missing symbols, regime T10Y2Y-missing degrade → never crash |
| VRT | backend feature has no UI surface in this CR; the evidence-count change forces a committed browser-visual re-pin — must stay 0-pixel under CR-FBP-001 threshold (`0.001`) |

## Boundary

No engine/loader/cost/metric/ranking semantics change; no live data fetch (reads
immutable CR-B21 vintage); no alpha claim; project stays `local_demo_only` /
`no_alpha_claim`. The comparison is **mechanism + comparability evidence on
approximate-availability deep history**, explicitly **not** a strategy verdict
and **not** true-PIT. The regime family ran price-trend-only until the CR-B21 FRED rate/FX residual
(incl. `T10Y2Y`) was backfilled — **now complete** (manifest `fail=0`), so the
regime family runs full-feature (the committed artifact was regenerated: regime
Sharpe `0.6811→0.6694`, ranking unchanged).

## Review verdict

**State: Implemented (repo-side) · Review PASSED (repo-side closure) · evidence-refresh
handoff pending UAT capture env.**

- **REQ-RDO5-001..005 met (repo-side):** shared-universe multi-family leaderboard
  ranked OOS-net with the dumb baseline visible; multi-cycle provenance recorded;
  every single-window honesty guard (sufficiency / sampling-frequency / degeneracy)
  reused and fail-closed; checksummed self-validating artifact; real CLI run over
  the CR-B21 deep backfill computed a 5-asset, 2000→2026 (317mo), 4-cycle comparison.
- **Evidence:** 28 new tests across unit / PBT / integration / e2e / smoke / chaos
  (all green, default env); 4 new mutations all KILLED in-session; mypy clean;
  import-linter KEPT; refactor safety-net intact (committed single-window artifact
  checksum unchanged). See `reports/cr-rdo-005-implementation-report.md`.
- **FMEA residual verification:** RISK-RDO5-01 (approximate marking pinned +
  mutation-guarded), -02 (single shared universe asserted), -03 (guards reused +
  mutation-guarded), -06 (universe/overlap/cycles recorded) — all mitigated.
  RISK-RDO5-04 (regime degraded, `T10Y2Y` missing) — contained: `family_status`
  records it verbatim; routed to ISSUE_LOG, tied to CR-B21 FRED residual.
  RISK-RDO5-05 (evidence-count drift) — contained by deferring the count/dashboard
  refresh to the UAT capture env rather than publishing a guard-forbidden
  skip-bearing transcript (see implementation report).
- **Live-demo readiness:** unchanged — `local_demo_only`, `no_alpha_claim`; this CR
  adds no UI surface and makes no hosting/alpha claim.
- **Not closed here (external):** canonical no-skip pytest gate bump (374→402),
  mutation count bump (111→115 JSON), dashboard `dataHash` regen, browser-visual
  VRT re-pin — all gated on the torch-enabled UAT capture env.
