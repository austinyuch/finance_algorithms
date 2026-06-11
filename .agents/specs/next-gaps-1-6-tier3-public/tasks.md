# Tasks — Next Gaps 1-6 Tier3/Public/Ops

Lane classification: CR overlay against completed F/E/B/D baselines.

- [x] 1. F public hosting proof [Implements REQ-NG16-F-PUBLIC]
  - [x] 1.1 RED: add Vitest coverage for proven vs configured-not-observed hosting evidence.
  - [x] 1.2 GREEN: add public-hosting classifier and manifest probe fields.
  - [x] 1.3 REFACTOR: keep dashboard runtime readiness separate from static hosting evidence.
  - _Eval: `cd frontend && npm test -- --run tests/public-demo.test.tsx`; `cd frontend && npm run probe:public-demo`._
- [x] 2. F browser visual proof [Implements REQ-NG16-F-VISUAL]
  - [x] 2.1 RED: add malformed screenshot-hash rejection test.
  - [x] 2.2 GREEN: add browser visual evidence builder and Chromium screenshot smoke.
  - [x] 2.3 REFACTOR: store screenshot evidence as JSON, not binary baseline churn.
  - _Eval: `cd frontend && npm run visual && npm run visual:browser`._
- [x] 3. E Tier3 first real slice [Implements REQ-NG16-E-TIER3]
  - [x] 3.1 RED: add manifest/drift skeleton tests and PBT count preservation.
  - [x] 3.2 GREEN: add artifact manifest, validator, and drift skeleton.
  - [x] 3.3 REFACTOR: preserve no-serving/no-retraining wording in one manifest API.
  - _Eval: `uv run pytest -q tests/quantlab/test_e_1_experiment_registry.py`._
- [x] 4. B scheduled snapshot ops [Implements REQ-NG16-B-SCHEDULE]
  - [x] 4.1 RED: add schedule report retention/latest-pointer test.
  - [x] 4.2 GREEN: add `scripts/snapshot_schedule_report.py`.
  - [x] 4.3 REFACTOR: reuse `snapshot_ops_gate` validation instead of duplicating rules.
  - _Eval: `uv run pytest -q tests/test_daily_snapshot.py`._
- [x] 5. D real-source family evaluation [Implements REQ-NG16-D-EVAL]
  - [x] 5.1 RED: add LocalResultStore-backed evaluator test.
  - [x] 5.2 GREEN: add result-store wrapper over existing evaluator.
  - [x] 5.3 REFACTOR: keep ranking authority in the existing OOS-net evaluator.
  - _Eval: `uv run pytest -q tests/quantlab/test_d_6_model_family_evaluation.py`._
- [x] 6. B Stooq source-contract decision [Implements REQ-NG16-B-STOOQ]
  - [x] 6.1 RED: add decision-helper test for blocked and available Stooq postures.
  - [x] 6.2 GREEN: add `decide_stooq_contract`.
  - [x] 6.3 REFACTOR: keep decision status-only and non-probing.
  - _Eval: `uv run pytest -q tests/test_daily_snapshot.py`._
- [x] 7. Verification and governance closeout
  - [x] 7.1 Run full Python, typing, import, mutation, frontend coverage/build/visual/browser/smoke/audit gates.
  - [x] 7.2 Refresh `quantlab/TESTS.md`, `.agents/specs/TESTS.md`, `SPECS.md`, `NEXT_STEPS.md`, and `review.md`.
