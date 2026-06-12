# EVIDENCE_METADATA_CONTRACT.md — Shared Evidence Field Semantics

> Canonical definitions for the evidence labels used by the generated **manual**
> (`docs/manual/`) and **executive review** (`docs/review/`). Both the
> `user-manual-skill` and `project-review-skill` reference this file as the
> single source of truth for evidence vocabulary so that captions, badges, and
> disclaimers stay consistent and artifact-honest.

## Why this exists

A screenshot, a CLI transcript, a rendered HTML payload, or an API JSON blob each
only proves **the artifact it shows**. None of them, on their own, prove that the
whole product, feature, or journey is production-ready. This contract keeps
section-level evidence from being silently promoted into a product-level
readiness claim.

The authoritative product-level readiness verdict always comes from
`.agents/specs/**/review.md` (and the registry summaries in
[`.agents/specs/SPECS.md`](../.agents/specs/SPECS.md)). Documentation generators
**consume** those verdicts; they never invent them.

## Required fields per evidence block

Every screenshot, command transcript, report artifact, or illustrative diagram in
the manual or review MUST carry at least:

| Field | Allowed values | Meaning |
|---|---|---|
| `Evidence Source` | `live_screenshot`, `live_command_output`, `report_artifact`, `fixture-backed`, `canonical_local_result_store`, `static_export`, `css_illustration`, `static_placeholder` | How the artifact was produced. |
| `Coverage Tier` | `full-integration`, `hybrid`, `mock-heavy`, `not_assessed` | Strength of *this* artifact's evidence — not the product total. |
| `Readiness State` | `PASS`, `CONDITIONAL`, `FAIL`, `not_assessed` | Copied from the owning `review.md`; never derived from task counts. |
| `Source Ref` | path | The `review.md` / `SPECS.md` / guide the readiness was copied from. |
| `Fallback Reason` | free text | Required whenever `Evidence Source` is not a live capture. |

## Evidence lane vocabulary (machine-readable maps)

When emitting a `benchmark-evidence-map.json` or similar index, use:

- `lane`: `ui` | `backend-tool-cli` | `hybrid` | `governance`
- `coverage_tier`: `full-integration` | `hybrid` | `mock-heavy` | `not_assessed`

## Claim-cap rule

- `ready`, `validated`, `full-integration`, `production-proven` wording is only
  permitted when a product-level authority (`review.md`) states it.
- `fixture-backed` / `canonical_local_result_store` / `static_export` / `css_illustration` evidence MUST be paired
  with the relevant warning code from
  [`DEMO_RISK_WARNING_TAXONOMY.md`](./DEMO_RISK_WARNING_TAXONOMY.md).

## Project-specific application (finance_algorithms)

This repository is **Backend / Tool / CLI-dominant Hybrid**:

- **Backend / CLI surface (dominant):** `quantlab` demos, `scripts/*.py`, and the
  legacy `invest_algorithms` FastAPI. Primary evidence = live command transcripts
  and report artifacts (`live_command_output`, `report_artifact`).
- **Frontend surface (secondary):** the `frontend/` Next.js showcase dashboard.
  Primary evidence = the committed static export (`static_export`) backed by a
  generated canonical local result-store payload
  (`canonical_local_result_store`), because the dashboard is still a
  deterministic local demo and its owning spec (`f-demo-hardening`) is
  `CONDITIONAL / local_demo_only`.

A missing browser screenshot for the dashboard does NOT downgrade the
backend/CLI surface, and a passing CLI transcript does NOT upgrade the
dashboard's public-hosting status.
