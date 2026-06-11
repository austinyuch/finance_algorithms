# Requirements — Epic B:真實資料平台(PIT 接入)

> SDD Phase 1。Spec: `b-data-platform`。分支 `spec/b-data-platform`。
> 上游:[../allweather-portfolio-platform/02-epic-breakdown.md](../allweather-portfolio-platform/02-epic-breakdown.md)、[../allweather-portfolio-platform/03-data-vintage-snapshot-policy.md](../allweather-portfolio-platform/03-data-vintage-snapshot-policy.md)、A0/A(已 merged)。

## 0. Governance
- **Work classification:** `new spec`。
- **Depends On:** `a0-backtest-foundation`(PIT DataProvider 介面)、`scripts/daily_snapshot.py`(vintage 捕捉,已上線)。
- **Impacts:** 無既有行為變更(新增 loader)。
- **First-slice boundary(B-1):** 把已在累積的 vintage snapshot JSON 解析成 A0 `InMemoryPITDataProvider`(PIT 正確:`available_date = snapshot 擷取日`),讓 `run_hedge_slice` 能在真實資料上重跑。**測試不打網路**(fixture JSON)。
- **成功定義:** 同一條 Epic A slice,把合成 provider 換成 vintage-loaded provider 就能跑。

## 1. 鎖定決策(承資料治理政策)
- Bitemporal:`event_date`(所屬期)+ `available_date`(snapshot 擷取日,自建 vintage = 真實可得日,`is_approximate=false`)。
- 來源:FRED(總經,fredgraph CSV,有完整歷史)、Stooq(行情 CSV)、NOAA ONI(氣候)。
- Hybrid 分層:有 vintage 的源用真實 vintage;無 vintage 的歷史用估算 lag + `is_approximate`(此政策已定,B 後續 task 落實)。

## 2. Functional Requirements
- **REQ-B-LOAD-001**(B-1)系統須讀取 `data/vintage/raw/<date>/*.json`,把 FRED 記錄解析成 macro 序列(event_date=observation date、available_date=snapshot 日、value),建成 A0 DataProvider。
- **REQ-B-LOAD-002**(B-1)須解析 Stooq 記錄成 price 序列(symbol、event_date=報價日、available_date=snapshot 日、close)。
- **REQ-B-LOAD-003**(B-1)多份 snapshot(不同日)的同一序列須保留各自 available_date,讓 PIT 取數呈現「修訂」(較晚 snapshot = 較新版本)。
- **REQ-B-CRAWL-001**(後續)歷史 backfill crawler(bulk fetch,真機/有網路時)。
- **REQ-B-ALIGN-001**(後續)頻率對齊、缺值、`is_approximate` 標註、`pit_strictness` 接入 `backtest_config`。

## 3. Acceptance Criteria(本回合聚焦 B-1)

#### AC-B-01 FRED vintage → PIT macro(REQ-B-LOAD-001/003）
1. Given fixture vintage:`fred_CPIAUCSL.json`(available_date D1,CSV 含兩個 observation)
2. When 由 vintage 目錄建 provider,查 `macro("CPIAUCSL", asof)`
3. Then asof < D1 → None;asof >= D1 → 回最新 observation 值
4. And 再加一份較晚 snapshot(D2>D1,同序列修訂值)→ asof>=D2 取修訂值,D1<=asof<D2 取原值

#### AC-B-02 Stooq vintage → PIT price(REQ-B-LOAD-002）
1. Given fixture `stooq_spy_us.json`(available_date D,close=C,報價日 Q)
2. When 由 vintage 建 provider,在 asof>=D 查價
3. Then 回傳 close=C、available_date=D(PIT)

## 4. Out of Scope（本回合）
歷史 bulk crawler、頻率對齊、`is_approximate` lag 估算、`pit_strictness`、組合最佳化（Epic C+）。
