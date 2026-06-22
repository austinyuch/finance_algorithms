# MANUAL_GENERATION_GUIDE.md — How the User Manual is Generated

> Project-specific generation note for `docs/manual/`, produced with the
> `user-manual-skill`. This is the canonical guide; the skill's mandated
> per-project file at `docs/manual/MANUAL_GENERATION_GUIDE.md` is a short pointer
> to this document. Referenced briefly from [`AGENTS.md`](../AGENTS.md).

## 1. Product surface classification

`finance_algorithms` is **Backend / Tool / CLI-dominant Hybrid**:

- **Dominant surface:** `quantlab` package + `scripts/*.py` CLI demos + the legacy
  `invest_algorithms` FastAPI. Primary evidence = **live command transcripts** and
  report artifacts. Browser screenshots are NOT the production gate here.
- **Secondary surface:** the `frontend/` Next.js showcase dashboard. Primary
  evidence = the committed **static export** (`frontend/out/`), because the
  dashboard is a generated canonical local result-store scenario and its owning
  spec is `CONDITIONAL / local_demo_only`.

## 2. Sources combined into the manual

| Source | Role |
|---|---|
| [`.agents/specs/SPECS.md`](../.agents/specs/SPECS.md) | Feature registry & dependency map |
| [`.agents/specs/NEXT_STEPS.md`](../.agents/specs/NEXT_STEPS.md) | Rolling state (backlog/gap hint only — **not** a readiness authority) |
| [`.agents/specs/ISSUE_LOG.md`](../.agents/specs/ISSUE_LOG.md) | Open improvement items (e.g. `ISSUE-B3-001`) |
| [`.agents/specs/RTM.md`](../.agents/specs/RTM.md) | Cross-spec traceability (verification context only) |
| [`.agents/specs/**/review.md`](../.agents/specs/) | **Authoritative** Live-Demo Readiness verdicts |
| [`docs/FEATURES.md`](./FEATURES.md) | Stable feature inventory |
| [`docs/EVIDENCE_METADATA_CONTRACT.md`](./EVIDENCE_METADATA_CONTRACT.md) | Evidence field semantics |
| [`docs/DEMO_RISK_WARNING_TAXONOMY.md`](./DEMO_RISK_WARNING_TAXONOMY.md) | Warning codes |

## 3. Evidence capture (Backend/CLI lane — primary)

Canonical seed/demo commands. Each writes a transcript under
`docs/manual/assets/`:

All assets are written under **`docs/manual/assets/`** (the single asset output
dir for both languages). Sample/seed data referenced by these demos:

- `data/vintage/raw/2026-06-09/`, `data/vintage/raw/2026-06-11/` — append-only PIT
  FRED + NOAA snapshots (immutable) consumed by the snapshot/vintage/real-data demos.
- `frontend/lib/showcase-payload.json` + `frontend/out/showcase.json` — the
  canonical local result-store dashboard scenario.
- `.agents/specs/real-data-oos-backtest/reports/real-data-oos-artifact.json` —
  the committed real computed OOS artifact (checksum `421c7fd2…`).

```bash
uv run python scripts/run_tsmc_hedge_slice.py     # → backend-hedge-slice-01-leaderboard.txt
uv run python scripts/run_vintage_slice.py        # → backend-vintage-slice-01-readiness.txt
uv run python scripts/daily_snapshot.py --dry-run # → backend-daily-snapshot-01-dryrun.txt
uv run python scripts/snapshot_ops_gate.py --help # → backend-ops-gate-01-help.txt

# Flow 5 — real-data OOS-net backtest (SP500 market index, exit 0 computed):
uv run python scripts/run_real_data_oos_backtest.py --out /tmp/rdo-demo.json
#   → real-data-oos-demo-01-run.txt   (trimmed transcript: computed run +
#      CR-RDO-004 oversampled_vs_native_frequency + degenerate_flat_oos fail-closed)
#   → real-data-oos-demo-02-artifact.json  (the computed artifact;
#      byte-for-byte the committed real run at
#      .agents/specs/real-data-oos-backtest/reports/real-data-oos-artifact.json)
```

Flow 6 — historical backfill & multi-cycle study (CR-B21):

```bash
uv run python scripts/backfill_history.py --since 1990-01-01   # idempotent; marks approximate
#   → backend-historical-backfill-01-demo.txt  (manifest 24/24 sources, fail=0
#      after the idempotent residual re-run + deep {^GSPC,^IXIC} 1990→2026
#      437-month computed run, 0.7007 vs 0.2264)
#   → backend-historical-backfill-02-drawdowns.txt  (regime drawdown validation:
#      dot-com −49%/−78%, GFC −57%, COVID −34%, 2022 −25% — matches the real record)
```

Flow 7 — deep-learning experiment (Epic H, real PyTorch):

```bash
uv run python scripts/run_dl_experiment.py --backend pytorch --symbols '^GSPC' '^IXIC' \
  --hidden-units 8 --lookback 6 --epochs 40 --seed 0 \
  --out out/dl-demo/exp-torch-gspc-ixic.json --viz out/dl-demo/exp-torch-gspc-ixic.svg
#   → backend-dl-experiment-01-demo.txt  (status=computed, backend=pytorch; OOS-net
#      DeepForecast +0.0919 UNDER StaticWeights baseline +0.1292 — no_alpha_claim)
```

The `pytorch` backend needs the optional torch lane installed; without it the same
call degrades to the deterministic `reference` backend (never raises). Deep history
is the CR-B21 approximate backfill (NOT true PIT; strict mode excludes it).

The backfill is `is_approximate=true` research data (NOT true PIT); **strict mode
excludes it**, only `approximate_availability=True` exposes it, `no_alpha_claim`.
Because the backfill widened the co-temporal universe, Flow 5's default run now
selects **12 co-temporal assets** (2016→2026) instead of the prior SP500-only
slice; the spec's single-index canonical artifact (`real-data-oos-artifact.json`,
checksum `421c7fd2…`) is kept as the earlier pinned record.

The real-data OOS evidence is `report_artifact` + `live_command_output`
(`no_alpha_claim`, mechanism not strategy verdict, `approximate_event_date` ≠ true
PIT). The committed `real-data-oos-demo-01-run.txt` was **live-captured on
2026-06-15** (the computed 12-asset co-temporal run plus both real fail-closed
paths). When live re-exec is unavailable, regenerate by reconstructing the
transcript from the committed real computed artifact and record a `Fallback
Reason` on the asset block.

Authoritative gates (recorded in the manual evidence panel):

```bash
uv run python scripts/capture_pytest_gate.py       # 478 passed (2026-06-18)
uv run mypy quantlab/ scripts/build_showcase_payload.py scripts/run_tsmc_hedge_slice.py scripts/run_vintage_slice.py scripts/scheduled_run_observer.py scripts/tier3_readiness_gate.py scripts/source_quorum_proof.py scripts/stooq_contract_proof.py scripts/run_real_data_oos_backtest.py --ignore-missing-imports # clean, 69 files
uv run lint-imports                                # engine/data KEPT, 88 files / 242 dependencies
(cd frontend && npm test && npm audit --omit=dev)  # 70 passed, 0 vulnerabilities
```

## 4. Evidence capture (Web UI lane — secondary)

The dashboard is captured from the **committed static export**, regenerated with:

```bash
cd frontend && npm run export:public-demo   # → frontend/out/{index.html,showcase.json,...}
```

`frontend/out/index.html` is real rendered dashboard markup driven by
`lib/showcase-payload.json`, generated by `scripts/build_showcase_payload.py`
from `LocalResultStore` / `ExperimentRegistry`. A real chromium-headless
screenshot is captured by:

```bash
cd frontend && npm run smoke              # ephemeral 127.0.0.1 start; validates / and /api/showcase (no port allocation)
cd frontend && npm run visual:browser     # → frontend/out/browser-visual.png (status proven)
npm run probe:public-demo                 # → frontend/out/public-hosting-probe.json
```

`npm run smoke` and `npm run visual:browser` are the default **no-port** evidence
path (ephemeral start, then exit) per CLAUDE.md — they need no registry
allocation. The committed dashboard screenshot in `docs/manual/assets/` is
`dashboard-browser-visual.png`; the embedded static export is
`dashboard-static-export.html`; the `/api/showcase` payload is `showcase.json`.

Public hosting is `proven` / `matched` for deployed==expected `dataHash 6c18e572…`
after the 2026-06-21 `main` deploy (live-probed 2026-06-21T04:18Z via
`scripts/refresh_public_hosting_proof.py --live`); the dashboard self-claim stays
`not_proven` by static-artifact contract — a static artifact cannot self-claim its
deployment. Freshness is deterministic
(CR-FPS-011): stale committed evidence downgrades to `configured_not_observed`
rather than crashing.

For Flow 4 the legacy FastAPI pyramid calculator can be started briefly for a
real response (root + a sample pyramid calc), then stopped:

```bash
cd invest_algorithms && uv run uvicorn api:app --host 127.0.0.1 --port 2224 &
curl -s 'http://127.0.0.1:2224/api/pyramidArithmetic?...'   # capture JSON, then stop the server
```

Any **persistent** port-bound service beyond an ephemeral smoke must go through
`local-infra-registry-governance`; if governance is unavailable, fall back to the
static export + headless screenshot and mark the section `Illustrative` with a
`Fallback Reason`.

The manual embeds `browser-visual.png` as `live_screenshot` evidence (the static
export ships semantic HTML without the app stylesheet, so the shot is
intentionally unstyled). A long-running `next start` server still requires a
registry-governed local port (`local-infra-registry-governance`); the headless
smoke and static export need none, so they are the default evidence path. The
dashboard's data remains a deterministic local scenario
(`canonical_local_result_store`, `no_alpha_claim`, `local_demo_only`), not a live
backend service; the visual diff gate is repo-baseline pixel-backed.

### Interactive research panel (Epic H slice H-3 — manual Flow 8)

The showcase dashboard carries an **Interactive Research** panel
(`frontend/components/InteractiveResearchPanel.tsx`, driven by
`frontend/lib/interactive-research.ts`) over the existing Epic H artifacts. Its
payload is the deterministic `static_replay` `interactiveResearch` block emitted by
`quantlab/showcase/scenario.py::_interactive_research_section` and committed in
`frontend/lib/showcase-payload.json` / `docs/showcase.json`. The manual's Flow 8
documents the parameter workflow, OOS-net-only model-vs-baseline leaderboard, the
`research_mode_approximate_availability` lineage warning, and the **fail-closed**
behavior. Capture/refresh evidence with:

```bash
cd frontend && npm run e2e:interactive   # real Chromium/Next.js: computed → seed change → fail_closed → VRT
```

`npm run e2e:interactive` is the H-3 evidence path: a real browser flow that
flips the panel `computed` → `fail_closed` and diffs the fail-closed screenshot
against the committed VRT baseline
`frontend/visual-baselines/interactive-research-failclosed.png` (0 mismatched
pixels). Readiness is copied from `.agents/specs/h-interactive-research-ui/review.md`
(PASSED, repo-side/local static-replay; public Pages parity deploy-gated). Boundary:
`static_replay` only — no live backend rerun, JAX/TF real training, GPU/native
models, or production Tier3; `no_alpha_claim`.

### Live rerun (Epic H slice H-4 — manual Flow 9)

The manual now also covers **H-4 live rerun** as Flow 9 (added to all four manual
files + the sidebar nav / audience quick-nav). It documents the additive
`live_compute` mode: a real Python ASGI backend
(`quantlab/showcase/rerun_service.py`) recomputes the experiment via
`run_experiment` behind a Next.js proxy route (`app/api/experiment/rerun`) with an
honest **static-replay fallback**, the 5-state `LiveRerunStatus` lifecycle, the
public PIT-provider read view, and the charter boundary (historical OOS-net
mechanism evidence only — no actionable-signal surface; `no_alpha_claim`).
Readiness and the test/mutation roster are copied from
`.agents/specs/h-live-rerun-api/review.md` (Review PASSED · deployed 2026-06-21)
and `docs/FEATURES.md` (#12) — never from raw task counts.

## 5. Runtime governance note

Any live, port-bound service (`next start`, `uvicorn`) must first obtain a
governed allocation via `local-infra-registry-governance`
(`~/.config/opencode/local-infra/registry.json`). CLI demos and the static export
require **no** port allocation and are the default evidence path.

## 6. Output contract (four-quadrant)

- `docs/manual/en/index.md` + `docs/manual/zh-tw/index.md` (plain-text reference)
- `docs/manual/en/index.html` + `docs/manual/zh-tw/index.html` (visual)
- Every evidence block shows `Evidence Source` / `Coverage Tier` / `Readiness
  State`; fallback/fixture/mock cases show the matching warning code.

## 7. Regeneration checklist

1. Refresh assets via §3–§4 commands.
2. Re-copy readiness verdicts from `review.md` (never from task counts).
3. Update the four manual files; keep EN and ZH-TW in sync.
4. Sanity-check relative asset paths resolve.
5. Visual render-validation: screenshot both HTML files headless and eyeball them —
   `/snap/bin/chromium --headless --no-sandbox --disable-gpu --window-size=1440,2400
   --screenshot="$PWD/out/docshots/manual-en.png" "file://$PWD/docs/manual/en/index.html"`
   (repeat for zh-tw). Snap chromium is confined — write the screenshot **inside the
   repo** (`out/…`), not `/tmp`. Record the result + any visual residual in the
   "Visual gap inventory" section.

### 7a. Epic H pipeline SVG + DL exploratory-analysis prose (Flow area)

The manual now carries, in the Flow 7 (deep-learning) area, a self-contained inline
**Epic H pipeline SVG** (`vintage → reference MLP │ optional lazy torch → OOS-net
report + checksum → 4-panel SVG viz → H-3 static_replay → H-4 live_compute`) plus a
short **"Epic H — exploratory analysis"** subsection: method (reference MLP + honest
backend fallback), metrics (OOS-net-only + 4-panel viz), the real multi-cycle
observation (Regime 0.669 > BuyAndHold 0.657 baseline > Forecast 0.354 > Robust
0.321), and the `no_alpha_claim` / approximate-availability / mechanism-not-verdict
boundary. The HTML files embed both the pipeline SVG and the leaderboard SVG; the MD
files carry the same prose plus the leaderboard as a small table. Sources: the SVGs
and prose are authored in
[`.agents/specs/docs-enrichment-h-eda/design.md`](../.agents/specs/docs-enrichment-h-eda/design.md)
and [`.agents/specs/docs-enrichment-h-eda/code/svg-snippets.html`](../.agents/specs/docs-enrichment-h-eda/code/svg-snippets.html);
the leaderboard numbers are hard-coded from the committed report JSON
`.agents/specs/real-data-oos-backtest/reports/multi-cycle-family-oos-artifact.json`
(single source of truth — never recompute them in the docs). All diagrams are inline
SVG only (no CDN, no external `<script src>` / `<img>`), and every DL slice repeats
the `no_alpha_claim` charter boundary.

## 8. Deploy-coupling & count-refresh policy (read before bumping numbers)

The committed manual HTML/MD are a **deploy-coupled snapshot**: their gate counts
(pytest full-suite, Python mutation, frontend), the `docs/showcase.json` payload, its
`dataHash`, and the public-hosting proof move **together**, and only at an actual GitHub
Pages deploy. Do **not** bump them as a standalone "make the published number current" edit:

- Regenerating `docs/showcase.json` changes `dataHash = sha256(JSON.stringify(dashboard))`
  (the evidence list is hashed), which flips `docs/deployment-manifest.json` /
  `docs/public-hosting-probe.json` to `configured_not_observed` / `mismatched` until `main`
  redeploys and a live re-probe (`scripts/refresh_public_hosting_proof.py --live`) observes
  the new hash — an intrinsically **async, post-deploy** step.
- A standalone count bump also rewrites the same number across EN+ZH × md+html plus the
  guides, and the repo's Copilot PR reviewer (`required_conversation_resolution` on `main`)
  re-reviews each push — empirically **non-converging** (the 2026-06-20 count-payload
  attempt, PR #131, was abandoned for exactly this; see `.agents/specs/NEXT_STEPS.md`).

**Authority for current numbers:** the governance SoT — `quantlab/TESTS.md`
(`Python full suite **N passed**`, `Python mutation spot checks: N/N`),
`.agents/specs/{SPECS,RTM,NEXT_STEPS}.md`, and `docs/FEATURES.md`. The manual HTML reflects
the **last-deployed** snapshot; a documented delta (e.g. governance mutation count ahead of
the deployed-snapshot payload) is expected, non-breaking, and reconciled at the next deploy
— never by a standalone doc edit. Honest interim hosting state — while a regenerated payload
is committed but not yet redeployed — is `configured_not_observed`; never hand-write `proven`
(copy it from the live-probe JSON `docs/public-hosting-probe.json`).
