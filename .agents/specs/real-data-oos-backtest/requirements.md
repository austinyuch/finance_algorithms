# Requirements — Real-Data ≥2-Asset OOS-Net Backtest

## Introduction

The A0 vectorized engine and the D model families have so far been proven on
synthetic data only: every existing slice is explicitly *pipeline-correctness*
with a `no_alpha_claim` boundary. The platform's stated success criterion is
methodology honesty plus experiment capability, not alpha. This slice produces
the project's first *honest real-data experiment artifact*: it runs the existing
A0 engine and a dumb baseline over **real point-in-time vintage data across ≥2
price assets** and emits a checksumed OOS-net comparison report. It changes no
engine semantics — it exercises the existing engine/loader on real-source-format
data under strict PIT, survivorship, cost, and walk-forward rules, and it fails
closed (never green) when accumulated history is insufficient.

This is deliberately scoped to *mechanism + honest comparison on real data*, not
a multi-year strategy validation. Data-volume sufficiency is an explicit
external gate, because real daily history only accrues as the append-only
snapshot routine keeps running.

## Dependencies, Impacts & CRs

- [Depends On: a0-backtest-foundation, b-data-platform (vintage loader, PIT,
  source quorum CR-B19), d-first-regime-model (baseline strategy + OOS-net
  benchmark helper)]
- [Impacts: d-model-family-evaluation (real-data records become rankable),
  f-showcase-read-api-dashboard (real OOS-net runs can surface in the dashboard
  later), RTM "Real-data backtest" open gap]
- [Open Change Requests: none]

## Repo-side Closure vs External Execution

- **Repo-side Closure**: add a real-data OOS-net runner (script + slice helper)
  that loads ≥2 price assets through the existing PIT vintage loader, runs the
  A0 engine for a strategy and a dumb baseline, and writes a checksumed OOS-net
  comparison artifact with explicit data-sufficiency status. Add PIT/no-lookahead
  and data-sufficiency tests on the real-data path, plus mutation coverage.
- **External Execution**: accumulation of *enough* real daily history across ≥2
  price assets is calendar-time dependent and runs outside this slice via the
  daily snapshot routine (`scripts/daily_snapshot.py` / `daily-snapshot.yml`).
  As of capture, only `yahoo_2330.TW` and `yahoo_idx_^TWII` exist as real price
  series with thin history; broad source quorum is CR-B19-proven but history
  depth is still short.
- **External Blockers / Constraints**: until ≥2 price assets accumulate a
  walk-forward-viable window, the runner must report `status=insufficient_data`
  / `not_proven` and must never emit an OOS-net "result" that could read as a
  validated or alpha-bearing comparison. Vintage snapshots remain immutable;
  this slice only reads them.

## Requirements

### Requirement 1 [REQ-RDO-001]

**User story:** As a researcher, I want the existing A0 engine run over real
≥2-asset PIT data against a dumb baseline, so I have a first honest OOS-net
comparison artifact instead of synthetic-only proofs.

#### Acceptance Criteria

1. When ≥2 real price assets with a walk-forward-viable window are available via
   the PIT vintage loader, then the runner shall execute the A0 engine for both
   a candidate strategy and a dumb baseline and write a checksumed artifact
   reporting OOS-**net** metrics for both, ranked OOS-net only with the baseline
   visible.
2. When the artifact is written, then it shall record the asset set, as-of
   window, cost/slippage/FX/tax configuration applied, and data provenance
   (vintage capture dates / `available_date` coverage).
3. When the output path is provided, then the runner shall write deterministic
   sorted JSON; when omitted, it shall print the artifact to stdout.

### Requirement 2 [REQ-RDO-002]

**User story:** As a correctness reviewer, I want the real-data path to obey PIT
and survivorship rules, so no lookahead or survivorship bias can enter the first
real comparison.

#### Acceptance Criteria

1. When the runner loads any value, then it shall respect `available_date <=
   asof`; if any requested value would require data later than `asof`, then it
   shall fail closed rather than substitute a revised/future value.
2. When the universe is resolved at an as-of date, then it shall preserve
   survivorship handling through listings data (assets present at that time,
   including ones later delisted).
3. When net metrics are computed, then costs, slippage, FX, and walk-forward
   boundaries shall be applied on the real-data path, and a test shall prove the
   net result differs from the gross result under nonzero costs.

### Requirement 3 [REQ-RDO-003]

**User story:** As a maintainer, I want the runner to fail closed on insufficient
data and to keep the honest claim boundary, so a thin-history run cannot be
mistaken for a validated or alpha-bearing result.

#### Acceptance Criteria

1. If fewer than 2 real price assets are available, or accumulated history is
   below the configured walk-forward minimum, then the runner shall emit
   `status=insufficient_data` (nonzero/at-most-`not_proven`) and shall not write
   a success comparison artifact.
2. When any artifact is emitted (including insufficient-data), then it shall
   carry `claim_boundary=no_alpha_claim` and shall not describe the run as
   validated, production, or alpha-bearing.
3. When data later satisfies the threshold, then re-running shall upgrade the
   status without manual edits to prior immutable vintage snapshots.
