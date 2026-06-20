# REVIEW_GENERATION_GUIDE.md — How the Executive Review is Generated

> Project-specific generation note for `docs/review/`, produced with the
> `project-review-skill`. Canonical guide; the skill's suggested
> `docs/PROJECT_REVIEW_GUIDE.md` is a short pointer to this file. Referenced
> briefly from [`AGENTS.md`](../AGENTS.md).

## 1. Purpose & audience

`docs/review/index.html` is a single-page executive product introduction:
value proposition (internal + external), an Amazon-style backwards PR/FAQ, UX
flow, core-feature cards, and a gap analysis. The audience is a reviewer or
stakeholder, **not** an engineer mid-task.

## 2. Readiness authority (non-negotiable)

- Feature readiness badges are **copied** from `.agents/specs/**/review.md` and
  the registry summary in [`SPECS.md`](../.agents/specs/SPECS.md).
- `NEXT_STEPS.md` and `RTM.md` may only supply backlog/gap hints and
  traceability context — never a readiness verdict.
- Mock/fixture/illustrative evidence is capped with the codes in
  [`DEMO_RISK_WARNING_TAXONOMY.md`](./DEMO_RISK_WARNING_TAXONOMY.md); field
  semantics follow [`EVIDENCE_METADATA_CONTRACT.md`](./EVIDENCE_METADATA_CONTRACT.md).

## 3. Sources combined

`README.md`, `AGENTS.md`, `docs/FEATURES.md`, `.agents/specs/{SPECS,NEXT_STEPS,
ISSUE_LOG,RTM}.md`, every `.agents/specs/**/review.md`, and `git log`.

## 4. Evidence capture & services started

Project is Backend/CLI-dominant Hybrid. Captured/refreshed live (2026-06-15,
post-CR-B21):

```bash
uv run python scripts/capture_pytest_gate.py  # 486 passed → docs/review/assets/gate-pytest.txt
uv run python scripts/run_mutation_spot_checks.py --report-json docs/review/assets/gate-python-mutation.json  # 118/118 killed
uv run mypy quantlab/ scripts/build_showcase_payload.py scripts/run_tsmc_hedge_slice.py scripts/run_vintage_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py scripts/source_quorum_proof.py scripts/stooq_contract_proof.py scripts/run_real_data_oos_backtest.py --ignore-missing-imports # clean 69 files → gate-mypy.txt
uv run lint-imports                  # KEPT, 88 files / 242 deps → gate-lint-imports.txt
(cd frontend && npm test)            # 52 passed     → gate-frontend-test.txt
(cd frontend && npm audit --omit=dev)# 0 vulns       → gate-frontend-audit.txt
```

Frontend visual evidence = a real chromium-headless screenshot
(`frontend/out/browser-visual.png`, `npm run visual:browser`, status `proven`)
plus the committed static export, the repo-baseline pixel diff
(`browser-visual-diff.json`), and the public-hosting probe
(`npm run probe:public-demo` → HTTP 200 plus deployed manifest contract metadata;
exit 0 only when deployed `dataHash` parity is proven, exit 2 while branch-local
Pages parity is pending). The review embeds the
screenshot as `live_screenshot` and discloses the remaining ops residual:
autonomous `event=schedule` dry-run proof exists as run `27392471359`, and CR-B12 proves scoped live-write mechanics. A long-running port-bound server still needs a
`local-infra-registry-governance` allocation; the headless smoke does not.

The latest resolved-since-last-check gap is **CR-B21** (deep 1990+ historical
backfill): the Gap Analysis surfaces it as resolved — `is_approximate=true`
research vintage, strict-excluded, a multi-cycle backtest (deep `{^GSPC,^IXIC}`
1990→2026) and regime-drawdown validation (dot-com/GFC/COVID/2022 matching the
real record), under `no_alpha_claim`. The CR-B21 dashboard refresh moved the
deployed-and-re-proven `dataHash` to `0f170441…` (`status=proven`,
`2026-06-15T07:07Z`).

## 5. Gap analysis policy

- ✅ **Resolved** — backed by the refreshed gate evidence above or `fix:` commits.
- ⏳ **Open** — items with `Live-Demo Readiness != PASS`, `not_proven`,
  `configured_not_observed`, or `ISSUE_LOG.md` entries. Each carries
  High/Medium/Low severity and a source ref.

## 6. Output

Single self-contained `docs/review/index.html` (Hero → Value Prop → Press
Release → FAQ → Core Features → UX Flow → Gap Analysis → Roadmap → Footer), with
every feature card showing Evidence Source / Coverage Tier / Readiness State.

**Bilingual (en + zh-tw), switched in-page.** Unlike the manual (separate
`{en,zh-tw}/index.html` files), the review is **one** file with an in-HTML
language toggle:

- Every translatable text unit is duplicated as adjacent siblings tagged
  `class="en"` / `class="zh"` (use `<span>` for inline, block tags for blocks).
  Keep code identifiers, paths, badges, and the UX-flow SVG labels in English.
- A small CSS rule hides the inactive language: `.zh{display:none}` and
  `html.lang-zh .en{display:none}` / `html.lang-zh .zh{display:revert}`. **English
  is the no-JS default** so the page still renders offline/without scripts.
- A fixed `EN / 中文` toggle flips `document.documentElement.classList` (a tiny
  inline script — no external/CDN dependency; keep the page self-contained).
- Translate zh-tw in the same register as the manual's `zh-tw/index.html`; keep
  all readiness/claim-cap wording faithful in both languages (no divergent claims).

## 7. Regeneration checklist

1. Re-run §4 gates; refresh `docs/review/assets/`.
2. Re-copy readiness from `review.md`.
3. Rebuild `index.html`; keep gap analysis honest (no false greens). Split the
   Gap Analysis into *resolved since last check* vs *still open*; when public
   hosting has been re-proven for the current `dataHash`, record it as resolved
   (live probe `status=proven`) while keeping the dashboard self-claim
   `not_proven` by static-artifact contract.
4. Record an audit row in `.agents/specs/ISSUE_LOG.md` (e.g. `DOC-RECON-<date>`)
   noting the evidence snapshot and that no new unowned items surfaced.
5. Visual render-validation: screenshot the built page headless and eyeball it —
   `/snap/bin/chromium --headless --no-sandbox --disable-gpu --window-size=1440,2400
   --screenshot="$PWD/out/docshots/review.png" "file://$PWD/docs/review/index.html"`.
   Note: snap chromium is confined — write the screenshot **inside the repo**
   (`out/…`), not `/tmp`. Verify cards/captions/badges and CSS. The UX-flow diagram
   is a self-contained inline SVG (no Mermaid CDN / client-side JS), so it renders
   in the static screenshot too; keep its accessible text-equivalent caption.

## Epic H deep-learning demo section

`docs/review/index.html` carries a dedicated **🤖 Deep-Learning Demo (Epic H)**
section showcasing the real-PyTorch training slice (H-2). Its evidence is the
canonical experiment artifact `out/dl-demo/exp-torch-gspc-ixic.json`
(`status=computed`, `backend=pytorch`, OOS-net DeepForecast under the
StaticWeights baseline — `no_alpha_claim`) plus the self-contained performance
report SVG copied to `docs/review/assets/dl-experiment-torch.svg`. Regenerate via
`scripts/run_dl_experiment.py --backend pytorch` (needs the optional torch lane).
Honesty cap: deep history is the CR-B21 approximate backfill (NOT true PIT);
public hosting stays `configured_not_observed` until Pages serves the new
`dataHash` after a `main` deploy.

### Epic H slice H-3 — interactive research UI

The review also carries an **Interactive research UI (H-3)** core-feature card and a
matching *resolved-since-last-check* gap entry. Readiness is copied from
`.agents/specs/h-interactive-research-ui/review.md` (**PASSED**, repo-side/local
static-replay; public Pages parity deploy-gated). Evidence is the committed
`interactiveResearch` `static_replay` block (emitted by
`quantlab/showcase/scenario.py`, surfaced via
`frontend/components/InteractiveResearchPanel.tsx`) plus the real-Chromium
`npm run e2e:interactive` fail-closed VRT (`computed` → seed change →
`fail_closed`, 0-pixel diff against
`frontend/visual-baselines/interactive-research-failclosed.png`) and the H-3
frontend mutations (`frontend-h3-interactive-claim-boundary`,
`frontend-h3-approximate-warning-gate`,
`frontend-h3-e2e-failclosed-status-gate`). Honesty cap: `static_replay` over
existing H artifacts only — OOS-net-only ranking with a visible baseline,
`no_alpha_claim`, no live backend rerun, JAX/TF real training, GPU/native models,
or production Tier3; public hosting stays `configured_not_observed` for expected
`dataHash c33da57d…` until Pages serves the refreshed artifact.
