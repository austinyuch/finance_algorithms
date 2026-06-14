# CR-FPS-011 — Deterministic hosting-evidence freshness + refresh automation

## Problem

Two coupled defects in the public-hosting freshness handling:

1. **Wall-clock suite-rot time-bomb.** The Python committed-evidence consumer
   `quantlab/showcase/scenario.py::_validate_public_hosting_probe` enforces
   `observedAt + maxAgeHours < datetime.now()` and **raises** when the committed
   observation ages past the 24h window — using a hidden wall-clock `now()`. So
   the committed `proven` probe and the test fixtures become latent failures:
   the dashboard build and the test suite break ~24h after any re-prove, with
   **no code change**. (Concretely, the line-262 fixture expires 24h after its
   hard-coded `observedAt`; the committed proof expires 24h after each capture.)

2. **Contract inconsistency with CR-FPS-008.** CR-FPS-008 already settled the
   correct contract on the frontend (`classifyPublicHostingEvidence`): stale
   hosting evidence must **downgrade to `configured_not_observed`** (req 2), and
   classification is **deterministic with an injected `now`**. The Python
   consumer never got that treatment — it hard-raises and reads wall-clock time
   internally, contradicting the established contract.

3. **No refresh automation.** Restoring `proven` after a redeploy is a manual
   re-probe + hand-edit of the committed probe/manifest (as done in CR-FPS-010
   / CR-RDO-003). There is no schedulable command to re-prove or auto-downgrade.

## Requirements

### REQ-FPS-CR11-001 — Deterministic freshness (no hidden wall-clock)
The Python hosting-evidence consumer classifies observation freshness against an
explicit `asof` reference time threaded from the build entry points
(`build_canonical_dashboard_artifact` / `write_canonical_dashboard_artifact`),
mirroring the CR-FPS-008 frontend injected `now`. `asof=None` resolves to
`datetime.now(timezone.utc)` only at the entry boundary; the classification core
takes `asof` explicitly so it is deterministically testable.

### REQ-FPS-CR11-002 — Stale downgrades, never crashes; integrity still hard-fails
- Committed hosting evidence whose observation is beyond the freshness window
  (`observedAt + maxAgeHours <= asof`) **or** which self-declares
  `freshnessStatus != "fresh"` **downgrades** the effective hosting status to
  `configured_not_observed` and the evidence string records it as stale. The
  build does **not** raise.
- The dashboard `demoReadiness.publicHosting` stays `not_proven` regardless
  (unchanged design invariant); a stale `proven` probe can **never** present as
  `proven`. Fail-closed against overclaim is preserved.
- Genuine integrity violations still hard-raise: future `observedAt`, malformed/
  non-UTC `observedAt`, wrong `targetUrl`/`httpStatus`/`deployedManifestStatus`,
  unmatched manifest contract, unsupported status, missing `claimBoundary`, and
  `proven` without a matched deployed `dataHash`.

### REQ-FPS-CR11-003 — Refresh automation (replaces manual re-prove)
`scripts/refresh_public_hosting_proof.py` re-probes the live deployment and
rewrites the committed `docs/public-hosting-probe.json` (+ `docs/review/assets/`
copy) and `docs/deployment-manifest.json` `hostingEvidence` to:
- `proven` iff the live deployed `dataHash` matches `expectedDataHash`, HTTP/
  manifest-contract checks pass, and the observation is fresh; else
- `configured_not_observed`.
It is schedulable, fails closed on probe error (non-zero exit, no partial
write), and never emits `proven` without a matched fresh observation.

## Design

- `_classify_hosting_freshness(probe, asof) -> "fresh" | "stale"` — pure helper;
  integrity checks stay in `_validate_public_hosting_probe(probe, *, asof)`,
  which raises only on integrity violations and returns the freshness verdict.
- `_current_evidence_tests(evidence_root, *, asof=None)` threads `asof`; when the
  verdict is `stale` the effective status string is
  `public hosting configured_not_observed (stale, hash <hashStatus>)`; when fresh
  it is unchanged (`public hosting <status> (hash <hashStatus>)`).
- `build_canonical_dashboard_artifact(... , asof=None)` and
  `write_canonical_dashboard_artifact(... , asof=None)` accept and forward `asof`.
- Automation script consumes a probe payload (live or injected for tests) and
  writes the three committed surfaces atomically; `proven` requires matched +
  fresh.

## Tests (TDD)

- Unit: deterministic `asof` fresh-vs-stale classification; stale `proven`
  downgrades to `configured_not_observed`; self-declared `freshnessStatus=stale`
  downgrades; integrity violations still raise (future/invalid observedAt,
  contract, proven-without-hash).
- PBT: for any `observedAt <= asof`, the verdict is `fresh` iff
  `observedAt + maxAgeHours > asof`, and a `proven` probe never yields a `proven`
  effective string once stale.
- Integration: refresh script rewrites all three surfaces to `proven` on a
  matched-fresh injected probe and to `configured_not_observed` on a mismatch,
  and fails closed (no write) on a probe error.
- Mutation: `public-hosting-freshness-downgrade-window` (boundary `>` vs `>=`),
  `public-hosting-stale-downgrade-not-proven` (stale must not stay proven).
- `TESTS.md` registry row + count resync.

## Boundary

No live backend, live QuantLab data, auth, production MLOps, or Tier3 claims.
This only makes committed hosting-evidence freshness deterministic and
non-crashing (consistent with CR-FPS-008) and automates re-proving. Project stays
`local_demo_only` / `no_alpha_claim`.
