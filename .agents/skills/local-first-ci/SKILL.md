---
name: local-first-ci
description: Use this skill when a task mentions CI, GitHub Actions, workflow cost, expensive hosted runs, pre-merge gates, smoke tests, mutation tests, subagents, "run what CI would run", "do not use Actions", "Actions are expensive", "盡可能在local", "CI流程都subagent完成", "原本常態要給CI跑得測試and CI流程都subagent完成", or asks to keep normal CI tests/workflows local because hosted Actions are costly. It converts the ordinary CI queue into local/subagent gate bundles first and reserves GitHub Actions for hosted-only semantics.
---

# Local-First CI

GitHub Actions minutes are cost-sensitive. When this skill is active, treat the normal CI loop as local/subagent-owned work first, not as a hosted discovery queue.

The goal is to produce the same pass/fail decision CI would normally produce before any push, PR, or hosted confirmation. Slow local runtime is not a hosted-only reason.

If the user says GitHub workflows or Actions are expensive, interpret that as a request to take over the ordinary CI queue locally: complete every repo-runnable test, coverage, PBT, mutation, smoke, build, visual, audit, type/import, dependency, and generated-evidence gate with local commands, subagents, or isolated local shells before considering hosted confirmation.

## Operating Model

1. Read repo guidance and workflow definitions before deciding what CI would run.
2. Map each ordinary CI step to a repo-local command, package script, static check, or generated-artifact check.
3. Split independent read-only gates across subagents or parallel local shells when practical.
4. Serialize mutation, generated-artifact, and other file-mutating gates so they do not race readers.
5. Fix or record local failures before spending hosted workflow minutes.
6. Leave only genuinely GitHub-hosted proof in the hosted-only ledger.
7. Do not classify a repo-runnable gate as hosted-only because it is slow, flaky, or historically lived in a workflow file.

## Local/Subagent By Default

Default these CI surfaces to local/subagent execution whenever the repo exposes commands for them:

- Unit, integration, property-based, chaos, coverage, and regression tests.
- Type checks, import architecture checks, formatting, dependency checks, and `git diff --check`.
- Mutation tests and mutation spot checks.
- Frontend unit tests, build/export, smoke, visual, audit, and frontend mutation gates.
- Generated docs, payloads, probe artifacts, spec registries, and governance freshness checks.
- Workflow contract checks that can be proven by reading YAML and running the same local scripts.

Do not push just to let Actions find ordinary failures that local commands can find.

## Hosted-Only Ledger

Use GitHub Actions only for proof that depends on GitHub-hosted state:

- Event payload semantics.
- Repository secrets, permissions, OIDC, protected environments, or deployment approvals.
- Artifact upload/download behavior.
- Scheduled triggers.
- GitHub Pages deployment state.
- Remote production identity or external service binding that cannot be reproduced locally.

Before a hosted run, record the smallest remaining hosted check, why local proof is insufficient, and the local gates already completed.

## Subagent Dispatch Contract

When assigning CI-equivalent work to subagents, give each one a bounded gate bundle and require this return shape:

- Scope: the CI job or workflow step being replaced locally.
- Command: exact command and working directory.
- Isolation: read-only, generated-artifact, mutation/file-mutating, or hosted-only.
- Evidence: exit status and the concise output line that matters.
- Changed files: any files created or modified.
- Remainder: hosted-only proof still required, if any.

The main agent remains responsible for changed-file scoping, conflict avoidance, evidence reconciliation, governance updates, and the final hosted-only decision.

## Finance Algorithms Default Matrix

For this repo, start from these local equivalents:

- Python correctness: `uv run pytest -q`, plus targeted coverage/PBT/chaos slices for correctness-sensitive changes.
- Static architecture: `uv run mypy quantlab/ --ignore-missing-imports`, `uv run lint-imports`, and `git diff --check`.
- Mutation: targeted `uv run python scripts/run_mutation_spot_checks.py --only ...`, then full mutation when readiness evidence depends on the full ledger.
- Frontend: from `frontend/`, `npm test -- --run`, build/export, smoke, visual, audit, and frontend mutation when dashboard or public demo surfaces are touched.
- Evidence/governance: regenerate payloads/docs/probe artifacts/spec registries, then run governance guard tests.
- Workflow contract: inspect `.github/workflows/` and run the local scripts invoked by the workflow; classify only GitHub-specific semantics as hosted-only.

For this repository, mutation gates and generated evidence gates can edit files. Do not run them in parallel with tests or builds that read those files.

## Handoff Shape

When the user is trying to avoid Actions spend, summarize the local CI replacement matrix before push/PR:

- `local/subagent`: ordinary gate completed locally, with command and evidence.
- `serialized`: mutation or generated-artifact gate completed without racing readers.
- `hosted-only`: smallest remaining GitHub-hosted proof and why local evidence cannot cover it.

Keep claims conservative: local proof is repo-side evidence, not GitHub Actions proof, Pages proof, scheduler proof, or production proof.
