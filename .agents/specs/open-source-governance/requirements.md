# Open Source Governance Requirements

## Scope

Prepare the public repository for open-source collaboration while protecting
`main` and `dev` through pull requests, local-first CI evidence, and security
guards. This lane governs repository policy and CI surfaces only; it does not
change QuantLab model behavior, data semantics, public demo claims, or legacy
`invest_algorithms` behavior.

## Requirements

### REQ-OSG-001 Branch Protection

`main` and `dev` must reject direct pushes through GitHub branch protection or
rulesets. Changes must enter through pull requests.

#### Acceptance Criteria

1. GitHub reports active protection or rulesets for both `main` and `dev`.
2. Pull requests to `main` require the configured CI/security checks.
3. Pull requests to `dev` require the configured CI/security checks.
4. Force-push and branch deletion are disabled for both branches.

### REQ-OSG-002 Pull Request Gate

The repository must provide a PR CI workflow that covers governance, core Python
correctness smoke, architecture boundaries, and frontend build/test paths.

#### Acceptance Criteria

1. `.github/workflows/pr-ci.yml` runs on pull requests to `main` and `dev`.
2. The workflow has separate required check names for governance, Python core,
   architecture, frontend, and `main` promotion source validation.
3. The workflow keeps daily scheduled snapshot semantics separate from routine PR
   gates.

### REQ-OSG-003 Security Scanning

The repository must provide secret and vulnerability scanning suitable for a
public Python/Node repository.

#### Acceptance Criteria

1. Pull requests to `main` and `dev` run secret scanning.
2. Pull requests and protected-branch pushes run filesystem vulnerability/SCA
   scanning.
3. Pull requests run SAST scanning.
4. Frontend dependency audit fails on high or critical advisories.

### REQ-OSG-004 Open Source Contribution Surfaces

The repository must document how contributors should report security issues,
submit PRs, and obtain owner review.

#### Acceptance Criteria

1. `SECURITY.md` exists.
2. `CONTRIBUTING.md` exists.
3. `.github/CODEOWNERS` exists.
4. A pull request template exists.
5. License selection is explicitly tracked as an owner decision until a license
   is chosen.

### REQ-OSG-005 Local Secret Guard

The repository must provide a local pre-commit guard, derived from the tested
governance pattern in `aclab-middlewares`, to prevent accidental secret commits.

#### Acceptance Criteria

1. `scripts/git-hooks/pre-commit` blocks real `.env` files and literal secrets.
2. `.env.example`, placeholders, type declarations, and environment variable
   references are allowed.
3. `scripts/tests/test_pre_commit_hook.sh` regression-tests blocking and allowed
   cases.
4. `scripts/install-git-hooks.sh` installs the hook.
