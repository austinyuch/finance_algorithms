# CR-FPS-010 — Public hosting observed `proven`

## Context

After `main` absorbed the full chain (including the #2c realData dashboard),
GitHub Pages (branch source, `main` `/docs`) deployed the new `docs/` artifact.
The deployed `dataHash` now equals the committed manifest `dataHash`
(`40e37b07…`), so the standalone probe observes a genuine `proven` deployment.
This CR commits that observed proof.

## Change

- `docs/public-hosting-probe.json` (+ `docs/review/assets/` copy): refreshed to
  the live observation — `status=proven`, `httpStatus=200`,
  `deployedManifestStatus=200`, `hashStatus=matched`, `manifestContractStatus=matched`,
  `freshnessStatus=fresh`, `deployedDataHash == expectedDataHash == 40e37b07…`.
- `docs/deployment-manifest.json` `hostingEvidence.status` refreshed to `proven`
  from the proven probe, **without changing the dashboard payload or `dataHash`**
  (re-export over the unchanged `main` payload keeps `40e37b07…`).

## Honest boundary (why the dashboard claim is unchanged)

The **dashboard payload** `demoReadiness.publicHosting` stays `not_proven` by
design: a static dashboard artifact cannot self-claim its own live deployment
(`buildPublicDemoManifest` enforces this). The `proven` claim lives only in the
**observed manifest/probe evidence**, which is self-protecting:
`_validate_public_hosting_probe` accepts `proven` only when
`deployedDataHash == expectedDataHash` and the observation is fresh — so if a
future branch-local change outpaces the deploy, the probe falls back to
`configured_not_observed` automatically. The project remains `local_demo_only` /
`no_alpha_claim`.

## Requirements

### REQ-FPS-CR10-001
1. When the deployed `dataHash` matches the committed manifest `dataHash` and the
   live URL returns HTTP 200, the committed probe + manifest `hostingEvidence`
   record `status=proven` with matched hash/contract and fresh observation.
2. The dashboard payload `publicHosting` is unchanged (`not_proven`); `dataHash`
   is unchanged (`40e37b07…`).
3. A `proven` probe whose deployed hash does not match expected, or whose
   observation is stale, must not validate as `proven`.

## Gates

Full suite green: pytest **338**, mypy 60, lint-imports KEPT 77/198, Python
mutation 106/106, frontend 46. `test_public_hosting_manifest_carries_observed_proof`
now passes against the proven manifest/probe.
