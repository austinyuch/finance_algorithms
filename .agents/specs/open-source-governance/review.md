# Open Source Governance Review

Status: Implemented; license chosen and committed (Apache-2.0, owner decision `2026-06-19`)

## Evidence

- Repo public state: `gh api repos/austinyuch/finance_algorithms` reported
  `"private": false`, default branch `main`, and (before this lane closed) no
  detected license.
- License decision (REQ-OSG-004 AC5; closes OSG-FM-005):
  - Owner chose **Apache-2.0** on `2026-06-19` for the public quant lab + demo
    (permissive reuse with an explicit patent grant and trademark protection).
  - Committed license surfaces:
    - `LICENSE` (verbatim Apache License 2.0 text; copyright
      `2026 Yueh-Cheng Chang`).
    - `NOTICE` (attribution plus the existing `no_alpha_claim` /
      point-in-time / approximate-data research boundary).
    - `pyproject.toml` -> `license = "Apache-2.0"`,
      `license-files = ["LICENSE", "NOTICE"]`.
    - `frontend/package.json` -> `"license": "Apache-2.0"` (`"private": true`
      retained as an npm anti-publish guard, not a license statement).
    - `README.md` and `CONTRIBUTING.md` License sections point at `LICENSE`.
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

Protected PR workflow is configured for `main` and `dev`, and the repository now
declares reusable open-source terms under **Apache-2.0**. All seven lane tasks
(T-OSG-001 .. T-OSG-007) are complete; no open-source readiness gap remains in
this lane.
