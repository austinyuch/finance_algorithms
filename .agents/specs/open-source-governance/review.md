# Open Source Governance Review

Status: Implemented for branch/CI protection and open-source licensing

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
- License controls added:
  - `LICENSE`: Apache License 2.0 for software source code.
  - `LICENSE-DOCS.md`: CC BY 4.0 for original project documentation and
    portfolio materials.
  - `NOTICE`: excludes third-party dependencies, market data, reconstructed
    historical data, PIT snapshots, trademarks, external media, and private
    credentials unless a file explicitly says otherwise.
  - `README.md` and `CONTRIBUTING.md` summarize the split license model.
- Focused local verification:
  - `bash scripts/tests/test_pre_commit_hook.sh` -> `pass=11 fail=0`.
  - `git diff --check` -> passed.
  - `uv run pytest -q tests/test_local_ci_matrix.py tests/test_dependency_security.py` -> `3 passed`.
  - `uv run mypy quantlab/ --ignore-missing-imports` -> clean over 62 source files.
  - `uv run lint-imports` -> 2 contracts kept, 0 broken.
  - Python YAML parse of `.github/workflows/*.yml` -> all three workflow files parsed.
  - `actionlint` was not installed locally, so deep GitHub Actions lint was not run.
- License closeout verification:
  - `git diff --check` -> passed.
  - `uv run pytest -q tests/quantlab/test_governance_guards.py tests/test_local_ci_matrix.py tests/test_dependency_security.py` -> `28 passed`.
  - `bash scripts/tests/test_pre_commit_hook.sh` -> `pass=11 fail=0`.
- Hosted branch protection verified after setup:
  - `main`: strict status checks required for `governance`, `python-core`,
    `architecture`, `frontend`, `main-promotion-source`, `gitleaks`,
    `trivy-fs`, `semgrep`, and `npm-audit`; solo-maintainer mode has no required
    reviewer; admin enforcement enabled; conversation resolution required;
    force-push and deletion disabled.
  - `dev`: strict status checks required for `governance`, `python-core`,
    `architecture`, `frontend`, `gitleaks`, `trivy-fs`, `semgrep`, and
    `npm-audit`; solo-maintainer mode has no required reviewer; admin
    enforcement enabled; conversation resolution required; force-push and
    deletion disabled.
  - Repository rulesets remain `[]`; protection is implemented through branch
    protection rather than rulesets.

## Current Verdict

Protected PR workflow is configured for `main` and `dev`, and the repository has
an explicit split open-source licensing model for software and documentation.
