# Design — G Alt-Data First Slice

## Classification

New optional G spec.

## Design

- Add `quantlab.data.alt_data`.
- `AltDataSourceContract` owns authority/pin/default-enabled/readiness posture.
- `load_alt_data_csv` reads local files only and filters by `available_date <= asof`.
- No integration into daily defaults or portfolio models in this first slice.

## FMEA

| Risk ID | Failure Mode | Effect | Control |
|---|---|---|---|
| G-FM-01 | Optional source becomes default-enabled | Unvetted external dependency | Contract default is false and tests assert it |
| G-FM-02 | Loader returns future-available rows | Lookahead bias | PBT and mutation around PIT gate |
| G-FM-03 | Unknown contract is loaded as ready | Source-contract false green | Strict mode rejects unready contracts |
