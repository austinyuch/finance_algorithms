# Review — h-showcase-shadcn-ui

## Verdict

**PASSED (repo-side · deploy-coupled visual upgrade).** The deployed showcase dashboard is upgraded to a polished shadcn/Tailwind UI with **self-contained inlined CSS** in the static export; all guard/test contracts preserved; `dataHash` unchanged (`6c18e572`) so public hosting stays `proven` (no 2-phase re-probe). All governance guards green; frontend CI tests + build green; browser VRT re-pinned to the new styled render.

## Scope delivered (vs requirements)

| REQ | Delivered | Evidence |
|---|---|---|
| REQ-SUI-001 (Tailwind+shadcn infra) | Tailwind v4 + @tailwindcss/postcss + @tailwindcss/cli + cva/clsx/tailwind-merge/lucide-react; `@theme` brand tokens; `components/ui/{card,badge,table,separator}.tsx` + `lib/utils.ts` `cn()` | `npm run build` ✓; deps audit 0 vulns |
| REQ-SUI-002 (Dashboard shadcn restyle, contracts kept) | Dashboard + InvestmentCharts + InteractiveResearchPanel + LiveRerunStatus restyled; **all 7 `data-section` + claim labels preserved** | frontend tests pass; grep: 7 data-sections + 7 claim strings present in docs/index.html |
| REQ-SUI-003 (export Tailwind-inline) | `build:export-css` (tailwindcss CLI) → `export-public-demo.tsx` inlines compiled CSS into `<head><style>`; self-contained, no CDN/external link | docs/index.html carries ~25KB inline `<style>`; export PASS |
| REQ-SUI-004 (deploy-coupled re-pin + guards) | static visual contract baseline re-pinned (showcase.visual.json htmlHash); byte-parity synced; browser VRT re-pinned to styled render (hash af37e49c, 0-pixel); guards 25 | `git diff` frozen data files unchanged; guards 25 passed |
| REQ-SUI-005 (docs/registry) | guides note + SPECS(Impacts F)/RTM/NEXT_STEPS closeout | this closeout |

## FMEA residual check (design.md)

- **FMEA-SUI-01 (lost data-section/claim)** — mitigated: grep confirms all 7 data-sections + no_alpha_claim/static_replay/research_mode_approximate_availability/registry_only/local_runtime_only/not_proven/local_demo_only in docs/index.html; frontend tests' section/claim assertions pass. ✓
- **FMEA-SUI-02 (no CSS / external link)** — mitigated: docs/index.html has inline `<style>` (compiled Tailwind), no CDN/external `<link>`/`<script src>`. ✓
- **FMEA-SUI-03 (dataHash drift)** — mitigated: data unchanged → dataHash stays `6c18e572`; showcase.json ×3 + probe ×2 + manifest dataHash byte-unchanged; hosting stays proven (no re-probe). ✓
- **FMEA-SUI-04 (weakened tests)** — mitigated: tests updated for new DOM but claim/section/aria assertions retained. ✓
- **FMEA-SUI-05 (CSS bloat)** — mitigated: JIT + --minify → ~25KB inline. ✓
- **FMEA-SUI-06 (actionable/alpha)** — mitigated: no buy-now/current-allocation text; "Current allocation"→"Allocation mix"; no_alpha_claim throughout. ✓

## Verification level / honesty boundary

- frontend CI tests (dashboard/interactive/smoke-port): **20 passed**; `npm run build`: ✓.
- Full `vitest run`: 68/70 reported with **1 pre-existing vitest tooling flake** (an unhandled `convert-source-map` source-map-parser error in vitest's stacktrace path — NOT a test failure; present on baseline). CI runs the 3-file subset (clean), and the committed `gate-frontend-test.txt` (70) was a clean capture; frontend count stays **70** (unchanged). Noted, not hidden.
- governance guards: **25 passed** (count/visual-evidence/payload/byte-parity sync).
- browser VRT honesty: the VRT harness renders `frontend/out/index.html` via `file://`; previously `out/` held a stale unstyled export, so the baseline (6d4e8442) was an unstyled render. This pass refreshed `out/` with the **styled inline-CSS export** and re-pinned the baseline to the real styled dashboard (af37e49c). Traceability hash refs updated in NEXT_STEPS + f-browser-pixel-baseline review/report.

## Repo-side closure vs external

- **Repo-side: complete.** Implementation + all local verification done.
- **External:** GitHub Pages auto-build on merge serves the new styled `docs/index.html`; **dataHash unchanged → committed probe stays valid, no `--live` re-probe required** (same property as a docs-only deploy). If a later change alters dashboard *data*, the full 2-phase runbook applies.

## Residual / follow-up

- Pre-existing vitest source-map flake on full-suite run (tooling, not test logic) — could be cleaned up separately; out of scope here.
- The VRT-via-file:// harness only renders styled when `out/` is the inlined export (now the case); a future hardening could make the harness deterministically rebuild `out/` first.
