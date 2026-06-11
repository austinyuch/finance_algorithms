# Design — Epic B:真實資料平台(PIT 接入)

> SDD Phase 2。B-1 為 as-built;B-後續為前瞻設計。需求:[requirements.md](./requirements.md)。

## 1. 架構

```
scripts/daily_snapshot.py(已上線 cron)──寫──▶ data/vintage/raw/<date>/*.json
                                                        │
quantlab/data/vintage.build_provider_from_vintage ◀─────┘  (B-1)
        │  解析 FRED/Stooq → bitemporal rows
        ▼
A0 InMemoryPITDataProvider ──▶ run_hedge_slice / 任意回測(同 Epic A slice)
```

⚠️ `quantlab/data/vintage.py` 屬 data/,受框架隔離契約約束(import-linter:禁 torch/tf/jax)。

## 2. B-1 設計(as-built)

- **解析來源依 JSON `source` 前綴**(不依檔名):`fred:` / `stooq:` / `noaa:`(B-1 略 noaa)。
- **FRED**:fredgraph CSV → 每 observation 一筆 macro,`event_date`=observation date、`available_date`=snapshot 擷取日、`value`。
- **Stooq**:quote CSV → price,`event_date`=報價日、`available_date`=snapshot 日、`close`。
- **修訂**:多份 snapshot 各保留自己的 `available_date`;A0 `macro()`/`get()` 的 as-of 過濾自然呈現「較晚 snapshot = 較新版本」。
- listings 由 price symbols 推導(`list_date`=最早 event_date,無 delist)。
- 空/不存在目錄 → 回空 provider 不崩。

## 3. 後續設計(B-rest)

- **B-CRAWL(歷史 backfill)**:bulk fetch(真機/有網路),寫成同格式 vintage(或直接 provider source)。沙箱網路稍早 Stooq 404 / FRED 偶逾時 → 屬真機執行。
- **B-ALIGN(頻率對齊 + is_approximate)**:日頻行情 vs 月/季總經以 available_date 做 as-of forward-fill;無 vintage 源的 pre-collection 歷史用「所屬期 + 典型 lag」估 available_date 並標 `is_approximate=true`(承資料治理政策 Decision 3)。
- **B-STRICT(pit_strictness)**:`backtest_config` 新增 `strict|lenient`(strict 只用 `is_approximate=false`)→ **對 a0 的 CR overlay**(改 `contract/schemas/backtest_config.json`,需 re-codegen + 全型別檢查)。

## 4. Lightweight FMEA(資料正確性風險)

| Risk ID | Failure Mode | Effect | Control | Task |
|---|---|---|---|---|
| FMEA-B-01 | snapshot 日 ≠ 真實可得日 | 隱性 lookahead | available_date=擷取日,append-only 不回填(政策 D1/D4) | B-1 |
| FMEA-B-02 | bulk backfill 用最終值當歷史 | lookahead/灌水 | 有 vintage(FRED/ALFRED)用真實版本;無 vintage 標 is_approximate | B-ALIGN |
| FMEA-B-03 | 解析錯欄位 → 錯價 | 錯誤回測 | fixture 測試 + 欄位名映射 | B-1 |

## 5. REQ → Design / Test
| REQ | Design | Test |
|---|---|---|
| LOAD-001/002/003 | §2 | test_b_1_vintage |
| CRAWL-001 | §3 B-CRAWL | (後續) |
| ALIGN-001 | §3 B-ALIGN/B-STRICT | (後續) |
