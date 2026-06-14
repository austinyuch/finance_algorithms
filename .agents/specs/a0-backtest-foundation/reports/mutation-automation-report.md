# Mutation Automation Report

Date: 2026-06-11
Current status refreshed: 2026-06-13

## Summary

Added a repo-local mutation spot-check runner for critical QuantLab invariants. It avoids the current mutmut sandbox/layout issue by applying deterministic text mutations in-place, running targeted tests that must fail, and restoring the original file in a `finally` block.

Current governance truth is no longer the initial A0-only runner size. The maintained suite is the cross-spec `scripts/run_mutation_spot_checks.py` registry referenced from `quantlab/TESTS.md`; current evidence is **110/110 configured/killed**, including CR-RDO-004 `real-data-oos-sampling-frequency-guard`, CR-A0 event replay, `result-store-finite-oos-net-sharpe`, B source-quorum/Stooq proof gates, F public-hosting/stakeholder payload drift gates, F visual diff contract gating, F public probe freshness/observedAt timestamp and age gating, stale F Next.js fixture review wording, governance refresh review stale-evidence regression, E Tier3 production-readiness gates, Tier3 gate proof-digest guard, Tier3 gate production-validator guard, Tier3 manifest/experiment-binding/retraining artifact URI guards, production drift threshold guard, and governance stale-evidence guards.

## Implemented Surface

- `scripts/run_mutation_spot_checks.py`
  - `engine-regime-selector`
  - `c3-regime-change`
  - `yahoo-latest-close`
- `tests/test_mutation_spot_checks.py`
  - PBT apply/restore roundtrip
  - ambiguity rejection
  - killed/survived command behavior
  - CLI list smoke

## Verification

```bash
uv run pytest -q tests/test_mutation_spot_checks.py
uv run python scripts/run_mutation_spot_checks.py
uv run coverage run -m pytest -q tests/test_mutation_spot_checks.py
uv run coverage report -m scripts/run_mutation_spot_checks.py
```

Initial results:
- Runner tests: **7 passed**.
- Mutation suite: **3/3 killed**.
- Runner line coverage: **89%**.

Current results:
- Runner/governance tests: covered by `uv run pytest -q tests/test_mutation_spot_checks.py tests/quantlab/test_governance_guards.py`.
- Mutation suite: **110/110 configured/killed** via `uv run python scripts/run_mutation_spot_checks.py`.
- Current registry authority: `quantlab/TESTS.md` and `.agents/specs/RTM.md`.

## Claim Boundary

This repairs automated spot-check mutation coverage for selected critical invariants. It does not claim full mutmut mutation-score coverage across the repo.
