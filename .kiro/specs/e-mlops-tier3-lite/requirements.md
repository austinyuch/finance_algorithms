# Requirements — E MLOps Tier3 Lite

## Introduction

This first E slice adds registry-first experiment governance for the three D model families. It records model lineage, reusable run configuration, run IDs, metrics, and conservative claim boundaries without implementing serving, retraining, or drift monitoring.

## Dependencies, Impacts & CRs

- [Depends On: a0-backtest-foundation, d-first-regime-model, d-return-risk-forecast-model, d-robust-portfolio-optimization-model, f-showcase-read-api-dashboard]
- [Impacts: f-showcase-read-api-dashboard] dashboard consumers can later read registry metadata.
- [Open Change Requests: none]

## Repo-side Closure vs External Execution

- **Repo-side Closure:** JSONL experiment registry, tests, mutation spot check, coverage, registry/test governance updates.
- **External Execution:** none.
- **External Blockers / Constraints:** full Tier3 serving, retraining cadence, and drift monitoring remain intentionally out of scope.

## Requirements

### Requirement 1 [REQ-E-LITE-REG-001]

**User Story:** As a QuantLab researcher, I want experiment configs and model lineage recorded, so that model families can be compared reproducibly without implying production MLOps readiness.

#### Acceptance Criteria

1. When an experiment is registered, the system shall persist model family, strategy name, config, run IDs, metrics, tags, and `no_alpha_claim`.
2. When the same model family, strategy, and config are registered again, the system shall return the same deterministic experiment ID instead of duplicating the entry.
3. If an experiment attempts an `alpha_claim`, the system shall reject it.

### Requirement 2 [REQ-E-LITE-READ-001]

**User Story:** As a dashboard or governance reader, I want registry entries to expose their readiness tier, so that registry-only evidence is not mistaken for serving or drift monitoring.

#### Acceptance Criteria

1. When a registry entry is read back, it shall include `status=research_only`.
2. When a registry entry is read back, it shall include `readiness=registry_only`.
3. While E-lite is active, the system shall not claim serving, auto-retraining, or drift monitoring.
