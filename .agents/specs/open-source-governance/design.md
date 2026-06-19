# Open Source Governance Design

## Design Summary

This lane adds repository-level protection in two layers:

1. **Repo-owned controls**: PR workflows, security scans, CODEOWNERS, PR template,
   security/contribution docs, and a tested local pre-commit hook.
2. **GitHub-hosted controls**: branch protection or rulesets for `main` and
   `dev`, requiring PRs and the repo-owned workflow checks.

The repo-owned controls are committed artifacts. GitHub branch/ruleset state is
external state and must be verified through `gh api`.

## Workflow Design

- `pr-ci.yml`
  - `governance`: existing governance/local-CI/dependency tests plus hook tests.
  - `python-core`: correctness-sensitive smoke over legacy pyramid and A0 core.
  - `architecture`: QuantLab mypy plus import-linter contracts.
  - `frontend`: Next/Vitest build path.
  - `main-promotion-source`: PRs targeting `main` must come from `dev` or
    `release/*`.
- `security-scan.yml`
  - `gitleaks`: secret scan.
  - `trivy-fs`: filesystem/dependency/IaC scan with SARIF upload.
  - `semgrep`: default SAST scan with SARIF upload.
  - `npm-audit`: frontend high/critical dependency audit.

The existing `daily-snapshot.yml` remains separate because schedule event
semantics and artifact upload transport are hosted-only evidence.

## Branch Ruleset Target

`main` and `dev` should enforce:

- pull request required before merge;
- required status checks:
  - `governance`
  - `python-core`
  - `architecture`
  - `frontend`
  - `gitleaks`
  - `trivy-fs`
  - `semgrep`
  - `npm-audit`
  - `main-promotion-source` for PRs targeting `main`
- CODEOWNERS review required;
- conversation resolution required;
- no force push;
- no branch deletion.

## Lightweight FMEA

| Risk ID | Failure Mode | Effect | Current Control | Planned Response | Task Trace |
|---|---|---|---|---|---|
| OSG-FM-001 | Branches remain unprotected | Direct push bypasses review and CI | GitHub API audit | Create/verify branch protections or rulesets | T-OSG-005 |
| OSG-FM-002 | CI exists but is not required | PR can merge with failing/absent gates | Required checks list | Bind check names into protection/ruleset | T-OSG-005 |
| OSG-FM-003 | Secret scanner false positive bypass pressure | Contributors disable hook or avoid scans | Tested allowlist patterns | Keep hook tests and CI Gitleaks | T-OSG-002/T-OSG-004 |
| OSG-FM-004 | Public demo/docs claim more than evidence | Open-source readers see false green | Existing spec review authority | PR checklist points claims back to review evidence | T-OSG-001 |
| OSG-FM-005 | Legal license chosen accidentally | Unintended reuse terms | No license file currently | Track license as owner decision, do not auto-select | T-OSG-001 |

## Boundaries

- No model, data, or dashboard behavior changes.
- No broad hosted CI substitution for local-first development workflow.
- License selection remains an owner decision.
