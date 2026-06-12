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

Project is Backend/CLI-dominant Hybrid. Captured live (2026-06-12):

```bash
uv run pytest -q                     # 223 passed → docs/review/assets/gate-pytest.txt
uv run mypy quantlab/ scripts/run_tsmc_hedge_slice.py --ignore-missing-imports # clean 53 files → gate-mypy.txt
uv run lint-imports                  # KEPT          → gate-lint-imports.txt
(cd frontend && npm test)            # 23 passed     → gate-frontend-test.txt
(cd frontend && npm audit --omit=dev)# 0 vulns       → gate-frontend-audit.txt
```

Frontend visual evidence = a real chromium-headless screenshot
(`frontend/out/browser-visual.png`, `npm run visual:browser`, status `proven`)
plus the committed static export, the repo-baseline pixel diff
(`browser-visual-diff.json`), and the public-hosting probe
(`npm run probe:public-demo` → HTTP 200 `proven`). The review embeds the
screenshot as `live_screenshot` and discloses the remaining ops residual:
autonomous `event=schedule` dry-run proof exists as run `27392471359`, and CR-B12 proves scoped live-write mechanics. A long-running port-bound server still needs a
`local-infra-registry-governance` allocation; the headless smoke does not.

## 5. Gap analysis policy

- ✅ **Resolved** — backed by the refreshed gate evidence above or `fix:` commits.
- ⏳ **Open** — items with `Live-Demo Readiness != PASS`, `not_proven`,
  `configured_not_observed`, or `ISSUE_LOG.md` entries. Each carries
  High/Medium/Low severity and a source ref.

## 6. Output

Single self-contained `docs/review/index.html` (Hero → Value Prop → Press
Release → FAQ → Core Features → UX Flow → Gap Analysis → Roadmap → Footer), with
every feature card showing Evidence Source / Coverage Tier / Readiness State.

## 7. Regeneration checklist

1. Re-run §4 gates; refresh `docs/review/assets/`.
2. Re-copy readiness from `review.md`.
3. Rebuild `index.html`; keep gap analysis honest (no false greens).
