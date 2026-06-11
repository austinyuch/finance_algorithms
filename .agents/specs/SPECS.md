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
| [a0-backtest-foundation](./a0-backtest-foundation/) | A0 | **Implemented · Review PASSED**(7/7 task;CR-A0 regime scheduling;mutation automation) | — (greenfield 地基) | (未來)A,B,C,D,E,F,G 全依賴其介面;C-3/D regime scheduling | — (CR-A0 Implemented) | `spec/a0-backtest-foundation` |
| [a-tsmc-hedge-slice](./a-tsmc-hedge-slice/) | A | **Implemented · Review PASSED**(6/6 task, 83 tests) | a0-backtest-foundation | a0(history() + metrics 防護,additive) | — | `spec/a-tsmc-hedge-slice` |
| [b-data-platform](./b-data-platform/) | B | **Implemented(repo-side)· Review PASSED**(B-1/2/4/5;B-3 bulk=真機 handoff;CR-B7/B8/B9/B10/B11 source policy/status/reporting) | a0-backtest-foundation | a0(history()/metrics additive;**CR-B5** pit_strictness additive schema); snapshot source defaults/status(CR-B7/CR-B8/CR-B9/CR-B10); run report(CR-B11) | — (CR-B5/CR-B7/CR-B8/CR-B9/CR-B10/CR-B11 Implemented);residual `ISSUE-B3-001` for Stooq availability only | `spec/b-data-platform`; `spec/next-gaps-4-3-1-2-5` |
| [c-portfolio-core](./c-portfolio-core/) | C | **Implemented(core+C-2+C-3)· Review PASSED**(C-1/2/3/4/5) | b-data-platform,d-first-regime-model(C-3 hook) | invest_algorithms/algo_pyramid(C-4 additive adapter,未改其行為); D regime signal consumed by C-3 selector | — | `spec/c-portfolio-core` |
| [d-first-regime-model](./d-first-regime-model/) + [d-return-risk-forecast-model](./d-return-risk-forecast-model/) + [d-robust-portfolio-optimization-model](./d-robust-portfolio-optimization-model/) | D | **Implemented(3 model families)· Review PASSED**(OOS-net baselines; no alpha claim; no Tier3) | a0-backtest-foundation,b-data-platform,c-portfolio-core | c-portfolio-core(C-3 regime hook consumed additively); A0 regime scheduling; F showcase payloads; E readiness input | — | `spec/d-first-regime-model`; `spec/f-showcase-and-d-return-risk` |
| [_e-mlops-tier3_](./e-mlops-tier3-readiness.md) + [e-mlops-tier3-lite](./e-mlops-tier3-lite/) + [e-f-registry-dashboard-bridge](./e-f-registry-dashboard-bridge/) | E | **Implemented(E-lite registry + dashboard bridge) · Review PASSED**(registry-only; no serving/retraining/drift yet) | d(3 model families),f-showcase-read-api-dashboard | experiment registry / config catalog / F dashboard read API | — | `spec/e-lite-source-f-hardening`; `spec/next-gaps-4-3-1-2-5` |
| [f-showcase-read-api-dashboard](./f-showcase-read-api-dashboard/) + [f-nextjs-showcase-dashboard](./f-nextjs-showcase-dashboard/) + [f-demo-hardening](./f-demo-hardening/) + [f-public-demo-readiness](./f-public-demo-readiness/) | F | **Implemented(local Next.js runtime + demo honesty + clean local production smoke)· Review PASSED**(local HTTP smoke; audit clean; public hosting/visual regression deferred) | a0(read API),c-portfolio-core,d-first-regime-model,d-return-risk-forecast-model,d-robust-portfolio-optimization-model,e-mlops-tier3-lite | QuantLab result-store/read surface; E registry display; no legacy API behavior change | — | `spec/f-showcase-and-d-return-risk`; `spec/e-lite-source-f-hardening`; `spec/next-gaps-4-3-1-2-5` |
| [g-alt-data-first-slice](./g-alt-data-first-slice/) | G | **Implemented(first slice) · Review PASSED**(optional, default-disabled, source-contract-first local CSV loader) | a0-backtest-foundation,b-data-platform(source-contract policy) | future model/source expansion; no default daily snapshot source enabled | — | `spec/next-gaps-4-3-1-2-5` |

## 治理註記
- **A0 = 關鍵路徑起點**;其 `contract/` 介面一旦穩定會被全 program 依賴 → 變更需走 CR overlay。
- 既有模組 `invest_algorithms/`(FastAPI + algo_pyramid)為 **immutable 既有基線**;A0 不修改它,僅在其上建立新地基。未來 Epic C 的進場整合會以 `[Impacts: invest_algorithms/algo_pyramid]` 宣告。
- External contract authority:資料源(Yahoo/FRED/證交所/主計總處/央行/氣候)屬 **external**,將於 Epic B 登錄 Source of Truth / Pin。
