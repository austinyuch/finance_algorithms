# 架構設計 — h-showcase-shadcn-ui

> 參照：[requirements.md](./requirements.md)（REQ-SUI-001..005）。關鍵既有檔：`frontend/components/Dashboard.tsx`、`frontend/components/{InvestmentCharts,InteractiveResearchPanel,LiveRerunStatus}.tsx`、`frontend/scripts/export-public-demo.tsx`、`frontend/lib/public-demo.ts`（`buildVisualSnapshot` 檢查 `data-section` + claim labels）、`frontend/app/{layout.tsx,globals.css}`。

## 概述

deployed `docs/index.html` 目前是 `renderToStaticMarkup` 的 className markup、`<head>` 無 CSS。本 spec：(1) 導入 Tailwind v4 + shadcn 設計系統；(2) 以 shadcn 元件重構儀表板（保留 `data-section`/claim 契約）；(3) 在 export 加一個 **Tailwind 編譯 → inline `<style>` 注入 `<head>`** 的步驟，讓部署單檔 self-contained 且有樣式。

## 架構決策（含替代方案）

**選型：Tailwind v4 + 手動加入 shadcn 原語（不跑 shadcn CLI）。**
- **方案 A（採用）**：Tailwind v4（`@tailwindcss/postcss` 給 Next build/dev；`@tailwindcss/cli` 給 export 編譯）。手動新增 `components/ui/{card,badge,table,separator}.tsx`（cva + tailwind-merge），對齊 shadcn 慣例但不依賴其 CLI（CLI 需互動式 init，對既有 hand-rolled 專案摩擦大）。
- 方案 B（排除）：跑 `shadcn init` CLI — 會假設標準 Next 結構並覆寫 config，對既有自訂 export pipeline 風險高。
- 方案 C（排除）：Tailwind v3 + PostCSS — 可行但 v4 setup 更簡、CSS-first `@theme` 對品牌 token 更直接。

**Export Tailwind-inline 機制（REQ-SUI-003，最高風險，需先 spike）：**
1. `frontend/app/globals.css`：`@import "tailwindcss";` + `@theme { --color-brand-blue:#005EB8; ... }`（品牌 token）+ 既有/精煉的 component CSS。
2. Next build/dev：`@tailwindcss/postcss` plugin（`postcss.config.mjs`）→ `npm run build` 正常編譯。
3. Export：新增 npm script `build:export-css` = `npx @tailwindcss/cli -i app/globals.css -o .export-css/showcase.css --minify`（v4 自動掃描 content）。`export-public-demo.tsx` 讀 `.export-css/showcase.css` 並把內容 inline 成 `<head><style>…</style>`。`export:public-demo:docs` 先跑 `build:export-css` 再跑 export。
4. self-contained：CSS 全 inline，無外部 link/CDN（REQ-SUI-003 AC2）。

## 契約保留（不可破壞）

`buildVisualSnapshot`（`frontend/lib/public-demo.ts`）要求 rendered HTML 含每個 `data-section="${section}"` 與 `no_alpha_claim`/`local_demo_only`。shadcn 重構時，這些屬性/文字掛在對應 shadcn `<Card data-section=…>` 等容器上保留。frontend 測試（`dashboard.test.tsx` 等）斷言 DOM/section/claim → 重構後更新測試 DOM 但**不弱化** claim/section 斷言。

## Test Coverage Declaration

- frontend unit（vitest）：dashboard/section/claim/interactive/live-rerun 測試須全綠（更新 DOM 斷言；保留語意斷言）。
- governance guards（authority）：25 passed（count/visual/payload/parity sync）。
- static export 契約：`docs/index.html` == `dashboard-static-export.html` byte-parity；`showcase.visual.json` htmlHash 重新 pin。
- browser VRT：以新 UI 重拍 baseline（chromium），0-pixel diff 對新 baseline。
- build：`npm run build` 綠。
- 無 mock 取代真實渲染；static export 為真實 `renderToStaticMarkup`。

## Repo-side Closure vs External Execution Boundary

- Repo-side：實作 + 本地驗證（build/test/guards/export/VRT）。
- External：Pages 部署（合併後）+ live re-probe。dataHash 預期不變（資料不變）→ 若不變則 hosting 維持 proven、毋須翻 configured_not_observed；若 export manifest 因故改變 dataHash，走完整 2-phase（runbook）。
- Handoff authority：本 spec `review.md`。

## 契約定義

無新 runtime contract。`contract/live-rerun.schema.json` 等不變。新增的是 build/style 設定，非資料契約。dataHash 來源（`canonicalDashboardDataHash` = sha256(JSON.stringify(dashboard data)））不變。

## 組件和介面

| 元件 | 變更 |
|---|---|
| `frontend/app/globals.css` | 改為 Tailwind v4 entry + `@theme` 品牌 token + 精煉 component layer |
| `frontend/postcss.config.mjs` | 新增 `@tailwindcss/postcss` |
| `frontend/components/ui/*.tsx` | 新增 shadcn 原語（card/badge/table/separator…） |
| `frontend/components/Dashboard.tsx` + panels | 以 shadcn restyle，保留 data-section/claim |
| `frontend/scripts/export-public-demo.tsx` | 讀編譯後 CSS 並 inline 進 `<head>` |
| `frontend/package.json` | 新 deps + `build:export-css` script + 串接 export |

## Failure Mode and Effects Analysis (FMEA)

| Risk ID | Failure Mode | Effect | Cause | Control | Sev | Planned Response | Task Trace |
|---|---|---|---|---|---|---|---|
| FMEA-SUI-01 | 重構移除 `data-section`/claim label | `buildVisualSnapshot`/guards/tests 失敗或 false-green | shadcn 元件替換掉語意 hook | 契約保留規則 | High | **Prevent/Detect**：每個 section 容器保留 data-section + claim；export 後 grep 驗證所有 sections + no_alpha_claim/local_demo_only 仍在 | T-REFACTOR, T-VERIFY |
| FMEA-SUI-02 | export `<head>` 仍無 CSS / 引入外部 link | 部署檔無樣式或非 self-contained | Tailwind compile/inline 步驟失敗或誤用 CDN | spike 先驗證；grep 無外部 link | High | **Prevent**：先 spike compile+inline；closeout grep 無 `http`/`<link`/CDN，且 `<style>` 存在且非空 | T-SPIKE, T-VERIFY |
| FMEA-SUI-03 | dataHash 意外改變 → hosting 翻 configured_not_observed | 需完整 2-phase deploy；若漏做則 hosting 證明 stale | 誤改 showcase.json 資料 | dataHash 只依資料；不動 showcase.json | Med | **Detect**：export 後比對 manifest dataHash；若仍 6c18e572 則 hosting 維持；若變則走 runbook 2-phase | T-DEPLOY, T-VERIFY |
| FMEA-SUI-04 | frontend 測試弱化以「假綠」 | false-green | 為過測試刪 claim/section 斷言 | 測試只更新 DOM selector，不刪語意斷言 | Med | **Contain**：review 檢查測試 diff 未弱化 claim/section | T-TESTS, T-REVIEW |
| FMEA-SUI-05 | Tailwind inline CSS 過大 | 部署檔肥大 | 未 JIT / 含整包 utilities | v4 JIT 只含用到 class + `--minify` | Low | **Detect**：檢查 inline CSS 體積合理（<~50KB） | T-SPIKE |
| FMEA-SUI-06 | 新增 actionable/alpha 語句 | 違反 charter | UI 文案手滑 | no_alpha_claim 全程 | High | **Prevent**：closeout grep 無 buy-now/actionable | T-VERIFY |

## 評估標準 (EDD)

REQ-SUI-001..005 AC 全滿足；build 綠；frontend 測試綠（語意斷言保留）；guards 25；export self-contained inline CSS；VRT 重拍；dataHash 行為已驗證；`no_alpha_claim`。

## Governance Artifact Lifecycle

- Upstream truth：frontend 程式碼 + 測試 + export pipeline。
- Derived（closeout 寫入）：SPECS.md（Impacts F）、RTM.md、NEXT_STEPS.md。
- 不得讓 derived 反寫程式碼真相；不得弱化 guard/test 契約。

## 追溯參照

REQ-SUI-001→T-INFRA/T-SPIKE；002→T-REFACTOR/T-TESTS；003→T-SPIKE/T-EXPORT；004→T-VERIFY/T-DEPLOY；005→T-DOCS/closeout。
