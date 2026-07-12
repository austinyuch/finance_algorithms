# Data Governance Decision — Vintage / Snapshot Policy(Epic B 前置)

> Program 級資料治理決策記錄(ADR 性質)。**約束 A0(DataProvider 契約)、B(蒐集/處理)、D(訓練)。**
> Status: **Accepted(2026-06-09)**。上游:[01-problem-space.md](./01-problem-space.md)
> 為何現在定:vintage 是 perishable —— 今天沒 snapshot 的資料,以後無法重建它當時的 point-in-time 樣貌。

## 核心問題
回測要的是「在時點 t,我**當時**實際能看到什麼」。但多數免費資料源只提供**現在這個修訂後的最終值**,且總經會被回溯修訂多次。若用最終值回測過去 = 隱性 lookahead,整個 lab 的結論不可信。

---

## Decision 1 — Bitemporal 記錄規則(強制)
所有資料在**蒐集當下**就必須同時寫入:
- `event_date`:資料所屬期(如 CPI 的所屬月)。
- `available_date`:該值**實際可得/公布**的日期。

A0 `DataProvider.get(asof)` 一律 `WHERE available_date <= asof`。**禁止事後補 `available_date`**(那本身就是猜測)。

## Decision 2 — 各源 vintage 策略
| 源 | 有無 vintage | 策略 |
|---|---|---|
| **FRED / ALFRED**(美國總經) | ✅ 有(ALFRED archival) | 取真實 vintage,`available_date` = 該 vintage 公布日,`is_approximate=false` |
| 台灣總經(主計總處/央行) | ❌ 多數無 | 自建 snapshot 向前累積;歷史用 Decision 3 估算 |
| 行情(yfinance 等) | ⚠️ 只給 adjusted | 抓**原始價 + as-of corporate actions**;snapshot 每日收盤 |
| 氣候(NOAA ONI/ENSO) | ⚠️ 會修訂 | snapshot 月度;歷史用估算 lag |

## Decision 3 — Hybrid 分層標註(pre-collection 歷史政策)
- 有 vintage 的源:用真實 vintage,`is_approximate=false`。
- 無 vintage 的源、且在 snapshot 起點之前的歷史:`available_date = event_date + 典型發布 lag`,並標 **`is_approximate=true`**。
- **回測可選嚴格度:**
  - `strict`:只用 `is_approximate=false` 的資料(最誠實,歷史較短)。
  - `lenient`:含 approximate(歷史較長,但須在 writeup 揭露此假設)。
- → A0 `BacktestConfig` 之後新增 `pit_strictness: strict|lenient`(Epic B 接入時擴充 schema,以 CR overlay 處理)。

### 典型發布 lag 估算表(初版,待逐源校正)
| 序列 | 估算 lag(所屬期末 → 可得) |
|---|---|
| US CPI | ~2 週 |
| US NFP/就業 | ~1 週(次月首個週五) |
| US GDP(advance) | ~30 天 |
| FOMC 利率 | 會議日(已知,非估算) |
| TW CPI(主計總處) | ~次月 5 日 |
| TW GDP(初步) | ~50 天 |
| ENSO ONI | ~次月初(前一月值) |

## Decision 4 — 每日 Snapshot Routine(現在啟動)
- **即刻啟動**最小每日 EOD snapshot,即使 A0/B 未完成(資料 perishable)。
- **Append-only / immutable**:每日 snapshot 寫一次,永不覆寫;`available_date` = 擷取日。
- 腳本:[scripts/daily_snapshot.py](../../../scripts/daily_snapshot.py)(standalone,degrade gracefully,不依賴 A0)。
- 之後 Epic B 正式開發時,把此 snapshot 流程整合進 bitemporal 儲存與資料版本管理。

## Decision 5 — data_version 與儲存
- 每次處理輸出打 `data_version` tag(對應 A0 可重現三元組 config+seed+data_version)。
- 儲存:append-only parquet,依 `snapshot_date` 分區;查詢用 DuckDB(輕量、無服務)。
- raw snapshot(未處理)與 processed(對齊後)分層,raw 永不修改。

## Decision 6 — 每日 Snapshot 的網路 egress allowlist(daily loop 執行環境約束)

> Status: **Accepted(2026-07-12)**。起因:daily loop 在 2026-06-12 之後連續失敗,`data/vintage/raw/` 從該日起無新 snapshot。

**根因(root cause):** daily loop 跑在 Claude Code 遠端執行環境內,對外 HTTPS 一律經過 policy-enforcing egress proxy。當環境的 network policy 未把資料源主機列入 allowlist 時,proxy 對 `CONNECT` 回 **`403 Forbidden`**(`gateway answered 403 to CONNECT`,policy denial),`scripts/daily_snapshot.py` 22 個 job 全數 `ProxyError` 失敗、`main()` 回 exit code 1,daily loop 因而記為 failure。這是**組織 egress 政策拒絕,不是程式 bug**;依 proxy 規約,egress 403/407 **只回報、不繞道**(不得改用替代主機或關閉 proxy 迴避政策)。

**必要 allowlist 主機(缺一即該源當日失敗):**

| 主機 | 用途 | 必要性 |
|---|---|---|
| `fred.stlouisfed.org` | FRED 總經 + 價格代理 CSV(`fetch_fred`) | **必要** |
| `query1.finance.yahoo.com` | Yahoo chart JSON — TSMC/TWSE/ETF 收盤(`fetch_yahoo_chart`) | **必要** |
| `www.cpc.ncep.noaa.gov` | NOAA Oceanic Niño Index(`fetch_noaa_oni`) | **必要** |
| `stooq.com` | Stooq 報價(`fetch_stooq`) | 選用;預設停用,僅 `QUANTLAB_STOOQ_SYMBOLS` opt-in 時才需要 |

**解法(operator 動作,非 repo 變更):** 在該 daily loop 執行環境的 network policy 內,把上述**必要**三個主機加入 allowlist(或改用允許這些主機的 policy)。設定位置為 Claude Code 環境設定 → network policy;參見 https://code.claude.com/docs/en/claude-code-on-the-web 。改完後以 `uv run python scripts/daily_snapshot.py --report-json artifacts/snapshot-report.json` 驗證 `fail=0`。

**preserve daily data:** `data/vintage/raw/` 已被 git 追蹤、未列入 `.gitignore`,故資料只要「擷取成功並 commit」即永久保存(append-only / immutable,見 Decision 4)。preservation 無缺口;唯一阻斷點是上述 egress。allowlist 補上後,daily loop 每日 capture→commit→push 即恢復。

**快速自我診斷(未來 daily loop 失敗時):**
- 症狀:所有 source `ProxyError: ... Tunnel connection failed: 403 Forbidden`。
- 確認:`curl -sS "$HTTPS_PROXY/__agentproxy/status"` 的 `recentRelayFailures` 是否為對上述主機的 `connect_rejected` / 403。
- 若是 → egress allowlist 缺該主機(本 Decision);**不是**程式或資料問題。

---

## 對下游的約束
- **A0:** DataProvider 契約已內建 `event_date`/`available_date`;Epic B 接真實資料時零改動即相容。`pit_strictness` 之後以 CR overlay 加入 `backtest_config.json`。
- **B:** 每個 source adapter 必須輸出 bitemporal 欄位 + `is_approximate` 旗標;raw 不可改。
- **D:** 訓練特徵只能用 PIT 資料;`strict`/`lenient` 模式須在每次實驗 metadata 標明。

## 待 Epic B 正式 spec 展開
本決策記錄只定治理方針與啟動 snapshot;完整 source adapter、頻率對齊、缺值、授權合規等 requirements 於 Epic B 進 SDD 時撰寫。
