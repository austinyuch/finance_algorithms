# Tasks — docs-enrichment-h-eda

> 鏡射 [design.md](./design.md) 的 repo-side closure 邊界（全部 repo-side，無 external execution）。每個 task 標 `[Implements REQ-…]`。Commit message 帶 `Ref: docs-enrichment-h-eda`。

## Design tokens (match + elevate)
brand palette `--blue:#005EB8 --sky:#04A9FB --orange:#FF6A39 --green:#97D700 --grey:#3B4559 --line:#e3e8f0`；hero dark `#0a0e1a/#13315c`；白卡 + 細邊；badge pass/cond/mock/base；EN/ZH `.en`/`.zh` 切換；mono `SF Mono/Menlo`。新 SVG 一律用此調色盤、self-contained、無 CDN。

## Tasks

- [x] **T-SVG-ASSETS** `[Implements REQ-DOCENRICH-001/002]` 設計 3 個可重用 inline-SVG 區塊（手寫、品牌調色盤）：
  - (a) Capability/data-flow map (A0→B→C→D→E→F→G→H, `no_alpha_claim` 標)
  - (b) Epic H pipeline (vintage→reference/torch→report→viz→static_replay→live_compute)
  - (c) DL OOS-net 排行水平條圖（multi-cycle 真值：Regime 0.669 / BuyAndHold 0.657(baseline) / Forecast 0.354 / Robust 0.321），caption: OOS-net-only · approximate-availability · 非 verdict · no_alpha_claim
- [x] **T-REVIEW** `[Implements REQ-DOCENRICH-001, REQ-DLEDA-001]` 在 `docs/review/index.html` 加入 (a)+(c) SVG + 一段 Epic H EDA 摘要卡（方法/指標/真實觀察/邊界），EN+ZH。
- [x] **T-MANUAL** `[Implements REQ-DOCENRICH-002, REQ-DLEDA-001]` 在 `docs/manual/{en,zh-tw}/index.html` 的 Epic H flows 加入 (b) pipeline SVG + (c) 排行圖 + EDA prose；`.md` 對應補充（inline SVG 或引用 `docs/manual/assets/*`）。EN/ZH 同步。
- [x] **T-FUTWORK** `[Implements REQ-FUTWORK-001]` design.md roadmap 已 author；在 review + manual 加一個精簡「Future work / Roadmap」可視區（表或卡），並確認 NEXT_STEPS pointer 已存在。Lane 2 標 charter-gated。
- [x] **T-GUIDES** `[Implements REQ-DOCENRICH-006]` 在 `docs/{MANUAL,REVIEW}_GENERATION_GUIDE.md` 各加小節（圖文並茂 SVG 來源 + Epic H EDA 數字 SSOT = committed report JSON），保留 deploy-coupling policy；AGENTS.md 確認已指向兩 guide（足夠則不膨脹）。
- [x] **T-VERIFY** `[Implements REQ-DOCENRICH-004]` closeout 驗證：
  - `git diff --name-only` 不含任何凍結檔（showcase.json×3 / manifest / probe×2 / index.html / dashboard-static-export.html / visual-snapshot.json / gate-*.txt / *.png / visual-baselines）
  - `uv run pytest tests/quantlab/test_governance_guards.py -q` = 25 passed
  - 三個 HTML well-formed 解析
  - grep 無新 CDN/外部 `src=`/`http(s)://…js`；無 current-asof/buy-now 語句；每張 DL 圖/段有 no_alpha_claim
  - EN/ZH 對齊抽查；DL 數字對回 artifact JSON

## FMEA Trace
FMEA-DE-01→T-VERIFY(frozen diff) · -02→T-REVIEW/T-MANUAL caption + T-VERIFY(no buy-now/數字 crosswalk) · -03→T-VERIFY(EN/ZH) · -04→T-SVG-ASSETS(inline only)+T-VERIFY(grep) · -05→T-VERIFY(well-formed) · -06→T-FUTWORK(charter 標)

## Completion Rule
全 task 勾選、T-VERIFY 全綠（guards 25 + frozen + well-formed + no-overclaim + EN/ZH）、`review.md` 裁決後，才進 Phase 5/6 registry + PR。
