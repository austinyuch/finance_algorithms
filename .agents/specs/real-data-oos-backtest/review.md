# Review — Real-Data ≥2-Asset OOS-Net Backtest

**Verdict: Implemented · Review PASSED** (repo-side mechanism + honest comparison;
`no_alpha_claim`). Live-demo readiness: not applicable (CLI/library slice; no
new served surface).

## Scope delivered

- `quantlab/research/real_data_oos.py` — `assess_data_sufficiency`,
  `build_real_data_oos_report`, `build_insufficient_data_report`,
  `build_real_data_oos_artifact`, `validate_real_data_oos_artifact`,
  `write_real_data_oos_artifact` (exported from `quantlab/research/__init__.py`).
  Composes the existing A0 `VectorizedEngine` + PIT vintage provider; no engine,
  loader, cost, metric, or walk-forward semantics changed.
- `scripts/run_real_data_oos_backtest.py` — CLI: loads accumulated vintage data,
  runs a candidate strategy + dumb baseline, emits a checksumed OOS-net
  comparison artifact (exit 0), or fails closed to `insufficient_data` (exit 2).

## Requirements → evidence

- **REQ-RDO-001** (real OOS-net comparison, ranked OOS-net, baseline visible):
  PASS — `test_real_data_oos.py::test_report_ranks_oos_net_desc_with_baseline_visible`,
  `::test_report_oos_net_sharpe_uses_out_of_sample_not_in_sample`; CLI exit-0
  computed artifact (`test_real_data_oos_cli.py`).
- **REQ-RDO-002** (PIT no-lookahead, survivorship, net≠gross under cost): PASS —
  `::test_future_revision_does_not_change_oos_output` (a revision available only
  after the window is ignored), `::test_report_provenance_records_survivorship_safe_universe`,
  `::test_net_differs_from_gross_under_nonzero_cost`.
- **REQ-RDO-003** (fail closed to insufficient_data; `no_alpha_claim`; re-run
  upgrades without mutating snapshots): PASS — sufficiency tests, insufficient
  artifact tests, CLI exit-2 tests.

## Gate evidence (local-first)

- `uv run pytest -q` → **324 passed** (was 288; +36 new tests).
- Focused: `quantlab.research.real_data_oos` line coverage **98%**
  (`coverage run -m pytest`); 36 tests across the two new files (unit + PBT +
  integration + CLI).
- `uv run mypy … run_real_data_oos_backtest.py --ignore-missing-imports` → clean,
  **60 source files**.
- `uv run lint-imports` → **KEPT** (76 files / 197 deps); `quantlab.research` is
  not backtest core and imports no ML framework.
- Mutation spot checks → **103/103 killed** (added
  `real-data-oos-sufficiency-asset-gate`, `real-data-oos-net-sharpe-segment`,
  `real-data-oos-baseline-visibility`; full report
  `docs/review/assets/gate-python-mutation.json`).
- Live evidence artifact: `reports/real-data-oos-artifact.json` (`status=computed`,
  `claim_boundary=no_alpha_claim`, BuyAndHold baseline vs RandomStrategy ranked
  OOS-net).

## Honest boundaries / residuals

- **No alpha claim.** OOS-net values are mechanism evidence; the slice proves the
  engine runs on real PIT data and ranks OOS-net honestly, not that any strategy
  has edge.
- **Default universe is not co-temporal.** Real data is "sufficient" by asset
  count (≥2) and calendar span (FRED proxies reach back to 1992), but the default
  proxy set mixes a 1992-start FRED proxy with 2026-only equities, so the current
  computed comparison is degenerate (baseline OOS-net ≈ 0). Refining sufficiency
  to require overlapping multi-asset coverage, and curating a co-temporal default
  universe, is the natural follow-up (candidate CR against this spec). This is
  disclosed, not hidden.
- **Sufficiency gate is coarse** (asset count + calendar span), not density-aware.
- Out of scope: HF/order-book simulation; dashboard surfacing of real runs;
  Stooq enablement (ISSUE-B3-001).

## Registry / governance handoff

- `quantlab/TESTS.md` + `.agents/specs/TESTS.md`: new rows added; counts resynced
  (324 / 60 / 76·197 / 103) across current-state surfaces; historical spec
  reports left at their as-of numbers.
- **`SPECS.md` epic registration** remains to be done by `spec-registry-manager`
  (not added in this lane to avoid premature implemented-epic count drift).
- Promotion (this lane → `dev`/`main`) is normal flow, not part of this review.
