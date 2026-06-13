# CR-RDO-002 — Surface the real OOS-net comparison in the dashboard (#2c)

## Context

`real-data-oos-backtest` (+ CR-RDO-001) produces a committed, checksumed real-data
OOS-net comparison artifact. The F showcase dashboard previously showed only the
canonical local-result-store scenario. This CR surfaces the **real** OOS-net
comparison in the dashboard payload + UI, under `no_alpha_claim`, without
upgrading any readiness claim.

Depends on **CR-FBP-001** (the visual traceability guard had to tolerate a
deterministically re-pinned baseline before the dashboard render could change).

## Change

- `quantlab/showcase/scenario.py`: `_real_data_section(evidence_root)` loads the
  committed `real-data-oos-artifact.json` (only when `status=computed` /
  `no_alpha_claim`), ranks rows OOS-net desc with a visible baseline, and attaches
  it as an optional `realData` block on the payload. Degrades to None (omits the
  block) when the artifact is absent.
- `frontend/lib/showcase-contract.ts`: optional `RealDataComparison` type +
  validation (computed / `no_alpha_claim` / ≥2 rows / visible baseline / ranked).
- `frontend/components/Dashboard.tsx`: compact `real-data` panel (rendered only
  when present), below the experiment registry.

## Requirements

### REQ-RDO-CR2-001 — surface under no_alpha_claim
1. When the committed artifact is a computed comparison, the payload carries a
   `realData` block (`source=real_data_oos_backtest_artifact`, `no_alpha_claim`,
   ranked rows, visible baseline) and the dashboard renders a `real-data` panel.
2. The contract validator rejects a `realData` block that loses `no_alpha_claim`,
   drops below 2 rows, hides the baseline, or is mis-ranked.
3. Absent/invalid artifact → no `realData` block; dashboard degrades to the
   canonical scenario (no overclaim). `publicHosting` stays `not_proven`.

## Implementation & Review — PASSED

- Tests: `frontend/tests/dashboard.test.tsx` (render + reject, 46 frontend total);
  `tests/quantlab/test_f_1_showcase_api.py` (surfaces / omits-without-evidence).
- Visual: the dashboard render changed, so both visual baselines were re-pinned
  (static-contract htmlHash + browser screenshot `0f2b849…`, 0-pixel diff —
  guard-legal under CR-FBP-001). Public-hosting `dataHash` parity restored
  (manifest == probe `expectedDataHash`); `publicHosting` remains
  `not_proven` / `configured_not_observed`.
- Gates: pytest **338**, frontend **46**, mypy 60, lint-imports KEPT 77/198,
  Python mutation **106/106**, frontend line coverage **90.00%**. Full suite green.
- Boundary: OOS-net values are mechanism evidence under `no_alpha_claim`, not a
  strategy verdict; sampling-frequency harmonization remains the documented
  follow-up.
