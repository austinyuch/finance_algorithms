# NEXT_STEPS.md — Rolling Operational Memo

> 高階、滾動、可覆寫。跨 spec 當前狀態與恢復點。詳細真相見各 spec artifact。

## Current State (2026-06-10)
- **A0 epic:** DONE、已 merged 進 main(PR #1)。
- **Epic A:** **DONE(Review PASSED)**。分支 `spec/a-tsmc-hedge-slice`(off main),**11 commits 未 push**。
- **Epic A 全部完成:** A-1 篩選 / A-2 LSTM(torch)/ A-3 baseline / A-4 對衝 / A-5 整合 / A-6 writeup。全套 **83 tests passed**,mypy clean(29 檔)。verdict 見 [a-tsmc-hedge-slice/review.md](./a-tsmc-hedge-slice/review.md)。
- **誠實 slice 結果(合成資料):** LSTM tie buy&hold、對衝降 Sharpe、隨機地板;未宣稱 alpha。重現 `uv run python scripts/run_tsmc_hedge_slice.py`。
- **Next action:** (a) push/PR `spec/a-tsmc-hedge-slice`;或 (b) 進 **Epic B**(真實資料源接入,把合成 provider 換成真實 PIT 資料,即可重跑同一 slice);或 (c) 補 residual。
- **反指標定義(已鎖):** 共整合 + 反向 spread。資料合成先行(strategy C)。
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
