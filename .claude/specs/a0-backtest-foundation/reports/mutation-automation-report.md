# Mutation Automation Report

Date: 2026-06-11

## Summary

Added a repo-local mutation spot-check runner for critical QuantLab invariants. It avoids the current mutmut sandbox/layout issue by applying deterministic text mutations in-place, running targeted tests that must fail, and restoring the original file in a `finally` block.

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

Results:
- Runner tests: **7 passed**.
- Mutation suite: **3/3 killed**.
- Runner line coverage: **89%**.

## Claim Boundary

This repairs automated spot-check mutation coverage for selected critical invariants. It does not claim full mutmut mutation-score coverage across the repo.
