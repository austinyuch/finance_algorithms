# Tasks — Real-Data ≥2-Asset OOS-Net Backtest

TDD order: write failing tests first (RED), implement to green (GREEN), then
REFACTOR with gates green. Keep `no_alpha_claim` on every artifact.

- [x] **T1 [REQ-RDO-001/002/003] RED** — author `tests/quantlab/test_real_data_oos.py`:
  - unit: sufficiency (≥2/<2 assets, span ≥/< min), report ranking OOS-net desc +
    baseline visible, artifact checksum round-trip, `validate_*` raises on
    tamper/missing-baseline/wrong-claim, insufficient artifact empty rows.
  - PBT (hypothesis): sufficiency true for valid ≥2-asset panels; checksum
    canonicalization invariance.
  - integration: in-memory sufficient-history provider → candidate+baseline →
    computed artifact validates; future-revision invariance (no lookahead);
    survivorship (delisted-at-end asset); net≠gross under nonzero cost.
  - Confirm the suite FAILS (module absent).
- [x] **T2 [REQ-RDO-001/003] GREEN** — implement `quantlab/research/real_data_oos.py`:
  `DataSufficiency`, `assess_data_sufficiency`, `build_real_data_oos_report`,
  `build_insufficient_data_report`, `build_real_data_oos_artifact`,
  `validate_real_data_oos_artifact`, `write_real_data_oos_artifact`. Export from
  `quantlab/research/__init__.py`.
- [x] **T3 [REQ-RDO-002] GREEN** — ensure report path reads only through
  `provider.history/get/universe`; no direct file/raw access; make future-revision
  invariance + survivorship + net≠gross tests pass.
- [x] **T4 [REQ-RDO-001/003] GREEN** — add CLI `scripts/run_real_data_oos_backtest.py`:
  load vintage provider, assess sufficiency, fail closed (exit 2) on
  insufficient with an `insufficient_data` artifact, else exit 0 with computed
  artifact; `--out` writes deterministic sorted JSON, omitted prints to stdout.
  Add a CLI test (sufficient fixture → exit 0; thin/real → exit 2).
- [x] **T5 [tests] REFACTOR** — dedupe shared OOS-net extraction with
  `quantlab/models/evaluation.py` helpers where clean; tighten types for mypy;
  keep behavior identical with gates green.
- [x] **T6 [mutation] GREEN** — add 3 `MutationSpec` entries to
  `scripts/run_mutation_spot_checks.py` (asset-gate, oos-net-segment,
  baseline-visibility) each pointing at a test that fails under mutation; run the
  new specs and confirm killed.
- [x] **T7 [registry] GREEN** — update `quantlab/TESTS.md` and
  `.agents/specs/TESTS.md` with the new test rows + mutation names mapped to
  REQ-RDO-001/002/003.
- [x] **T8 [gates]** — run local matrix: `uv run pytest -q`,
  `uv run mypy quantlab/ scripts/run_real_data_oos_backtest.py --ignore-missing-imports`,
  `uv run lint-imports`, new-module focused coverage, new mutation spot checks.
  Record results in the implementation report.
- [x] **T9 [review]** — author `review.md` with verdict copied from evidence
  (PASSED only if gates pass); honest boundaries (real disk data still
  `insufficient_data`; mechanism proven on sufficient-history fixtures;
  `no_alpha_claim`). Then hand registry/NEXT_STEPS/RTM sync to
  `spec-registry-manager` / governance.

## CR-RDO-004 — sampling-frequency homogeneity guard (Implemented · merged)

See [change-requests/cr-rdo-004-sampling-frequency-guard.md](./change-requests/cr-rdo-004-sampling-frequency-guard.md).
TDD complete; merged via PR #95 (`dev`==`main`).

- [x] **M1 [REQ-RDO-CR4-001/002] RED** — author `tests/quantlab/test_real_data_oos_frequency.py`
  (cadence classification boundaries, `estimate_sampling_frequencies` on daily/monthly
  providers, `frequency_homogeneous`, oversampling fail-closed, coarse-rebalance pass,
  provenance) + PBT (`is_oversampled` formula; `classify_cadence` monotonic). Confirm RED.
- [x] **M2 [REQ-RDO-CR4-001/002] GREEN** — implement `SamplingFrequency`,
  `SamplingFrequencyError`, `classify_cadence`, `rebalance_cadence_days`, `is_oversampled`,
  `estimate_sampling_frequencies`; extend `DataSufficiency`; add the oversampling guard +
  `sampling_frequency` provenance in `build_real_data_oos_report`.
- [x] **M3 [REQ-RDO-CR4-003] GREEN** — CLI maps `SamplingFrequencyError` →
  `reason=oversampled_vs_native_frequency` (exit 2) ahead of the degeneracy catch; add a
  CLI oversampled-fail-closed test. Default single-index SP500 run stays `computed`.
- [x] **M4 [mutation] GREEN** — add `real-data-oos-sampling-frequency-guard` to
  `scripts/run_mutation_spot_checks.py` (flip the oversampling `>`); confirm killed.
- [x] **M5 [registry] GREEN** — `quantlab/TESTS.md` + `.agents/specs/TESTS.md` rows;
  count resync (pytest 355→367, mutation 109→110) across governance surfaces.
- [x] **M6 [gates + cascade]** — full suite 374, mutation 118/118, mypy clean,
  <!-- as-of M6 close; current workspace evidence is 402/115 after later CRs (CR-RDO-005 + CR-DME-001) -->
  lint-imports KEPT, frontend 46, governance guards 25, visual 0-pixel; dashboard
  dataHash → `c73d7c88`; public hosting re-proven (PR #97).
