# Tasks — Real-Data ≥2-Asset OOS-Net Backtest

TDD order: write failing tests first (RED), implement to green (GREEN), then
REFACTOR with gates green. Keep `no_alpha_claim` on every artifact.

- [ ] **T1 [REQ-RDO-001/002/003] RED** — author `tests/quantlab/test_real_data_oos.py`:
  - unit: sufficiency (≥2/<2 assets, span ≥/< min), report ranking OOS-net desc +
    baseline visible, artifact checksum round-trip, `validate_*` raises on
    tamper/missing-baseline/wrong-claim, insufficient artifact empty rows.
  - PBT (hypothesis): sufficiency true for valid ≥2-asset panels; checksum
    canonicalization invariance.
  - integration: in-memory sufficient-history provider → candidate+baseline →
    computed artifact validates; future-revision invariance (no lookahead);
    survivorship (delisted-at-end asset); net≠gross under nonzero cost.
  - Confirm the suite FAILS (module absent).
- [ ] **T2 [REQ-RDO-001/003] GREEN** — implement `quantlab/research/real_data_oos.py`:
  `DataSufficiency`, `assess_data_sufficiency`, `build_real_data_oos_report`,
  `build_insufficient_data_report`, `build_real_data_oos_artifact`,
  `validate_real_data_oos_artifact`, `write_real_data_oos_artifact`. Export from
  `quantlab/research/__init__.py`.
- [ ] **T3 [REQ-RDO-002] GREEN** — ensure report path reads only through
  `provider.history/get/universe`; no direct file/raw access; make future-revision
  invariance + survivorship + net≠gross tests pass.
- [ ] **T4 [REQ-RDO-001/003] GREEN** — add CLI `scripts/run_real_data_oos_backtest.py`:
  load vintage provider, assess sufficiency, fail closed (exit 2) on
  insufficient with an `insufficient_data` artifact, else exit 0 with computed
  artifact; `--out` writes deterministic sorted JSON, omitted prints to stdout.
  Add a CLI test (sufficient fixture → exit 0; thin/real → exit 2).
- [ ] **T5 [tests] REFACTOR** — dedupe shared OOS-net extraction with
  `quantlab/models/evaluation.py` helpers where clean; tighten types for mypy;
  keep behavior identical with gates green.
- [ ] **T6 [mutation] GREEN** — add 3 `MutationSpec` entries to
  `scripts/run_mutation_spot_checks.py` (asset-gate, oos-net-segment,
  baseline-visibility) each pointing at a test that fails under mutation; run the
  new specs and confirm killed.
- [ ] **T7 [registry] GREEN** — update `quantlab/TESTS.md` and
  `.agents/specs/TESTS.md` with the new test rows + mutation names mapped to
  REQ-RDO-001/002/003.
- [ ] **T8 [gates]** — run local matrix: `uv run pytest -q`,
  `uv run mypy quantlab/ scripts/run_real_data_oos_backtest.py --ignore-missing-imports`,
  `uv run lint-imports`, new-module focused coverage, new mutation spot checks.
  Record results in the implementation report.
- [ ] **T9 [review]** — author `review.md` with verdict copied from evidence
  (PASSED only if gates pass); honest boundaries (real disk data still
  `insufficient_data`; mechanism proven on sufficient-history fixtures;
  `no_alpha_claim`). Then hand registry/NEXT_STEPS/RTM sync to
  `spec-registry-manager` / governance.
