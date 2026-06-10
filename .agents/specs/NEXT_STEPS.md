# NEXT_STEPS.md — Rolling Operational Memo

> 高階、滾動、可覆寫。跨 spec 當前狀態與恢復點。詳細真相見各 spec artifact。

## Current State (2026-06-10)
- **Active spec:** `a0-backtest-foundation` — **DONE(Review PASSED)**。分支 `spec/a0-backtest-foundation`,9 commits 未 push。
- **A0 epic 完成:** 7/7 task(A0-0~A0-6),**66 tests passed**,mypy clean(24 檔),mutation spot-check 5/5。verdict 見 [a0-backtest-foundation/review.md](./a0-backtest-foundation/review.md)。
- **Next action(新工作):** (a) push/PR `spec/a0-backtest-foundation` lane;或 (b) 進 **Epic A**(反台積電對衝 thin slice,作品集中心),依賴 A0 已就緒;或 (c) 補 A0 residual(MLflow backend、import-linter、mutmut 自動化、三框架真機驗證)。
- **A0 residual(刻意降級,非阻塞,見 review.md §Residual):** MLflow 延後(現 SQLite LocalResultStore);三框架 env 僅宣告;成本僅周轉型;mutation 手動;import-linter / drift-guard 待辦。
- **Loop:** A0 實作目標已達成 → 自主 loop 在此收束(spec 已 implemented)。
- **Blockers:** 無。技術已鎖定:追蹤=MLflow(local);平行=joblib-first 預留 Ray;引擎=向量化先行;codegen=datamodel-codegen(--enum-field-as-literal --field-constraints,mypy 相容)。
- **待補(非阻塞):** import-linter 正式化框架隔離(目前用 AST 測試守住);spec contract/interfaces.py ↔ quantlab/contracts/interfaces.py drift-guard 測試。
- **Lane hint:** A0 為地基,動實作碼前先開 `spec/a0-backtest-foundation` 分支(目前在 main,tree 乾淨)。

## Scheduled Ops
- **每日 vintage snapshot routine 已上線**:`trig_01G7GG93ELcs2x98GvxDcjdD`(台灣 08:00 / 00:00 UTC),跑 `scripts/daily_snapshot.py` → commit+push `data/vintage/raw/<date>/` 到 main。首次執行 2026-06-10 08:00。
  - 管理:https://claude.ai/code/routines/trig_01G7GG93ELcs2x98GvxDcjdD
  - 已 push 到 main:snapshot 腳本 + test(9 綠)+ 治理政策 + program 規劃文件 + 首日 seed 資料(commit 98d47b8)。
  - 待真機驗證:Stooq symbol/URL(沙箱回 404);FRED 偶發逾時(transient)。
  - 隔日檢查點:確認 routine 有成功 commit 當日 snapshot;留意失敗源。

## Resume Hints
- 先讀 [SPECS.md](./SPECS.md) → 本檔 → [a0-backtest-foundation/requirements.md](./a0-backtest-foundation/requirements.md)
- Program 脈絡:[allweather-portfolio-platform/01-problem-space.md](./allweather-portfolio-platform/01-problem-space.md)(含完整 decision log 與風險 R1/R2/R3)

## Key Locked Decisions(影響所有後續 spec)
- 個人自用純紙上;成功=方法論誠實度 + 實驗能力,非 alpha;雙目的(作品集 + lab)→ 兩速結構。
- 每模型 DoD:A0 產出「可與笨 baseline 並排比較的 OOS 報告」。
- 三框架(PyTorch/TF/JAX)harness 無感;Tier1+2 進 A0,Tier3(完整 MLOps)延後。
