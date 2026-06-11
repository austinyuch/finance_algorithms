# NEXT_STEPS.md — Rolling Operational Memo

> 高階、滾動、可覆寫。跨 spec 當前狀態與恢復點。詳細真相見各 spec artifact。

## Current State (2026-06-11)

- **Current branch lane:** `spec/d-first-regime-model`. Future `main` updates should go through PR/squash flow, not direct push.
- **Latest local evidence:** `uv run pytest -q` → **123 passed**; `uv run mypy quantlab/ --ignore-missing-imports` → clean(39 files); `uv run lint-imports` → KEPT.
- **PR:** branch PR opened at `https://github.com/austinyuch/finance_algorithms/pull/7`.
- **ISSUE-B3-001 handled in advance:**
  - Promoted/folded into [CR-B7 source health](./b-data-platform/change-requests/cr-b7-source-health.md) for invalid FRED gold proxy defaults.
  - Repo-side fix: default FRED price proxy list now uses reachable `PCOPPUSDM` commodity proxy instead of invalid London gold IDs.
  - Promoted/folded into [CR-B8 Yahoo chart fallback](./b-data-platform/change-requests/cr-b8-yahoo-chart-fallback.md) for TSMC/TWSE fallback capture and PIT loading.
  - Residual: Stooq itself remains external/source-contract blocked; TSMC/TWSE fallback is now live-smoke proven through Yahoo chart from this environment.
- **Epic D first slice:** [d-first-regime-model](./d-first-regime-model/) is **Implemented(first slice) · Review PASSED**.
  - Added `RegimeSignal`, `RegimeFeatureBuilder`, `FirstRegimeClassifier`, and `RegimeAllocationStrategy`.
  - Targeted D evidence: 6 tests for PIT-safe signal and OOS-net baseline integration.
  - Conservative writeup: synthetic data proves pipeline correctness only; no alpha claim.
- **Epic C C-3:** time/regime rebalance selector implemented additively in `quantlab/portfolio/rebalance.py`; no A0 engine scheduling change.

## Recommended Next Action

1. Run `git diff --check`, stage only this slice, commit, and push to PR #7.
2. Next implementation slice: decide whether to add A0 engine-level event scheduling for regime-triggered rebalances or move to the next model/data priority.
3. Keep Stooq-specific work blocked unless restoring/removing Stooq itself becomes a priority.

## Scheduled Ops

- Daily vintage snapshot routine is expected to continue writing append-only files under `data/vintage/raw/<date>/`.
- Current live proof says routine/source health is partial: Yahoo fallback is proven for `2330.TW` and `^TWII` on 2026-06-11; Stooq remains blocked.

## Resume Hints

- For D closure truth, read [d-first-regime-model/review.md](./d-first-regime-model/review.md), [writeup.md](./d-first-regime-model/writeup.md), and [reports/implementation-report.md](./d-first-regime-model/reports/implementation-report.md).
- For B-3 source status, read [ISSUE_LOG.md](./ISSUE_LOG.md), [b-data-platform/change-requests/cr-b7-source-health.md](./b-data-platform/change-requests/cr-b7-source-health.md), and [b-data-platform/change-requests/cr-b8-yahoo-chart-fallback.md](./b-data-platform/change-requests/cr-b8-yahoo-chart-fallback.md).
- For C-3 closure truth, read [c-portfolio-core/reports/c3-rebalance-report.md](./c-portfolio-core/reports/c3-rebalance-report.md).
- For test truth, read [quantlab/TESTS.md](../../quantlab/TESTS.md) then [.agents/specs/TESTS.md](./TESTS.md).

## Key Locked Decisions

- 個人自用純紙上;成功=方法論誠實度 + 實驗能力,非 alpha;雙目的(作品集 + lab)→ 兩速結構。
- 每模型 DoD:A0 產出「可與笨 baseline 並排比較的 OOS 報告」。
- 三框架(PyTorch/TF/JAX)harness 無感;Tier1+2 進 A0,Tier3(完整 MLOps)延後。
