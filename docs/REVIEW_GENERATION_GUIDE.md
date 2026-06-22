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
uv run python scripts/capture_pytest_gate.py  # 478 passed → docs/review/assets/gate-pytest.txt
uv run python scripts/run_mutation_spot_checks.py --report-json docs/review/assets/gate-python-mutation.json  # 123/123 killed
uv run mypy quantlab/ scripts/build_showcase_payload.py scripts/run_tsmc_hedge_slice.py scripts/run_vintage_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py scripts/source_quorum_proof.py scripts/stooq_contract_proof.py scripts/run_real_data_oos_backtest.py --ignore-missing-imports # clean 69 files → gate-mypy.txt
uv run lint-imports                  # KEPT, 88 files / 242 deps → gate-lint-imports.txt
(cd frontend && npm test)            # 70 passed     → gate-frontend-test.txt
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
public hosting is `proven` / `matched` for deployed==expected `dataHash 6c18e572…`
after the 2026-06-21 `main` deploy (live-probed 2026-06-21T04:18Z via
`scripts/refresh_public_hosting_proof.py --live`); the dashboard self-claim stays
`not_proven` by static-artifact contract.

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
or production Tier3; public hosting is `proven` / `matched` for deployed==expected
`dataHash 6c18e572…` after the 2026-06-21 `main` deploy (live-probed 2026-06-21T04:18Z
via `scripts/refresh_public_hosting_proof.py --live`); the dashboard self-claim stays
`not_proven` by static-artifact contract.

### Epic H slice H-4 — live backend rerun API

The review now also carries a **Live backend rerun API (H-4)** core-feature card,
placed right after the H-3 card. Readiness and the test/mutation roster are copied
from `.agents/specs/h-live-rerun-api/review.md` (**PASSED** · deployed 2026-06-21)
and `docs/FEATURES.md` (#12) — never from raw task counts. The card describes the
additive `live_compute` mode: a real Python ASGI backend
(`quantlab/showcase/rerun_service.py`) recomputes the experiment via
`run_experiment` behind a Next.js proxy route (`app/api/experiment/rerun`) with an
honest static-replay fallback, the 5-state `LiveRerunStatus` lifecycle, the public
PIT-provider read view, and the charter guard (no actionable-signal surface —
historical OOS-net mechanism evidence only; `no_alpha_claim`). Evidence is
`test_h4_provider_view` / `test_h4_live_rerun` / real-backend uvicorn smoke
(FMEA-H4-01) + the frontend live-rerun tests + mutation
`h4-rerun-validation-fail-closed-gate`. The H-3 card's boundary list no longer says
"no live backend rerun" (it shipped as H-4).

### Capability map + DL exploratory-analysis card

The review now also carries a self-contained inline **capability / data-flow map**
SVG (A0 → … → Epic H, `no_alpha_claim`) inside the Value-Proposition overview, and a
dedicated **"Epic H — deep-learning exploratory analysis"** section: the multi-cycle
OOS-net leaderboard SVG (Regime 0.669 > BuyAndHold 0.657 baseline > Forecast 0.354 >
Robust 0.321) with EDA prose covering method (reference MLP + honest backend
fallback), metrics (OOS-net-only + 4-panel viz), the real multi-cycle observation,
and the `no_alpha_claim` / approximate-availability / mechanism-not-verdict boundary,
followed by a **"Future work / Roadmap"** sub-block (JAX/TF backends, GPU/native
models, production Tier3 with external proof, Lane 2 actionable signal **charter-gated
/ deferred**, strict-PIT verdict-grade comparison). Sources: the SVGs and prose are
authored in
[`.agents/specs/docs-enrichment-h-eda/design.md`](../.agents/specs/docs-enrichment-h-eda/design.md)
(Future-Work Roadmap table) and
[`.agents/specs/docs-enrichment-h-eda/code/svg-snippets.html`](../.agents/specs/docs-enrichment-h-eda/code/svg-snippets.html);
the leaderboard numbers are hard-coded from the committed report JSON
`.agents/specs/real-data-oos-backtest/reports/multi-cycle-family-oos-artifact.json`
(single source of truth — never recompute them in the docs). All diagrams are inline
SVG only (no CDN, no external `<script src>` / `<img>`), bilingual via the existing
`.en` / `.zh` spans, and every DL slice repeats the `no_alpha_claim` charter boundary.

## Deploy-coupling & count-refresh policy (read before bumping numbers)

`docs/review/index.html` is a **deploy-coupled snapshot**: its gate counts (pytest
full-suite, Python mutation, frontend), the `docs/showcase.json` payload it summarizes, the
`dataHash`, and the public-hosting proof move **together**, and only at an actual GitHub
Pages deploy. Do **not** bump them as a standalone "make the published number current" edit:

- Regenerating `docs/showcase.json` changes `dataHash = sha256(JSON.stringify(dashboard))`,
  flipping `docs/deployment-manifest.json` / `docs/public-hosting-probe.json` to
  `configured_not_observed` / `mismatched` until `main` redeploys and a live re-probe
  (`scripts/refresh_public_hosting_proof.py --live`) observes the new hash — an
  intrinsically **async, post-deploy** step.
- A standalone count bump rewrites the same number across the bilingual review/manual docs +
  guides, and the repo's Copilot PR reviewer (`required_conversation_resolution` on `main`)
  re-reviews each push — empirically **non-converging** (the 2026-06-20 count-payload
  attempt, PR #131, was abandoned for exactly this; see `.agents/specs/NEXT_STEPS.md`).

**Authority for current numbers:** the governance SoT — `quantlab/TESTS.md`,
`.agents/specs/{SPECS,RTM,NEXT_STEPS}.md`, and `docs/FEATURES.md`. The review HTML reflects
the **last-deployed** snapshot; a documented delta (e.g. governance mutation count ahead of
the deployed-snapshot payload) is expected, non-breaking, and reconciled at the next deploy.
Honest interim hosting state — while a regenerated payload is committed but not yet
redeployed — is `configured_not_observed`; never hand-write `proven` (copy it from the
live-probe JSON `docs/public-hosting-probe.json`). The
`review.md` per-spec verdict remains the readiness authority — copy verdicts from it, never
derive readiness from gate counts.
