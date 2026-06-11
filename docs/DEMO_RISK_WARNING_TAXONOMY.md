# DEMO_RISK_WARNING_TAXONOMY.md — Shared Warning Codes

> Canonical warning codes for stakeholder-facing artifacts (`docs/manual/`,
> `docs/review/`). Referenced by `user-manual-skill` and `project-review-skill`.
> These codes make evidence limits explicit instead of hiding them behind vague
> adjectives.

| Code | When to apply | Effect on wording |
|---|---|---|
| `DEMO_NOT_ASSESSED` | The owning `review.md` has no explicit Live-Demo Readiness verdict for this surface. | Show as `not_assessed`; do not imply it works. |
| `MOCK_DOMINANT_EVIDENCE` | The artifact is driven by fixture/synthetic data rather than a live integration. | Use conservative wording (`illustrative`, `fixture-backed`). |
| `ARTIFACT_HONESTY_GAP` | An artifact could be mistaken for stronger evidence than it is (e.g. static export shown as if a live deploy). | Add a visible disclaimer banner. |
| `AUTH_FIXTURE_COUPLING` | A screen/flow depends on injected session/storageState rather than a real auth flow. | State that auth is fixture-injected. |
| `CROSS_SPEC_DEMO_DEPENDENCY` | The surface depends on another spec whose readiness is `!= PASS`. | Disclose the dependency in the gap section. |

## Project-specific mapping (finance_algorithms)

| Surface | Codes that apply | Source of truth |
|---|---|---|
| `frontend/` Next.js dashboard | `MOCK_DOMINANT_EVIDENCE` (fixture data). Browser visual now `proven` (`browser-visual.png`); residual = hash-equality diff, not pixel-tolerance CI | `.agents/specs/f-demo-hardening/review.md`, `ops-visual-drift-artifacts/review.md` |
| Public static showcase / GitHub Pages | Public-hosting probe now `proven` HTTP 200 (`public-hosting-probe.json`). `ARTIFACT_HONESTY_GAP` only on the stale `deployment-manifest.json` / export panel still reading `configured_not_observed` / `not_proven` | `.agents/specs/ops-visual-drift-artifacts/review.md`, `frontend/out/public-hosting-probe.json` |
| `daily_snapshot.py` external sources | `CROSS_SPEC_DEMO_DEPENDENCY` — Stooq opt-in/blocked, residual `ISSUE-B3-001` | `.agents/specs/ISSUE_LOG.md`, `b-data-platform/change-requests/cr-b9-stooq-opt-in.md` |
| Regime / forecast / optimizer model families | `MOCK_DOMINANT_EVIDENCE` — methodology slices, `no_alpha_claim` | `.agents/specs/d-*/review.md` |

No surface in this repo may be described as alpha-generating or
production-deployed; every model slice carries an explicit `no_alpha_claim`
boundary.
