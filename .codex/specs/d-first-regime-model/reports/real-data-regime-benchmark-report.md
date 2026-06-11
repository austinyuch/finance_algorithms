# D-3 Real-Data-Shaped Regime Benchmark Report

Date: 2026-06-11

## Summary

Added a D-3 benchmark helper that runs the first regime model against a static baseline using an A0 PIT provider built from vintage source payloads. The test fixture uses FRED-style raw CSV snapshots through `build_provider_from_vintage`, so it exercises the data path rather than bypassing it with hand-built provider frames.

## Implemented Surface

- `quantlab/models/regime_benchmark.py`
  - `benchmark_price_dates(data, symbols, asof)`
  - `run_real_data_regime_benchmark(data, dates, store, ...)`
- `tests/quantlab/test_d_3_real_data_regime_benchmark.py`
  - PBT as-of-gated benchmark date selection
  - integration run against `LocalResultStore`
  - explicit `no_alpha_claim` assertion

## Verification

```bash
uv run pytest -q tests/quantlab/test_d_3_real_data_regime_benchmark.py
uv run coverage run -m pytest -q tests/quantlab/test_d_3_real_data_regime_benchmark.py
uv run coverage report -m quantlab/models/regime_benchmark.py
```

Results:
- D-3 tests: **2 passed**.
- Line coverage: `quantlab/models/regime_benchmark.py` **92%**.
- Mutation: changing `claim_boundary` to `alpha_claim` was killed by the D-3 integration test.

## Claim Boundary

This proves a real-source-format vintage benchmark path and OOS-net baseline logging. It does not claim the regime model has alpha, and the current checked-in live vintage data is still sparse.
