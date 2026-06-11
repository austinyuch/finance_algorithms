# quantlab — TESTS.md(folder-level test registry)

Spec coverage: A0, A, B, C, D model families, E-lite registry, F showcase/demo hardening, and legacy `invest_algorithms` regression.
Canonical command: `uv run pytest -q`
Last refreshed: 2026-06-11 · Python full suite **156 passed** · `uv run mypy quantlab/ --ignore-missing-imports` clean(48 files) · `uv run lint-imports` KEPT · Python mutation spot checks 8/8 killed · E-lite trace coverage 97.3% · B source-health trace coverage 97.6% · F Next.js tests 6 passed, coverage 84.37%, build/smoke/mutation passed

| Test ID / file | Covers | Spec / REQ / AC | Evidence |
|---|---|---|---|
| `test_a0_0_contract` | Strategy Protocol, schema roundtrip, AST framework isolation | a0-backtest-foundation IFC-001/002/003, FWAGN-001 | 3 pass |
| `test_a0_1_pit_dataprovider` | lookahead golden, survivorship, macro lag/revision, PBT-2 | a0 PIT-001..004, AC-A0-01/02 | 4 pass |
| `test_a0_2_engine` | toy parity, costs, metrics, walk-forward, event-driven stub, regime rebalance policy | a0 BT-001..006, AC-A0-03, CR-A0 regime scheduling | 9 pass |
| `test_a0_3_parallel` | parallel==sequential, child seeds, env isolation declarations | a0 PAR-001/002/003, AC-A0-06 | 3 pass |
| `test_a0_4_tracking` | log/get roundtrip, OOS-net leaderboard, reproducibility | a0 TRK-001/002/003, AC-A0-07 | 4 pass |
| `test_a0_5_integration` | full-chain happy/lookahead/reproducible/parallel consistency | a0 AC-A0-01..07 integration | 4 pass |
| `test_a_1_screen` | reverse cointegration screen and PIT history | a-tsmc-hedge-slice A-1 | 3 pass |
| `test_a_2_lstm` | PyTorch LSTM strategy protocol, fallback, reproducibility, leaderboard | a-tsmc-hedge-slice A-2 | 4 pass |
| `test_a_3_baselines` | static/random baselines and leaderboard runs | a-tsmc-hedge-slice A-3 | 4 pass |
| `test_a_4_hedge` | hedge weights, strategy screen, volatility reduction | a-tsmc-hedge-slice A-4 | 4 pass |
| `test_a_5_slice` | end-to-end TSMC hedge slice leaderboard and reproducibility | a-tsmc-hedge-slice A-5 | 2 pass |
| `test_b_1_vintage` | FRED/Stooq/Yahoo vintage loader to PIT provider, empty dir | b-data-platform B-1 / CR-B8 | 4 pass |
| `test_b_2_fred_prices` | FRED price proxy loader and snapshot source list | b-data-platform B-2 | 3 pass |
| `test_b_4_align` | as-of frequency alignment and PIT forward fill | b-data-platform B-4 | 2 pass |
| `test_b_5_strictness` | `pit_strictness` schema/provider/loader behavior | b-data-platform CR-B5 | 3 pass |
| `test_b_6_source_health` | source-contract health summary, Stooq blocked/default-disabled posture, PBT latest status preservation | b-data-platform CR-B10 | 3 pass |
| `test_daily_snapshot` | bitemporal stamping, append-only write, parser wrappers, Yahoo latest-close PBT, Stooq opt-in policy, graceful degradation | data vintage routine / CR-B8 / CR-B9 | 14 pass |
| `test_mutation_spot_checks` | mutation runner apply/restore PBT, ambiguity rejection, killed/survived behavior, CLI smoke | A0 mutation automation | 7 pass |
| `test_governance_guards` | import-linter wrapper and spec/runtime interface drift guard | residual hardening | 2 pass |
| `test_c_1_optimize` | SLSQP max-return-under-vol optimizer and `MeanVarianceStrategy` | c-portfolio-core C-1 AC-C-01/02/03 | 5 pass |
| `test_c_2_multihorizon` | `MultiHorizonMeanVarianceStrategy`, horizon blending, PIT/reproducible fallback | c-portfolio-core C-2 AC-C-04/05 | 3 pass |
| `test_c_3_rebalance` | time/regime rebalance selector, D classifier smoke, PBT change invariants | c-portfolio-core C-3 AC-C-06/07 | 5 pass |
| `test_c_4_pyramid` | portfolio budget to legacy pyramid entry adapter | c-portfolio-core C-4 | 2 pass |
| `test_c_5_integration` | C strategy leaderboard integration and reproducibility | c-portfolio-core C-5 | 2 pass |
| `test_d_1_regime` | PIT-safe regime signal, missing fallback, macro revision as-of gate, stable labels | d-first-regime-model REQ-D-REGIME-001 / REQ-D-HOOK-001 | 4 pass |
| `test_d_2_regime_integration` | Regime allocation strategy vs static baseline in OOS-net leaderboard | d-first-regime-model REQ-D-BASELINE-001 / REQ-D-HOOK-001 | 2 pass |
| `test_d_3_real_data_regime_benchmark` | Vintage-loader real-source-format regime benchmark vs static baseline with no-alpha claim | d-first-regime-model D-3 continuation | 2 pass |
| `test_d_4_return_risk_forecast` | PIT-safe return/risk forecasts, degraded fallback metadata, PBT long-only weights, OOS-net benchmark smoke | d-return-risk-forecast-model REQ-D-FORECAST-001 / REQ-D-ALLOC-001 / REQ-D-BENCH-001 | 4 pass |
| `test_d_5_robust_optimization` | PIT-safe robust optimizer estimates, downside penalty invariant, degraded fallback metadata, PBT long-only weights, OOS-net benchmark smoke | d-robust-portfolio-optimization-model REQ-D3-ROBUST-001 / REQ-D3-ALLOC-001 / REQ-D3-BENCH-001 | 4 pass |
| `test_e_1_experiment_registry` | E-lite experiment lineage, config catalog, deterministic dedupe, PBT config roundtrip, no-alpha claim rejection | e-mlops-tier3-lite REQ-E-LITE-REG-001 / REQ-E-LITE-READ-001 | 4 pass |
| `test_f_1_showcase_api` | Showcase read API, dashboard summary, conservative defaults, PBT leaderboard order, deterministic HTML smoke | f-showcase-read-api-dashboard REQ-F-SHOWCASE-001/002/003 | 4 pass |
| `frontend/tests/dashboard.test.tsx` | Real Next.js dashboard component, `/api/showcase` route, PBT leaderboard validator, no-alpha and demo-readiness claim boundaries | f-nextjs-showcase-dashboard / f-demo-hardening REQ-FNX-DASH-001 / REQ-FNX-API-001 / REQ-F-DEMO-001 / REQ-F-DEMO-002 | 6 pass |
| `test_algo_pyramid` | legacy pyramid calculator behavior | legacy `invest_algorithms` | 33 pass |

## External / Blocked Evidence

- B-3 live proof attempt on 2026-06-11: `uv run python scripts/daily_snapshot.py` captured six files under `data/vintage/raw/2026-06-11/` (`fred_FEDFUNDS`, `fred_CPIAUCSL`, `fred_GDPC1`, `fred_UNRATE`, `fred_SP500`, `noaa_oni`) and exited 1 after 16 source failures. All configured Stooq symbols, including `2330.tw`, returned HTTP 404; configured FRED gold proxy returned HTTP 404; several FRED series timed out. Tracked in `.agents/specs/ISSUE_LOG.md` as `ISSUE-B3-001`; invalid FRED gold default addressed by CR-B7.
- CR-B8 Yahoo fallback smoke on 2026-06-11: `fetch_yahoo_chart("2330.TW", "2026-06-11")` and `fetch_yahoo_chart("^TWII", "2026-06-11")` returned non-empty payloads with `event_date=2026-06-11`. Stooq itself remains external/source-contract blocked.
- CR-B9 Stooq opt-in smoke on 2026-06-11: `uv run python scripts/daily_snapshot.py --dry-run` listed no Stooq jobs and exited with `fail=0`.

## Mutation spot-check(A0-6,manual)

`mutmut` 3.x sandbox 與本 layout 不相容(只複製受變異檔,top-level import 失敗)→ 改用手動代表性變異,5/5 全被殺:
M1 PIT `<=`→`>=`、M2 成本 turnover→0、M3 walk-forward `<`→`<=`、M4 累積報酬 `-1`→`+1`、M5 survivorship `>`→`<`。
> 待辦:mutmut 自動 runner 於乾淨 layout 重接(非阻塞)。

## Mutation spot-check(B/C continuation,manual)

- CR-B8 Yahoo parser: accepting trailing null closes in `_latest_yahoo_event_date()` was killed by `test_pbt_yahoo_latest_event_date_matches_last_valid_close`.
- C-3 rebalance selector: changing regime-change detection from `!=` to `==` was killed by `test_pbt_regime_rebalance_is_ordered_subset_and_captures_changes`.
- CR-A0 engine scheduling: bypassing `select_rebalance_dates(...)` was killed by the A0 regime rebalance example and PBT tests.
- CR-B9 Stooq policy: defaulting Stooq to `["spy.us"]` was killed by `test_stooq_defaults_disabled_after_source_contract_block`.
- D-3 benchmark: changing `claim_boundary` to `alpha_claim` was killed by the D-3 integration test.
- `scripts/run_mutation_spot_checks.py`: automated suite killed 8/8 configured mutations (`engine-regime-selector`, `c3-regime-change`, `yahoo-latest-close`, `showcase-claim-boundary`, `d2-forecast-claim-boundary`, `d3-robust-claim-boundary`, `e-registry-claim-boundary`, `b-source-health-claim-boundary`).
- F showcase mutation: changing missing claim boundary from `no_alpha_claim` to `alpha_claim` was killed by `test_dashboard_summary_conservative_defaults_and_no_mutation`.
- D2 return/risk mutation: changing strategy metadata claim boundary from `no_alpha_claim` to `alpha_claim` was killed by `test_forecast_strategy_fallback_metadata_for_degraded_history`.
- D3 robust optimizer mutation: changing strategy metadata claim boundary from `no_alpha_claim` to `alpha_claim` was killed by `test_robust_strategy_degraded_history_falls_back_and_preserves_claim_boundary`.
- E-lite registry mutation: changing default claim boundary from `no_alpha_claim` to `alpha_claim` was killed by `test_experiment_registry_dedupes_same_config_and_preserves_no_alpha_claim`.
- B source-health mutation: changing `source_contract_status_only` to `source_contract_ready` was killed by `test_source_health_summary_marks_stooq_blocked_without_reenabling_defaults`.
- F Next.js mutations: changing fixture claim boundary from `no_alpha_claim` to `alpha_claim`, and changing public hosting from `not_proven` to `proven`, were killed by `frontend/tests/dashboard.test.tsx`.

## Line coverage spot checks

- F showcase: `uv run pytest --cov=quantlab.showcase --cov-report=term-missing tests/quantlab/test_f_1_showcase_api.py` → 95%.
- D2 return/risk: `pytest-cov` / `coverage run` hit NumPy native import instrumentation error (`cannot load module more than once per process`); fallback stdlib trace command passed and parsed `quantlab.models.return_risk` at 108/124 executable lines → 87.1%.
- D3 robust optimizer: `pytest-cov` hit the same NumPy native import instrumentation error; fallback stdlib trace command passed and parsed `quantlab.models.robust_optimization` at 117/133 executable lines → 88.0%.
- E-lite registry: `pytest-cov` hit the same NumPy native import instrumentation path through package imports; fallback stdlib trace command passed and parsed `quantlab.mlops.experiment_registry` at 73/75 executable lines → 97.3%.
- B source-health: fallback stdlib trace command passed and parsed `quantlab.data.source_health` at 41/42 executable lines → 97.6%.
- F Next.js: `cd frontend && npm run coverage` → 84.37% line coverage; `npm run build` and local HTTP smoke on `127.0.0.1:3044` passed.
