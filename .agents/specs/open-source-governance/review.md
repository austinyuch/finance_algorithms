# Open Source Governance Review

Status: Implemented for branch/CI protection; license decision pending

## Evidence

- Repo public state: `gh api repos/austinyuch/finance_algorithms` reported
  `"private": false`, default branch `main`, and no detected license.
- Pre-existing GitHub protection state before this lane:
  - `main`: branch protection API returned `Branch not protected (HTTP 404)`.
  - `dev`: branch protection API returned `Branch not protected (HTTP 404)`.
  - Repository rulesets API returned `[]`.
- Repo-side controls added:
  - `.github/workflows/pr-ci.yml`
  - `.github/workflows/security-scan.yml`
  - `.github/CODEOWNERS`
  - `.github/PULL_REQUEST_TEMPLATE/pull_request_template.md`
  - `SECURITY.md`
  - `CONTRIBUTING.md`
  - `scripts/git-hooks/pre-commit`
  - `scripts/install-git-hooks.sh`
  - `scripts/tests/test_pre_commit_hook.sh`
- Focused local verification:
  - `bash scripts/tests/test_pre_commit_hook.sh` -> `pass=11 fail=0`.
  - `git diff --check` -> passed.
  - `uv run pytest -q tests/test_local_ci_matrix.py tests/test_dependency_security.py` -> `3 passed`.
  - `uv run mypy quantlab/ --ignore-missing-imports` -> clean over 62 source files.
  - `uv run lint-imports` -> 2 contracts kept, 0 broken.
  - Python YAML parse of `.github/workflows/*.yml` -> all three workflow files parsed.
  - `actionlint` was not installed locally, so deep GitHub Actions lint was not run.
- Hosted branch protection verified after setup:
  - `main`: strict status checks required for `governance`, `python-core`,
    `architecture`, `frontend`, `main-promotion-source`, `gitleaks`,
    `trivy-fs`, `semgrep`, and `npm-audit`; code-owner review required;
    stale reviews dismissed; 1 approval required; admin enforcement enabled;
    conversation resolution required; force-push and deletion disabled.
  - `dev`: strict status checks required for `governance`, `python-core`,
    `architecture`, `frontend`, `gitleaks`, `trivy-fs`, `semgrep`, and
    `npm-audit`; code-owner review required; stale reviews dismissed; 1
    approval required; admin enforcement enabled; conversation resolution
    required; force-push and deletion disabled.
  - Repository rulesets remain `[]`; protection is implemented through branch
    protection rather than rulesets.

## Current Verdict

Protected PR workflow is now configured for `main` and `dev`.

Remaining open-source readiness gap:

1. The repository owner must choose and commit a license before advertising
   reusable open-source terms.
