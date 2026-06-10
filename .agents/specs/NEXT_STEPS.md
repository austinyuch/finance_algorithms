# NEXT_STEPS.md — Rolling Operational Memo

> 高階、滾動、可覆寫。跨 spec 當前狀態與恢復點。詳細真相見各 spec artifact。

## Current State (2026-06-11)
- **已 merged 進 main:** A0(PR #1)、Epic A(PR #2)、residual hardening(PR #3)、Epic B B-1/B-2(PR #4)。main 全套 **91 passed**、mypy clean(30 檔)、import-linter KEPT。
- **Active spec:** `b-data-platform`(Epic B)— **Implemented(repo-side)· Review PASSED**。lane `spec/b-data-platform-cont`(未 push)。
- **Epic B 完成:** B-1 loader / B-2 FRED 價格代理 / B-4 as-of 對齊 / B-5 pit_strictness(**CR-B5** overlay,已 Implemented) / B-6 review。**B-3 bulk = 真機 handoff**(FRED 全史已被 snapshot 涵蓋;Stooq/個股待真機)。verdict 見 [b-data-platform/review.md](./b-data-platform/review.md)。
- **B-2 已啟用:** daily_snapshot 加 FRED 價格代理,cron 累積真實價格中(繞過 Stooq 404)。
- **Next action:** push/PR/merge `spec/b-data-platform-cont`;之後可進 **Epic C(組合最佳化)** 或等真機累積真實價格後重跑 Epic A slice。
- **Residual 狀態:** ✅ import-linter + drift-guard(PR #3)。延後(環境阻擋):MLflow(Py3.13)、mutmut 自動化、三框架真機 GPU。
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
