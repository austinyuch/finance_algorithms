# Tasks — Epic B:真實資料平台(PIT 接入)

> SDD Phase 3。執行紀律:嚴格 TDD = RED → GREEN → REFACTOR。
> 需求:[requirements.md](./requirements.md) · 設計:[design.md](./design.md)

| Task | 內容 | Implements | 狀態 |
|---|---|---|---|
| **B-1** ✅ | vintage loader:snapshot JSON → A0 PIT DataProvider(FRED/Stooq 解析、PIT 含修訂、空目錄不崩) | LOAD-001/002/003, AC-B-01/02 | **DONE**(TDD 3→3→refactor;commit b412888) |
| **B-2** ✅ | FRED 價格代理 → 真實價格資產(繞過 Stooq 404);loader `fred_price_series` 參數;snapshot 加 SP500/那指/黃金/油/台幣匯率;`scripts/run_vintage_slice.py` demo(誠實報告就緒、夠了才跑回測) | LOAD-* 應用 | **DONE**(TDD;全套 91 passed) |
| **B-4** ✅ | as-of 頻率對齊(`research/align.align_asof`,PIT forward-fill) | ALIGN-001 | **DONE**(TDD;commit 220f723) |
| **B-5** ✅ | `pit_strictness`(strict/lenient)接入 `backtest_config` | ALIGN-001 | **DONE**(**CR-B5** overlay:schema+re-codegen+provider strict;commit 9733a8b) |
| **B-3** ◑ | 歷史 bulk backfill | CRAWL-001 | **FRED 全史已被 snapshot 涵蓋**;Stooq/個股=真機 handoff(見 review.md);**深度 1990+ 近似 backfill 已落地(CR-B21**:`scripts/backfill_history.py`,`is_approximate=true`、per-source degradation/idempotent、18/24 sources;strict 模式排除、`no_alpha_claim`);6 FRED rate/FX 系列待 idempotent 重跑(FRED IP throttle) |
| **B-6** ✅ | review.md verdict + CR 收斂 | — | **DONE**([review.md](./review.md);Verdict PASSED repo-side) |

> `is_approximate` lag 估算(無 vintage 源歷史)為前瞻能力,待 bulk backfill 落實(政策 Decision 3)。

## 注意
- B-5 會修改 a0 的 `contract/schemas/backtest_config.json` → 須走 **CR overlay**(登錄於 SPECS.md Open CRs、re-codegen Pydantic models、跑全型別檢查找漂移)。
- B-3 屬真機/有網路執行(沙箱網路不穩);repo-side 先備好 loader 與測試,bulk fetch 為 handoff。
