# Design — Real-Data ≥2-Asset OOS-Net Backtest

## Overview

Add a research-layer orchestration module plus a CLI that runs the *existing*
A0 `VectorizedEngine` over real PIT vintage data for a candidate strategy and a
dumb baseline, and emits a checksumed OOS-net comparison artifact. No engine,
loader, cost, or metric semantics change — this slice is composition + honest
gating only. Data-volume sufficiency is computed up front and the runner fails
closed to `insufficient_data` when history is too thin.

## Module placement & framework isolation

- Core logic: **`quantlab/research/real_data_oos.py`** (new). `quantlab/research`
  is explicitly *not* backtest core and is exempt from the ML-framework
  isolation rule; it may import `quantlab.runner`, `quantlab.data`,
  `quantlab.strategies`, `quantlab.tracking`. It does **not** import
  `torch`/`tf`/`jax`, so `lint-imports` stays green and no new contract is needed.
- CLI: **`scripts/run_real_data_oos_backtest.py`** (new), mirroring
  `scripts/run_vintage_slice.py` but producing a governed artifact + exit code
  instead of a print-only demo.
- Reuse the existing checksumed-artifact pattern from
  `quantlab/models/evaluation.py` (`_canonical_json` + `sha256` over a
  `{artifact_uri, generated_at, report}` payload).

## Existing APIs consumed (verified)

- `build_provider_from_vintage(vintage_root, fred_price_series=None, strict=False)
  -> InMemoryPITDataProvider` — `quantlab/data/vintage.py:81`.
- `InMemoryPITDataProvider.history(asof, field, symbols)`, `.universe(asof)`,
  `.get(...)` — PIT-safe (`available_date <= asof`) — `quantlab/data/provider.py:42-87`.
- `run_and_log(strategy, data, config, store) -> (run_id, result)` —
  `quantlab/runner.py:18`; `VectorizedEngine().run` returns
  `{run_id, strategy_name, strategy_metadata, config, rebalance_dates, metrics[...]}`.
- `metrics[i]` carries `segment ∈ {in_sample,out_of_sample,full}`,
  `basis ∈ {gross,net}`, `sharpe`, etc. OOS-net Sharpe =
  `metric where segment==out_of_sample and basis==net`.
- `LocalResultStore(db_path)` — `.log`, `.leaderboard`, `.get` —
  `quantlab/tracking/local_store.py`.
- Baselines: `BuyAndHold`, `StaticWeights`, `RandomStrategy` —
  `quantlab/strategies/`.

## Public API (new) — `quantlab/research/real_data_oos.py`

```python
@dataclass(frozen=True)
class DataSufficiency:
    price_assets: tuple[str, ...]
    asset_count: int
    history_start: str | None      # ISO date of earliest price event_date
    history_end: str | None
    history_span_months: float
    min_assets: int
    min_history_months: float
    sufficient: bool
    reason: str                    # "ok" | "fewer_than_min_assets" | "history_below_min_window"

def assess_data_sufficiency(
    provider: Any, *, min_assets: int = 2, min_history_months: float = 18.0,
) -> DataSufficiency: ...
# 18.0 default = train(12)+test(6) of the default walk-forward window.

def build_real_data_oos_report(
    provider: Any, *, candidate: Any, baseline: Any,
    config: Mapping[str, Any], store: Any,
) -> dict[str, Any]:
    # runs candidate + baseline via run_and_log, extracts OOS-net Sharpe each,
    # ranks OOS-net only with baseline visible. Returns:
    # {claim_boundary:"no_alpha_claim", metric_authority:"out_of_sample_net_only",
    #  status:"computed", rows:[{strategy_name,oos_net_sharpe,is_baseline,run_id}],
    #  asset_set:[...], asof_window:{start,end}, cost_config:{...},
    #  data_provenance:{asset_count,history_start,history_end,history_span_months}}

def build_insufficient_data_report(suff: DataSufficiency, *, config) -> dict[str, Any]:
    # status:"insufficient_data", rows:[], same claim/provenance fields.

def build_real_data_oos_artifact(report, *, artifact_uri, generated_at) -> dict
def validate_real_data_oos_artifact(artifact) -> None      # raises on drift
def write_real_data_oos_artifact(artifact, path) -> Path
```

Artifact shape: `artifact_kind="real_data_oos_backtest_artifact"`,
`claim_boundary="no_alpha_claim"`, `metric_authority="out_of_sample_net_only"`,
`status ∈ {computed, insufficient_data}`, `row_count`, `report`, `checksum`.

## Behavior / decision flow (CLI)

```
provider = build_provider_from_vintage(VINTAGE_ROOT, PRICE_PROXIES)
suff = assess_data_sufficiency(provider, min_assets=2, min_history_months=18)
if not suff.sufficient:
    artifact = build_real_data_oos_artifact(build_insufficient_data_report(suff,...))
    write/print artifact
    return 2                      # fail closed; NOT a success comparison
report   = build_real_data_oos_report(provider, candidate, baseline, cfg, store)
artifact = build_real_data_oos_artifact(report, ...)
write/print artifact
return 0
```

## Correctness mapping (REQ → mechanism)

- **REQ-RDO-001** — `build_real_data_oos_report` runs both strategies through the
  engine, reads OOS-net Sharpe, ranks OOS-net only, baseline visible; records
  asset set, as-of window, cost config, provenance. CLI writes deterministic
  sorted JSON or stdout.
- **REQ-RDO-002** —
  - *No lookahead:* the module only reads through `provider.history/get`
    (already `available_date <= asof`). Proven by a **future-revision invariance
    test**: adding a price row with `available_date` after the window must not
    change OOS-net output.
  - *Survivorship:* universe pulled via `provider.universe(asof)`; test includes
    a delisted-at-end asset.
  - *Net≠gross under cost:* candidate with cross-rebalance turnover under nonzero
    `cost_config`; test asserts OOS-net Sharpe ≠ OOS-gross Sharpe.
- **REQ-RDO-003** — sufficiency gate (<2 assets OR span < min window) →
  `insufficient_data`, nonzero, no success rows; every artifact carries
  `no_alpha_claim`; re-run with more data upgrades status (vintage snapshots read
  only, never mutated).

## Test strategy (TDD: red → green → refactor)

New tests: `tests/quantlab/test_real_data_oos.py`.

- **Unit (line-coverage target ≥90% on the new module):** sufficiency thresholds
  (≥2 / <2 assets; span ≥ / < min); report rows ranked OOS-net desc with baseline
  visible; artifact checksum round-trip; `validate_*` raises on tampered
  checksum / missing baseline / wrong claim boundary; insufficient artifact has
  empty rows + `no_alpha_claim`.
- **PBT (hypothesis):** for random ≥2-asset price panels with positive history,
  `assess_data_sufficiency(...).sufficient is True` and never raises;
  artifact checksum is stable across dict key reordering (canonicalization
  invariance).
- **Integration:** build an in-memory provider with sufficient real-format
  history → run candidate (turnover) + `BuyAndHold` baseline end-to-end → assert
  computed artifact validates, rows include both, baseline visible. Plus the
  future-revision invariance, survivorship, and net≠gross tests above.
- **Mutation spot checks** (`scripts/run_mutation_spot_checks.py`):
  - `real-data-oos-sufficiency-asset-gate` — flip `min_assets` comparison
    (`<` → `<=` or `count >= min` → `True`) ⇒ sufficiency test fails.
  - `real-data-oos-net-sharpe-segment` — flip OOS-net extraction
    (`out_of_sample` → `in_sample`) ⇒ ranking/cost test fails.
  - `real-data-oos-baseline-visibility` — drop the baseline-visible guard ⇒ test
    fails.

## TESTS.md registry

Add rows to `quantlab/TESTS.md` (folder registry) and `.agents/specs/TESTS.md`
(spec rollup) mapping the new tests to REQ-RDO-001/002/003 and the three mutation
spot checks, with evidence = `uv run pytest -q tests/quantlab/test_real_data_oos.py`
plus the mutation names.

## Out of scope (explicit)

- High-frequency/order-book simulation (A0 event-replay future scope).
- Real multi-year history sufficiency (calendar-time gated; external).
- Surfacing real runs in the Next.js dashboard (later F follow-up).
- Stooq enablement (ISSUE-B3-001, separate).
