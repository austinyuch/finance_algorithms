# Design — E Tier3 Production Evidence Gate

## Overview

The readiness gate now treats production Tier3 readiness as a higher authority than local smoke proof. Each required key is accepted only when the submitted evidence is a mapping with:

- `status=proven`
- `readiness_evidence_for=<required_key>`
- `evidence_tier=production`

Local smoke builders remain useful for regression proof and demo evidence, but they are explicitly marked `evidence_tier=local_smoke`.

## Components

| Component | Responsibility |
|---|---|
| `_is_production_evidence` | Shared predicate for Tier3 readiness acceptance. |
| `build_tier3_readiness_gate` | Computes missing production evidence and returns `tier3_ready` only when no required production evidence is missing. |
| `build_serving_smoke_evidence` / `build_retraining_smoke_evidence` | Continue executable local smoke proof, now explicitly tiered as `local_smoke`. |
| `build_automated_drift_monitoring_evidence` | Executes a monitor callable and emits local automated drift monitoring smoke evidence. |
| `validate_*_evidence` | Reject wrong artifact kinds, alpha claims, wrong readiness targets, unsupported statuses, wrong tiers, and missing metrics. |

## FMEA

| Failure mode | Control |
|---|---|
| Arbitrary `status=proven` maps promote `tier3_ready`. | Gate requires correct readiness target and `evidence_tier=production`. |
| Local smoke evidence is mistaken for production proof. | Local builders and validators require `evidence_tier=local_smoke`; gate rejects non-production tiers. |
| Automated drift monitor overclaims alpha or omits measurable deltas. | Builder and validator reject `alpha_claim`, unsupported statuses, and empty `metric_deltas`. |
| Drift monitor output is non-deterministic or opaque. | Evidence stores deterministic request/result digests and normalized metric deltas. |

## Boundaries

- No production endpoint is deployed.
- No production retraining scheduler is configured.
- No production drift monitoring service is configured.
- The slice proves local automation and fail-closed governance only.
