# Review — Epic B:真實資料平台(PIT 接入)

> SDD Phase 5。verdict authority。
> 驗證:`uv run pytest -q` → **137 passed**;mypy clean(40 files);import-linter KEPT;drift-guard 綠。

## Verdict:**PASSED(repo-side)**;B-3 bulk fetch 為 external/real-machine handoff

repo 端的資料平台能力完成且有測試:vintage 橋接、FRED 價格代理、as-of 對齊、pit_strictness(經 CR-B5)。真實「歷史 bulk fetch + 個股」屬真機/有網路執行(沙箱 Stooq 404),以 handoff 交付。

## REQ / Task → Evidence

| Task | 內容 | 證據 |
|---|---|---|
| B-1 ✅ | vintage loader(snapshot JSON → PIT provider) | test_b_1_vintage |
| B-2 ✅ | FRED 價格代理 → 價格資產(繞 Stooq 404)+ demo | test_b_2_fred_prices |
| B-4 ✅ | as-of 頻率對齊 | test_b_4_align |
| B-5 ✅ | pit_strictness（**CR-B5** overlay on a0：schema+codegen+provider strict） | test_b_5_strictness |
| B-3 ◑ | bulk crawler | **FRED 全史已被每日 snapshot 涵蓋**(fredgraph CSV 每次回完整序列);Stooq/個股(含 TSMC)= 真機 handoff(見下) |
| B-6 ✅ | 本 review | — |

## B-3 External Execution Handoff(real-machine)

- **狀態分類:** `completed-handoff`(repo 端已備好 loader + snapshot;bulk fetch 在沙箱外）。
- **FRED:** 不需額外 backfill — 每日 `scripts/daily_snapshot.py` 的 fredgraph 抓取**本身就回完整歷史**,且向前累積 vintage。
- **Stooq / 個股(含 TSMC 2330):** 本環境仍回 404; restoration attempts must run `scripts/stooq_contract_proof.py --stooq-symbols ...` and may only reach `eligible_for_opt_in_review` after append-only snapshot files contain positive finite close rows.
- **下一步(真機):** 跑數日 snapshot 累積價格 vintage 後,`scripts/run_vintage_slice.py` 即可在真實資料上跑回測。

## CR 收斂
- **CR-B5(pit_strictness)→ Implemented**(additive schema overlay on a0;re-codegen + 全型別檢查通過,無漂移)。SPECS.md Open CR 收斂。
- **CR-B7/CR-B8/CR-B9 source policy → Implemented**:invalid FRED gold proxy removed, Yahoo fallback added, and Stooq made opt-in after repeated 404s.
- **CR-B10 source health → Implemented(repo-side)**:source status summaries are explicit and do not re-enable blocked Stooq defaults.
- **CR-B11 snapshot run report → Implemented(repo-side)**:`daily_snapshot.py --report-json` emits machine-readable counts, per-source outcomes, and source-health posture while preserving graceful degradation.
- **CR-B12 scoped live write smoke → Implemented(repo-side + local live smoke)**:`daily_snapshot.py --out-root --fred-series FEDFUNDS --yahoo-symbols '' --no-noaa` wrote one real public FRED source, and the second run skipped the existing same-day file.
- **CR-B18 source quorum gate → Implemented(repo-side)**:`snapshot_ops_gate.py --require-source-quorum` rejects scoped, dry-run, replayed-dry, failed-source, and missing-group reports as broad source readiness evidence.
- **CR-B19 source quorum live proof → Implemented(repo-side + live proof)**:`source_quorum_proof.py` ran the broad FRED/Yahoo/NOAA quorum scope, failed closed on a transient FRED timeout, then passed on retry with append-only `skip=6`, `fail=0`, proof `status=proven`.
- **CR-B20 Stooq contract proof wrapper → Implemented(repo-side + live fail-closed proof)**:`stooq_contract_proof.py` requires explicit Stooq symbols, verifies snapshot files and positive finite close rows, and exits nonzero unless the result is only `eligible_for_opt_in_review`; the 2026-06-12 live `spy.us` probe returned HTTP 404 and emitted `status=not_proven`.

## Residual / 刻意降級
- is_approximate lag 估算(無 vintage 源的 pre-collection 歷史)為前瞻能力,目前資料皆 `is_approximate=false`;待 bulk backfill 時落實 lag 表(政策 Decision 3）。
- Broad source quorum for the selected FRED/Yahoo/NOAA default groups is proven for 2026-06-12 by `.agents/specs/b-data-platform/reports/source-quorum-attempt-2026-06-12-proof.json`.
- Stooq/個股 bulk fetch remains source-contract blocked; Stooq default source stays disabled until `stooq_contract_proof.py` records positive finite live close rows and a maintainer separately approves opt-in review.

## 交棒
真實價格累積後,Epic A slice 可由 `build_provider_from_vintage(..., fred_price_series=...)` 換真實 provider 重跑。Epic C(組合最佳化)可在此資料平台上接續。
