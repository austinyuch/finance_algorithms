# Tasks — h-showcase-shadcn-ui

> Mirrors design.md repo-side closure (all repo-side; external = Pages auto-build, dataHash unchanged → no re-probe).

- [x] **T-SPIKE** `[REQ-SUI-001/003]` Tailwind v4 install + postcss + @theme tokens; validate `npm run build`; CLI compile; export inline `<style>` wiring (`build:export-css` + export reads `.export-css/showcase.css`).
- [x] **T-INFRA+REFACTOR** `[REQ-SUI-002]` `components/ui/{card,badge,table,separator}` + `lib/utils.cn`; restyle Dashboard + InvestmentCharts + InteractiveResearchPanel + LiveRerunStatus; preserve all `data-section` + claim labels.
- [x] **T-TESTS+EXPORT** `[REQ-SUI-002/003]` update frontend tests for new DOM (keep claim/section assertions, 70 unchanged); export inlines CSS; re-pin static visual contract baseline + byte-parity sync.
- [x] **T-VERIFY** `[REQ-SUI-004]` browser VRT re-pinned to styled render (af37e49c, 0-pixel); guards 25; build+CI tests green; frozen data files unchanged (dataHash 6c18e572 / probe proven); traceability hash refs updated.
- [x] **T-DOCS** `[REQ-SUI-005]` review.md + SPECS(Impacts F)/RTM/NEXT_STEPS + generation-guide notes.
- [ ] **T-DEPLOY** PR→main, CI+Copilot, merge, ff dev; Pages serves styled docs/index.html (dataHash unchanged → hosting stays proven, no re-probe).

## FMEA Trace
FMEA-SUI-01→T-REFACTOR/T-VERIFY · -02→T-SPIKE/T-VERIFY · -03→T-VERIFY · -04→T-TESTS/review · -05→T-SPIKE · -06→T-REFACTOR/T-VERIFY
