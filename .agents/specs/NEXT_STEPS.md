# NEXT_STEPS.md — Rolling Operational Memo

> 高階、滾動、可覆寫。跨 spec 當前狀態與恢復點。詳細真相見各 spec artifact。

## Current State (2026-06-11)

- **Current branch lane:** `spec/d-first-regime-model`. Future `main` updates should go through PR/squash flow, not direct push.
- **Latest local evidence:** `uv run pytest -q` → **114 passed**; `uv run mypy quantlab/ --ignore-missing-imports` → clean(38 files); `uv run lint-imports` → KEPT.
- **ISSUE-B3-001 handled in advance:**
  - Promoted/folded into [CR-B7 source health](./b-data-platform/change-requests/cr-b7-source-health.md) for invalid FRED gold proxy defaults.
  - Repo-side fix: default FRED price proxy list now uses reachable `PCOPPUSDM` commodity proxy instead of invalid London gold IDs.
  - Residual: Stooq/TSMC remains external/source-contract blocked until a verified endpoint/source pin captures non-empty close rows.
- **Epic D first slice:** [d-first-regime-model](./d-first-regime-model/) is **Implemented(first slice) · Review PASSED**.
  - Added `RegimeSignal`, `RegimeFeatureBuilder`, `FirstRegimeClassifier`, and `RegimeAllocationStrategy`.
  - Targeted D evidence: 6 tests for PIT-safe signal and OOS-net baseline integration.
  - Conservative writeup: synthetic data proves pipeline correctness only; no alpha claim.
- **Epic C next dependency:** C-3 time/regime rebalance remains planned and can now consume the D regime signal contract additively.

## Recommended Next Action

1. Open PR for this branch after a final `git diff --check` / staged review.
2. Next implementation slice: continue `c-portfolio-core` C-3 time-based rebalance plus optional consumption of D `RegimeSignal`.
3. If data-source work is prioritized instead, resolve residual Stooq/TSMC by selecting a verified replacement endpoint/source pin before another B CR.

## Scheduled Ops

- Daily vintage snapshot routine is expected to continue writing append-only files under `data/vintage/raw/<date>/`.
- Current live proof says routine/source health is partial, not fully proven for Stooq/TSMC.

## Resume Hints

- For D closure truth, read [d-first-regime-model/review.md](./d-first-regime-model/review.md), [writeup.md](./d-first-regime-model/writeup.md), and [reports/implementation-report.md](./d-first-regime-model/reports/implementation-report.md).
- For B-3 source status, read [ISSUE_LOG.md](./ISSUE_LOG.md) and [b-data-platform/change-requests/cr-b7-source-health.md](./b-data-platform/change-requests/cr-b7-source-health.md).
- For test truth, read [quantlab/TESTS.md](../../quantlab/TESTS.md) then [.agents/specs/TESTS.md](./TESTS.md).

## Key Locked Decisions

- 個人自用純紙上;成功=方法論誠實度 + 實驗能力,非 alpha;雙目的(作品集 + lab)→ 兩速結構。
- 每模型 DoD:A0 產出「可與笨 baseline 並排比較的 OOS 報告」。
- 三框架(PyTorch/TF/JAX)harness 無感;Tier1+2 進 A0,Tier3(完整 MLOps)延後。
