# quantlab — TESTS.md(folder-level test registry)

Spec coverage: A0, A, B, C, D first model plus legacy `invest_algorithms` regression.
Canonical command: `uv run pytest -q`
Last refreshed: 2026-06-11 · full suite **123 passed** · `uv run mypy quantlab/ --ignore-missing-imports` clean(39 files) · `uv run lint-imports` KEPT · A0 mutation spot-check 5/5 killed

| Test ID / file | Covers | Spec / REQ / AC | Evidence |
|---|---|---|---|
| `test_a0_0_contract` | Strategy Protocol, schema roundtrip, AST framework isolation | a0-backtest-foundation IFC-001/002/003, FWAGN-001 | 3 pass |
| `test_a0_1_pit_dataprovider` | lookahead golden, survivorship, macro lag/revision, PBT-2 | a0 PIT-001..004, AC-A0-01/02 | 4 pass |
| `test_a0_2_engine` | toy parity, costs, metrics, walk-forward, event-driven stub | a0 BT-001..006, AC-A0-03 | 6 pass |
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
| `test_daily_snapshot` | bitemporal stamping, append-only write, parser wrappers, Yahoo latest-close PBT, graceful degradation | data vintage routine / CR-B8 | 12 pass |
| `test_governance_guards` | import-linter wrapper and spec/runtime interface drift guard | residual hardening | 2 pass |
| `test_c_1_optimize` | SLSQP max-return-under-vol optimizer and `MeanVarianceStrategy` | c-portfolio-core C-1 AC-C-01/02/03 | 5 pass |
| `test_c_2_multihorizon` | `MultiHorizonMeanVarianceStrategy`, horizon blending, PIT/reproducible fallback | c-portfolio-core C-2 AC-C-04/05 | 3 pass |
| `test_c_3_rebalance` | time/regime rebalance selector, D classifier smoke, PBT change invariants | c-portfolio-core C-3 AC-C-06/07 | 5 pass |
| `test_c_4_pyramid` | portfolio budget to legacy pyramid entry adapter | c-portfolio-core C-4 | 2 pass |
| `test_c_5_integration` | C strategy leaderboard integration and reproducibility | c-portfolio-core C-5 | 2 pass |
| `test_d_1_regime` | PIT-safe regime signal, missing fallback, macro revision as-of gate, stable labels | d-first-regime-model REQ-D-REGIME-001 / REQ-D-HOOK-001 | 4 pass |
| `test_d_2_regime_integration` | Regime allocation strategy vs static baseline in OOS-net leaderboard | d-first-regime-model REQ-D-BASELINE-001 / REQ-D-HOOK-001 | 2 pass |
| `test_algo_pyramid` | legacy pyramid calculator behavior | legacy `invest_algorithms` | 33 pass |

## External / Blocked Evidence

- B-3 live proof attempt on 2026-06-11: `uv run python scripts/daily_snapshot.py` captured six files under `data/vintage/raw/2026-06-11/` (`fred_FEDFUNDS`, `fred_CPIAUCSL`, `fred_GDPC1`, `fred_UNRATE`, `fred_SP500`, `noaa_oni`) and exited 1 after 16 source failures. All configured Stooq symbols, including `2330.tw`, returned HTTP 404; configured FRED gold proxy returned HTTP 404; several FRED series timed out. Tracked in `.agents/specs/ISSUE_LOG.md` as `ISSUE-B3-001`; invalid FRED gold default addressed by CR-B7.
- CR-B8 Yahoo fallback smoke on 2026-06-11: `fetch_yahoo_chart("2330.TW", "2026-06-11")` and `fetch_yahoo_chart("^TWII", "2026-06-11")` returned non-empty payloads with `event_date=2026-06-11`. Stooq itself remains external/source-contract blocked.

## Mutation spot-check(A0-6,manual)

`mutmut` 3.x sandbox 與本 layout 不相容(只複製受變異檔,top-level import 失敗)→ 改用手動代表性變異,5/5 全被殺:
M1 PIT `<=`→`>=`、M2 成本 turnover→0、M3 walk-forward `<`→`<=`、M4 累積報酬 `-1`→`+1`、M5 survivorship `>`→`<`。
> 待辦:mutmut 自動 runner 於乾淨 layout 重接(非阻塞)。

## Mutation spot-check(B/C continuation,manual)

- CR-B8 Yahoo parser: accepting trailing null closes in `_latest_yahoo_event_date()` was killed by `test_pbt_yahoo_latest_event_date_matches_last_valid_close`.
- C-3 rebalance selector: changing regime-change detection from `!=` to `==` was killed by `test_pbt_regime_rebalance_is_ordered_subset_and_captures_changes`.
