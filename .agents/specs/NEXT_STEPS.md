# NEXT_STEPS.md — Rolling Operational Memo

> 高階、滾動、可覆寫。跨 spec 當前狀態與恢復點。詳細真相見各 spec artifact。

## Current State (2026-06-11)

- **Main local evidence:** `uv run pytest -q` → **108 passed**; `uv run mypy quantlab/ --ignore-missing-imports` → clean(36 files); `uv run lint-imports` → KEPT.
- **Governance sync completed:** `quantlab/TESTS.md` refreshed as row-level test catalog; `.agents/specs/TESTS.md` added as workspace rollup; `SPECS.md` updated for C-2 and D first-model spec.
- **Epic B B-3 proof attempt:** `uv run python scripts/daily_snapshot.py` captured partial FRED/NOAA data under `data/vintage/raw/2026-06-11/` but exited 1. All configured Stooq symbols, including `2330.tw`, returned HTTP 404; configured FRED gold proxy returned HTTP 404; several FRED series timed out.
  - Tracking surface: [ISSUE_LOG.md](./ISSUE_LOG.md) `ISSUE-B3-001`.
  - Current classification: B remains repo-side Review PASSED; B-3 external/source-contract proof is not closed for Stooq/TSMC.
- **Epic C:** `c-portfolio-core` is **Implemented(core+C-2) · Review PASSED**.
  - C-2 added `HorizonConfig` + `MultiHorizonMeanVarianceStrategy`, with 3 tests in `test_c_2_multihorizon`.
  - C-3 time/regime rebalance remains planned; regime hook depends on Epic D.
- **Epic D:** [d-first-regime-model](./d-first-regime-model/) is created with requirements/design/tasks. Scope is a deterministic PIT-safe first regime classifier, OOS-net baseline comparison, and future C-3 additive hook. Tier3 MLOps remains deferred.

## Recommended Next Action

1. Start implementation for [d-first-regime-model/tasks.md](./d-first-regime-model/tasks.md) Task 1, unless B-3 source correction is prioritized.
2. If B-3 source correction is prioritized, promote `ISSUE-B3-001` to a B CR overlay only after selecting replacement source symbols/URLs or source pins that require repo changes.
3. After D first-model implementation, return to C-3 for time-based rebalance plus optional regime hook consumption.

## Scheduled Ops

- Daily vintage snapshot routine is expected to continue writing append-only files under `data/vintage/raw/<date>/`.
- Current live proof says routine/source health is partial, not fully proven for Stooq/TSMC.

## Resume Hints

- For governance/test truth, read [quantlab/TESTS.md](../../quantlab/TESTS.md) then [.agents/specs/TESTS.md](./TESTS.md).
- For B-3 source status, read [ISSUE_LOG.md](./ISSUE_LOG.md) and [b-data-platform/review.md](./b-data-platform/review.md).
- For next model work, read [d-first-regime-model/requirements.md](./d-first-regime-model/requirements.md), [design.md](./d-first-regime-model/design.md), and [tasks.md](./d-first-regime-model/tasks.md).

## Key Locked Decisions

- 個人自用純紙上;成功=方法論誠實度 + 實驗能力,非 alpha;雙目的(作品集 + lab)→ 兩速結構。
- 每模型 DoD:A0 產出「可與笨 baseline 並排比較的 OOS 報告」。
- 三框架(PyTorch/TF/JAX)harness 無感;Tier1+2 進 A0,Tier3(完整 MLOps)延後。
