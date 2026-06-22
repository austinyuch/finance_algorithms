# 需求文件 — Showcase Dashboard shadcn/Tailwind UI Upgrade (FW-DOC-VIS)

Spec ID: `h-showcase-shadcn-ui` · Epic: F (showcase) · Profile: `default` · Branch: `release/h-showcase-shadcn-ui`

## 介紹

把目前**未上樣式**的已部署 showcase 儀表板（`docs/index.html` — `export-public-demo.tsx` 產出的 className 語意 markup、`<head>` 無任何 CSS）升級為 **shadcn/Tailwind** 設計品質的視覺化儀表板，並**內嵌 (inline) 編譯後的 Tailwind CSS 到 self-contained 靜態匯出的 `<head>`**，使部署在 GitHub Pages 的單檔儀表板真正美觀。對應 roadmap **FW-DOC-VIS**。使用者已選擇「Full shadcn + Tailwind adoption」。

> **為何這些需求需要存在 (Ponytail Rung 1)**：使用者明確要求用 shadcn 升級 live dashboard。經調查發現 deployed `docs/index.html` 目前**完全沒有 CSS**（self-contained 匯出未注入樣式），所以這是真實且有價值的缺口，非 speculative。

## 相依、影響與變更請求

- [Depends On: f-public-static-showcase, f-nextjs-showcase-dashboard, f-browser-pixel-baseline, h-interactive-research-ui, h-live-rerun-api]
- [Impacts: f-public-static-showcase, f-nextjs-showcase-dashboard]（**deploy-coupled 視覺面變更**：static export HTML、static visual contract `showcase.visual.json` htmlHash、browser VRT baseline 會改變）→ 以本 active spec 承接，登錄為對 F baseline 的視覺升級（additive UI；不改 data/contract 語意）。
- [Open Change Requests: 無]（同 epic 內 UI 升級，非跨 immutable baseline 的契約變更；以本 spec 直接承接並在 SPECS 標 Impacts）

## Repo-side Closure vs External Execution

- **Repo-side Closure**: 全部實作（deps、Tailwind config、shadcn ui 元件、Dashboard 重構、export Tailwind-inline pipeline、tests、static-export/VRT 重新 pin、本地 guard/build 驗證）。
- **External Execution**: GitHub Pages 部署（合併 `dev`→`main` 後自動建置）+ 部署後 live re-probe。屬 deploy-coupled 2-phase（沿用 `deploy-coupled-payload-runbook`）。
- **External Blockers**: 需 headless Chromium 重拍 VRT（`/usr/bin/google-chrome` 可用）。

## Key Locked Decisions（不可違反）

- **保留 guard/test 契約**：重構必須保留每個 `data-section="..."` 標記、`no_alpha_claim` / `local_demo_only` claim labels、以及 `buildVisualSnapshot` 檢查的 sections 結構（`frontend/lib/public-demo.ts`）。restyle 不可移除這些語意 hook。
- **Self-contained 部署檔**：deployed `docs/index.html` 必須是單一 self-contained HTML——Tailwind CSS 以 **inline `<style>`** 注入 `<head>`，**無 CDN、無外部 `<link>`/`<script src>`**。
- **dataHash 不變**：dashboard **資料 (showcase.json)** 不變 → `dataHash` 維持 `6c18e572`（hosting 仍 proven）；只有 rendered HTML / visual contract / VRT screenshot 改變並需重新 pin。
- **`no_alpha_claim` 全程**：UI 升級不得新增任何 actionable/buy-now 訊息。
- **counts 同步**：若 frontend 測試數因新增 ui 元件測試而變動，須跨所有 guard-coupled count surface 同步（478/70→新值）；否則維持。
- **品牌一致**：shadcn theme tokens 對齊既有品牌色（--blue #005EB8 / --sky #04A9FB / --orange #FF6A39 / --green #97D700 / --grey #3B4559）。

## 需求

### 需求 1 [REQ-SUI-001] — Tailwind + shadcn 基礎設施

**用戶故事：** 作為前端維護者，我希望 frontend/ 具備 Tailwind + shadcn 基礎，以便用一致的設計系統建構儀表板 UI。

#### 驗收標準

1. The frontend shall 加入 Tailwind（+ PostCSS/autoprefixer 或 Tailwind v4 等價設定）與 shadcn 所需基礎（`class-variance-authority`、`tailwind-merge`、`clsx`、`lucide-react`，radix 視需要），並設定品牌色 theme tokens。
2. The repo shall 新增最小集合的 shadcn UI 原語於 `frontend/components/ui/`（至少 Card、Badge、Table、Separator；視需要 Tabs/Select 的 presentational 版本）。
3. When 執行 `npm run build`，Next.js 建置 shall 成功（Tailwind 正確編譯）。

### 需求 2 [REQ-SUI-002] — Dashboard 以 shadcn 重構（保留契約）

**用戶故事：** 作為 stakeholder，我希望 live dashboard 視覺精緻（卡片、表格、badge、層次分明），以便這個 demo 看起來是 production-grade。

#### 驗收標準

1. The Dashboard 與主要 panels（header、leaderboard、allocation、charts、evidence、readiness、experiments、real-data、interactive、live-rerun）shall 以 shadcn Card/Badge/Table/Separator 等重構，達到精緻、品牌一致、非通用 AI 美學的視覺品質。
2. The 重構 shall 保留所有 `data-section="..."` 屬性、`no_alpha_claim`/`local_demo_only` labels、以及既有 section 結構（`buildVisualSnapshot` 與 frontend 測試所依賴者）。
3. The 重構 shall 維持 chart.js 圖表（InvestmentCharts）功能（dev/build 路徑）與既有資料呈現語意不變。
4. When 執行既有 frontend 測試，所有測試 shall 通過（必要時更新測試以反映新 DOM，但不得弱化 claim/section 斷言）。

### 需求 3 [REQ-SUI-003] — 靜態匯出 Tailwind-inline pipeline

**用戶故事：** 作為部署維護者，我希望 self-contained 的 `docs/index.html` 內嵌編譯後的 Tailwind CSS，以便 Pages 上的單檔儀表板真正有樣式且無外部相依。

#### 驗收標準

1. The export pipeline (`frontend/scripts/export-public-demo.tsx` 或新增 build step) shall 編譯 Tailwind（僅掃描實際使用的 class，JIT）成 CSS 字串，並 inline 注入匯出 HTML 的 `<head>` `<style>`。
2. The 匯出的 `docs/index.html` shall 無任何 CDN / 外部 `<link rel=stylesheet>` / 外部 `<script src>`；CSS 全部 inline。
3. The 匯出 shall 維持 `docs/index.html` == `docs/manual/assets/dashboard-static-export.html` byte-parity（guard），並更新 static visual contract baseline（`frontend/visual-baselines/showcase.visual.json` htmlHash）。
4. When 在 file:// / headless 開啟匯出檔，dashboard shall 正確上樣式渲染。

### 需求 4 [REQ-SUI-004] — Deploy-coupled 重新 pin 與 guard 安全

**用戶故事：** 作為維護者，我希望 UI 升級乾淨通過所有 governance guards 並正確走 deploy-coupled 流程，以便不產生 false-green 或破壞 hosting 證明。

#### 驗收標準

1. When 執行 `uv run pytest tests/quantlab/test_governance_guards.py -q`，系統 shall 25 passed（必要時同步 count surfaces、visual evidence、payload-sync guards）。
2. The browser VRT baseline（`docs/browser-visual.png` + diff + review/manual copies）shall 以新 UI 重拍並同步（0-pixel diff 對新 baseline）。
3. The `dataHash` shall 維持 `6c18e572`（資料不變）；hosting probe 維持 proven（除非 export 的 manifest 也納入 htmlHash 影響——若 dataHash 真的改變，則走完整 2-phase deploy + live re-probe）。
4. The 變更 shall 全程 `no_alpha_claim`，無 actionable surface。

### 需求 5 [REQ-SUI-005] — 文件與生成指南同步

#### 驗收標準

1. The `docs/{MANUAL,REVIEW}_GENERATION_GUIDE.md` shall 簡述新的 shadcn/Tailwind UI + Tailwind-inline export pipeline 與其 source-of-truth。
2. The SDD artifacts（design/tasks/review）、SPECS.md（Impacts F）、RTM.md、NEXT_STEPS.md shall 於 closeout 更新。

## 成功標準

- live Pages dashboard 以 shadcn/Tailwind 精緻上樣式（self-contained inline CSS）；保留所有 data-section/claim 契約；guards 25 passed；VRT 重拍；`no_alpha_claim`；deploy-coupled 流程正確（dataHash 行為已驗證）。

## 邊緣情況與約束

- 靜態匯出無 client JS hydration → shadcn 互動原語在匯出檔僅呈現 presentational 狀態（可接受，dashboard 為 static_replay）。
- Tailwind inline CSS 體積須受控（JIT 只含用到的 class）。
- Lightweight FMEA 於 Phase 2 必做（deploy-coupled stakeholder artifact + 契約保留風險）。
