# Design — Epic D:First Regime Model

> SDD Phase 2. Requirements: [requirements.md](./requirements.md).

## 1. Overview

The first D slice should prove the model-evaluation discipline before adding heavy ML infrastructure. It will produce a deterministic regime signal from PIT features, run it through A0 reporting, and preserve a clean handoff point for C-3 rebalance triggers.

## 2. Architecture

```text
PIT provider
  ├─ macro(asof, series) / history(asof, close, symbols)
  ↓
RegimeFeatureBuilder(asof)
  ↓
FirstRegimeClassifier.predict(asof, data)
  ↓
RegimeSignal(label, confidence, feature_status)
  ↓
future C-3 rebalance hook / D leaderboard experiment
```

Proposed code boundary:

```text
quantlab/models/
  regime.py        RegimeSignal, FirstRegimeClassifier
  features.py      PIT-safe feature extraction helpers
tests/quantlab/
  test_d_1_regime.py
```

## 3. Test Coverage Declaration

- Unit tests: PIT feature extraction, missing-feature fallback, deterministic labels.
- Integration tests: A0 run/log path comparing regime-aware strategy stub vs no-regime/static baseline.
- Critical evidence: OOS-net leaderboard rows. Synthetic data is acceptable for first-slice correctness, but any writeup must label it as synthetic unless real vintage data is used.

## 4. Repo-side Closure vs External Execution Boundary

- **Repo-side Closure:** feature builder, deterministic classifier, tests, A0 leaderboard comparison, conservative writeup.
- **External Execution:** none required for first slice.
- **External Blockers:** real macro/market usefulness remains data-dependent and should not be claimed from synthetic fixtures.

## 5. Components

- `RegimeSignal`: small data structure with `label`, optional `confidence`, and `feature_status`.
- `FirstRegimeClassifier`: rules-based first slice, for example using trend + yield curve / inflation availability to emit labels such as `risk_on`, `defensive`, `inflation`, `unknown`.
- Baseline comparison: no-regime/static allocation remains the acceptance yardstick.

## 6. Lightweight FMEA

| Risk ID | Failure Mode | Effect | Control | Task |
|---|---|---|---|---|
| FMEA-D-01 | Feature builder reads revised/future macro values | Lookahead bias | only use provider `macro(asof, ...)` / `history(asof, ...)`; no raw file shortcuts | D-1 |
| FMEA-D-02 | Synthetic fixture result is presented as real alpha | Overclaim | writeup must label data source and report failed baselines honestly | D-3 |
| FMEA-D-03 | Regime label vocabulary drifts across runs | C-3 integration fragility | stable label enum and metadata tests | D-1 |
| FMEA-D-04 | Heavy ML framework leaks into engine/data | Architecture violation | import isolation test remains mandatory | D-2 |

## 7. Evaluation Standard

The first model spec is successful if it produces a deterministic PIT-safe regime signal and an OOS-net comparison against naive baselines. It is not required to outperform the baseline.

## 8. Traceability

| Requirement | Design Section | Planned Evidence |
|---|---|---|
| REQ-D-REGIME-001 | §2, §5 | `test_d_1_regime.py` |
| REQ-D-BASELINE-001 | §3, §7 | D integration leaderboard test/writeup |
| REQ-D-HOOK-001 | §2, §5 | signal contract tests |
