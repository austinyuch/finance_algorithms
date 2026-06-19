# Security Policy

## Supported Branches

Security fixes are handled on `dev` and promoted to `main` through pull requests.
Direct pushes to `main` and `dev` are not part of the project workflow.

## Reporting a Vulnerability

Please report vulnerabilities privately by opening a GitHub security advisory for
this repository, or by contacting the repository owner directly if advisory access
is unavailable. Do not disclose exploitable details in public issues until a fix
or mitigation is available.

Include:

- affected files, commands, or public endpoints;
- reproduction steps;
- expected impact;
- whether secrets, private data, or misleading public demo evidence may be involved.

## Secret and Data Handling

Do not commit `.env` files, API keys, tokens, private keys, broker credentials, or
private financial data. `.env.example`, placeholders, and documented environment
variable names are acceptable when they contain no real secret value.

Historical and generated research data must keep the existing point-in-time,
approximate-data, and `no_alpha_claim` boundaries documented under `.agents/specs/`
and `quantlab/CORRECTNESS_CHECKLIST.md`.
