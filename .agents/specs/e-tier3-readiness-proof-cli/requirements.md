# Requirements — E Tier3 Readiness Proof CLI

## Introduction

The E production evidence builders reduce false-green risk at the library layer, but external proof handoff still needs an operational entrypoint. This slice adds a strict CLI gate that validates production proof JSON files and emits a Tier3 readiness gate artifact only through the governed validators. Final readiness also requires the manifest artifact URI to point to an external artifact, not a local file or bare label.

## Dependencies, Impacts & CRs

- [Depends On: e-mlops-tier3-lite, e-tier3-production-evidence-gate, e-tier3-production-probes]
- [Impacts: e-tier3-production-probes]
- [Open Change Requests: none]

## Repo-side Closure vs External Execution

- **Repo-side Closure**: add `scripts/tier3_readiness_gate.py`, CLI tests, mutation coverage, and governance updates.
- **External Execution**: production serving, retraining, drift monitoring, and the production manifest artifact must still run or exist outside this repo and provide evidence JSON files/URIs.
- **External Blockers / Constraints**: without externally produced production evidence JSON and an external manifest artifact URI, the CLI cannot prove Tier3 readiness.

## Requirements

### Requirement 1 [REQ-E-CLI-001]

**User story:** As a release reviewer, I want a single CLI gate for Tier3 proof files, so review and CI do not hand-assemble production readiness maps.

#### Acceptance Criteria

1. When the CLI receives a valid Tier3 manifest with an external artifact URI and all three valid governed production evidence files, then it shall write a `tier3_readiness_gate` artifact with `readiness=tier3_ready`.
2. When the output path is omitted, then the CLI shall print the gate artifact JSON to stdout.
3. When the output path is provided, then the CLI shall write deterministic sorted JSON to that file.

### Requirement 2 [REQ-E-CLI-002]

**User story:** As a maintainer, I want the CLI to fail closed on local-smoke or malformed evidence, so production readiness cannot be claimed from fixture/local artifacts.

#### Acceptance Criteria

1. If any evidence file is local-smoke tier, has the wrong artifact kind, has the wrong readiness target, or the manifest artifact URI is local/bare, then the CLI shall return nonzero.
2. If any evidence file lacks required production proof metadata, then the CLI shall return nonzero.
3. If any input JSON is invalid or missing, then the CLI shall return nonzero and shall not write a success artifact.

### Requirement 3 [REQ-E-CLI-003]

**User story:** As a reviewer, I want CLI output to preserve the same claim boundary as the library gate, so downstream docs cannot overstate the evidence.

#### Acceptance Criteria

1. When the CLI succeeds, then the output shall preserve `claim_boundary=no_alpha_claim`.
2. When the CLI succeeds, then the output shall include all three validated evidence artifacts.
3. When one production proof is invalid, then the CLI shall not downgrade it to a warning; it shall fail.
