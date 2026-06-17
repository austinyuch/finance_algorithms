# Agent Guide

This file is the operating guide for coding agents working in this repository.

## First Reads

Start with these files before making non-trivial changes:

1. `.agents/specs/SPECS.md`
2. `.agents/specs/NEXT_STEPS.md`
3. The relevant spec folder under `.agents/specs/`
4. `quantlab/CORRECTNESS_CHECKLIST.md` for backtest correctness constraints
5. `quantlab/TESTS.md` for the test registry

## Project Shape

- `invest_algorithms/` is the legacy FastAPI pyramid calculator. Preserve existing behavior unless a task explicitly targets it.
- `quantlab/` is the newer research platform built through SDD specs.
- `.agents/specs/` is the source of truth for requirements, designs, reviews, and task history.
- `data/vintage/raw/` is append-only point-in-time data. Do not overwrite existing daily snapshots.

## Development Commands

Use `uv`:

```bash
uv sync
uv run pytest -q
uv run mypy quantlab/ --ignore-missing-imports
uv run lint-imports
```

Useful demo commands:

```bash
uv run python scripts/run_tsmc_hedge_slice.py
uv run python scripts/run_vintage_slice.py
uv run python scripts/daily_snapshot.py --dry-run
```

To run the legacy API:

```bash
cd invest_algorithms
uv run uvicorn api:app --host 127.0.0.1 --port 2224
```

## Generated Documentation

Stakeholder-facing docs live under `docs/` and are regenerated from the specs
plus refreshed gate evidence. Keep readiness claims copied from
`.agents/specs/**/review.md` (never derived from task counts):

- **User manual** — `docs/manual/{en,zh-tw}/index.{md,html}`. Regeneration steps:
  [`docs/MANUAL_GENERATION_GUIDE.md`](docs/MANUAL_GENERATION_GUIDE.md). The
  bilingual manual is regenerated per that guide with real CLI/API evidence and
  briefly-started services (CLI demos, `frontend` smoke + headless screenshot,
  and a transient legacy `uvicorn` curl), and reconciled against the spec
  governance set (`.agents/specs/{NEXT_STEPS,SPECS,ISSUE_LOG,RTM}.md` +
  [`docs/FEATURES.md`](docs/FEATURES.md)).
- **Executive review** — `docs/review/index.html`. Regeneration steps:
  [`docs/REVIEW_GENERATION_GUIDE.md`](docs/REVIEW_GENERATION_GUIDE.md). Regenerated
  per that guide with real gate/CLI evidence and started services, a Gap Analysis
  that separates resolved-since-last-check from still-open (no false greens, claim
  cap from `review.md`), and an audit row recorded in
  [`.agents/specs/ISSUE_LOG.md`](.agents/specs/ISSUE_LOG.md).
- **Shared contracts** — [`docs/FEATURES.md`](docs/FEATURES.md),
  [`docs/EVIDENCE_METADATA_CONTRACT.md`](docs/EVIDENCE_METADATA_CONTRACT.md),
  [`docs/DEMO_RISK_WARNING_TAXONOMY.md`](docs/DEMO_RISK_WARNING_TAXONOMY.md).
- **Traceability bridge** — [`.agents/specs/RTM.md`](.agents/specs/RTM.md)
  (verification context only, not a readiness authority).

Live, port-bound services for evidence capture must go through
`local-infra-registry-governance`; CLI demos and the committed static export
need no port allocation and are the default evidence path.

## Architecture Rules

- `quantlab.engine` and `quantlab.data` must not import `torch`, `tensorflow`, `jax`, or `flax`.
- Keep ML framework code behind strategy adapters or environment-specific modules.
- Epic H (deep-learning research lab) keeps frameworks behind `quantlab/models/dl/backends.py` (`FrameworkAdapterRegistry`): torch/jax/tf are resolved lazily and degrade honestly to the framework-free `reference` backend when absent. A second import-linter contract forbids `engine`/`data` from importing the DL backend boundary. `quantlab/models/dl_forecaster.py` (reference MLP), `quantlab/research/model_performance_report.py` + `model_report_viz.py` (stats/viz), and `scripts/run_dl_experiment.py` (parameterized experiment CLI → `ExperimentRegistry` lineage) are all `no_alpha_claim`. Epic H slice **H-2** (`h-deep-learning-real-training`) adds a real PyTorch training path in `quantlab/models/dl/torch_trainer.py` (lazy `import torch`, float64, seed-init parity with the reference within `1e-3`), reached only via the `NumpyMLPForecaster` backend dispatch when `backend="pytorch"` resolves; it runs in an **optional default-skipped torch lane** (`tests/quantlab/test_h2_torch_training.py`, `pytest.importorskip("torch")`) and degrades honestly to `reference` when torch is absent. Torch stays out of the default lock; the canonical no-skip pytest count is captured in a torch-enabled venv.
- Keep `quantlab/contracts/interfaces.py` structurally aligned with `.agents/specs/a0-backtest-foundation/contract/interfaces.py`.
- For schema changes, update the spec contract first, regenerate generated models if needed, and run tests plus mypy.
- Backtest results should report out-of-sample net metrics when used for leaderboard comparisons.
- PIT access must respect `available_date <= asof`; avoid any shortcut that can introduce lookahead.
- Preserve survivorship handling through listings data.
- Cost, tax, slippage, FX, and walk-forward behavior are correctness-sensitive. Add or update tests when touching them.

## Data Rules

- Vintage snapshots are immutable. If a daily file exists, skip it instead of overwriting it.
- `available_date` represents when the project captured or could have known a value.
- If historical data is reconstructed without a true vintage source, mark it approximate and keep strict/lenient behavior explicit. The CR-B21 deep historical backfill (`scripts/backfill_history.py` → `data/vintage/raw/backfill-1990-01-01/`, 1990+) is exactly this case: every record is `is_approximate=true` + `backfill=true`, **strict PIT mode excludes it**, and only `approximate_availability=True` (research mode) exposes it under `no_alpha_claim`.
- Snapshot fetching should degrade per source: one failed external source should not corrupt other captures (the CR-B21 backfill follows the same per-source degradation + idempotent-skip contract).

## Testing Expectations

- For documentation-only edits, no full test run is required.
- For code touching `quantlab/engine`, `quantlab/data`, contracts, costs, metrics, or portfolio logic, run `uv run pytest -q`.
- For typed QuantLab changes, run `uv run mypy quantlab/ --ignore-missing-imports`.
- For imports involving `quantlab.engine` or `quantlab.data`, run `uv run lint-imports`.
- For legacy `invest_algorithms/` changes, run `uv run pytest -q tests/test_algo_pyramid.py` at minimum.

## Local-First CI Policy

Hosted GitHub Actions are cost-sensitive. Use `.agents/skills/local-first-ci/`
when a task mentions CI, workflow cost, pre-merge gates, smoke tests, mutation
tests, or "run what CI would run". Run the matching local gates first and do not
trigger or rerun GitHub Actions unless the user explicitly asks or the proof
genuinely depends on GitHub-hosted state. Use local subagents or parallel local
shells for independent CI-equivalent gates when that can reduce hosted workflow
usage without weakening evidence. Treat routine CI as local subagent gate
bundles first: Python, static typing/import architecture, mutation, frontend,
smoke, visual, audit, and evidence-regeneration checks should complete locally
before hosted CI is used for confirmation. Normal tests and workflow steps that
would usually be queued in CI should be treated as local completion work first.
When this repo has an equivalent command, split the gate into subagent-owned
bundles when possible. Treat "CI would catch this" as a
local/subagent responsibility first; use hosted Actions only for confirmation or
claims that require GitHub-hosted event semantics, secrets, permissions,
artifact transport, scheduled triggers, or Pages deployment state. Do not leave
unit/integration, line coverage, PBT, mutation, smoke, build, visual, audit,
type/import, or generated-evidence sync gates for hosted CI when the repo has a
local command that can prove them. Before a push intended to trigger Actions,
complete the local/subagent matrix or record the exact hosted-only gap; do not
use GitHub Actions as the routine queue for CI-equivalent work that local
subagents can finish.

Commit, push, and PR-prep requests inherit this policy unless the user
explicitly asks to skip local gates. Split independent CI-equivalent bundles
across local subagents when available, but keep file-mutating gates such as
mutation tests isolated and reconcile all evidence in the main agent before
claiming readiness. Subagent-owned gates should return the command, exit status,
key evidence, and any hosted-only gap; treat that as the local CI decision path,
not just a preflight before spending GitHub Actions minutes. Use the handoff
fields from `.agents/skills/local-first-ci/`: Scope, Command, Isolation,
Evidence, Remainder, changed files if any, and a fail-closed stop rule for the
first unexplained failure.

Completion means producing the same local pass/fail decision the hosted CI step
would have produced, not merely a preflight before Actions.
If workflow or Actions cost is the concern, maximize local/subagent completion
of the normal CI test and workflow matrix. Slow local execution is not by itself
a hosted-only gap.

When reducing Actions cost, treat the normal CI flow as a local/subagent
takeover target: inspect the workflow or documented gate, map ordinary test,
coverage, mutation, smoke, build, visual, audit, type/import, dependency, and
generated-evidence steps to repo-local commands, and finish those locally before
hosted confirmation. Only GitHub event semantics, secrets/permissions, artifact
transport, scheduled triggers, Pages deployment state, protected environments,
and remote production identity should remain hosted-only.
If the user explicitly says GitHub workflows or Actions are expensive, complete
the ordinary CI test and workflow matrix through local commands, subagents, or
isolated local shells as far as practical. Do not leave a repo-runnable CI step
for Actions merely because it is slow or normally belongs to the hosted
workflow.
Prompts such as "盡可能在local", "CI流程都subagent完成", or "gh workflow and
actions很貴" mean the normal CI queue should be taken over locally first:
inspect workflow YAML, translate ordinary steps to local commands, split
independent gates across local subagents or shells, serialize file-mutating
mutation/generated-artifact gates, and keep only GitHub-hosted semantics in the
hosted-only ledger.

For push/PR readiness, build a local CI replacement matrix from the touched
files and finish it before using hosted Actions for confirmation. The matrix
should cover any repo-available unit, integration, line coverage, PBT, mutation,
smoke, build, visual, audit, type/import, dependency, and generated-evidence
checks. If a remaining gate is truly hosted-only, record the expected workflow,
why local/subagent evidence is insufficient, the smallest hosted run needed,
and the local evidence already completed.

## Style Notes

- Prefer small, spec-aligned changes over broad refactors.
- Use existing local patterns before adding abstractions.
- Keep public behavior stable unless the relevant spec or user request calls for a change.
- Do not remove user-created files or untracked files unless explicitly asked.
- Keep docs and comments concise, but record decisions in the spec artifacts when they affect future work.
