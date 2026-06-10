# NEXT_STEPS.md — Rolling Operational Memo

> 高階、滾動、可覆寫。跨 spec 當前狀態與恢復點。詳細真相見各 spec artifact。

## Current State (2026-06-10)
- **A0 epic:** DONE、**已 merged 進 main**(PR #1,merge commit eba4004)。
- **Active spec:** `a-tsmc-hedge-slice`(Epic A,作品集中心)。分支 `spec/a-tsmc-hedge-slice`(off main),4 commits 未 push。
- **Epic A 進度:** A-1 共整合-反向篩選 ✅ · A-3 笨 baseline 群 ✅ · A-4 對衝部位建構 ✅(含降波動 showcase)。全套 **77 tests passed**,mypy clean(28 檔)。
- **Next action:** A-2 LSTM 訊號(**需裝 PyTorch ~數百 MB**,屆時確認)→ A-5 整合 leaderboard(HedgeStrategy vs baselines)→ A-6 一頁誠實 writeup。
- **反指標定義(已鎖):** 共整合 + 反向 spread(Engle-Granger,hedge ratio<0)。資料合成先行(strategy C)。
- **A0 residual(見 a0 review.md):** MLflow 延後(現 SQLite)、三框架 env 僅宣告、成本僅周轉型、mutation 手動、import-linter/drift-guard 待辦。
- **高階計畫:** [allweather-portfolio-platform/](./allweather-portfolio-platform/)(problem-space + epic-breakdown + 資料治理)。

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
