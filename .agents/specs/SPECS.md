# SPECS.md — Feature Registry & Dependency Map

> Workspace 規格總目錄與相依地圖(穩定治理登錄表)。不承載即時 branch 狀態。
> 滾動操作狀態見 [NEXT_STEPS.md](./NEXT_STEPS.md)。

## Program: Portfolio-grade 個人 Quant 研究 Lab

程式級 problem-space 與 epic 分解(非 SDD spec,為 program 規劃 artifact):
- [allweather-portfolio-platform/01-problem-space.md](./allweather-portfolio-platform/01-problem-space.md)
- [allweather-portfolio-platform/02-epic-breakdown.md](./allweather-portfolio-platform/02-epic-breakdown.md)

## Spec Registry

| Spec | Epic | Lifecycle | Depends On | Impacts | Open CRs | Lane |
|---|---|---|---|---|---|---|
| [a0-backtest-foundation](./a0-backtest-foundation/) | A0 | **Implemented · Review PASSED**(7/7 task, 66 tests, mutation 5/5) | — (greenfield 地基) | (未來)A,B,C,D,E,F,G 全依賴其介面 | — | `spec/a0-backtest-foundation` |
| [a-tsmc-hedge-slice](./a-tsmc-hedge-slice/) | A | **Implemented · Review PASSED**(6/6 task, 83 tests) | a0-backtest-foundation | a0(history() + metrics 防護,additive) | — | `spec/a-tsmc-hedge-slice` |
| [b-data-platform](./b-data-platform/) | B | **In Progress**(B-1/B-2 merged:vintage loader + FRED 價格代理) | a0-backtest-foundation | a0(history()/metrics 已 additive;B-5 將提 `pit_strictness` CR) | B-5 pit_strictness(規劃中) | `spec/b-data-platform` |
| _c-portfolio-core_ | C | Planned | b-data-platform | invest_algorithms/algo_pyramid(進場整合) | — | (TBD) |
| _d-ml-models_ | D | Planned | b, c, a0 | — | — | (TBD) |
| _e-mlops-tier3_ | E | Deferred(R3) | d | — | — | (TBD) |
| _f-frontend_ | F | Planned | a0(read API) | — | — | (TBD) |
| _g-alt-data_ | G | Optional | a0 | — | — | (獨立 optional lane) |

## 治理註記
- **A0 = 關鍵路徑起點**;其 `contract/` 介面一旦穩定會被全 program 依賴 → 變更需走 CR overlay。
- 既有模組 `invest_algorithms/`(FastAPI + algo_pyramid)為 **immutable 既有基線**;A0 不修改它,僅在其上建立新地基。未來 Epic C 的進場整合會以 `[Impacts: invest_algorithms/algo_pyramid]` 宣告。
- External contract authority:資料源(Yahoo/FRED/證交所/主計總處/央行/氣候)屬 **external**,將於 Epic B 登錄 Source of Truth / Pin。
