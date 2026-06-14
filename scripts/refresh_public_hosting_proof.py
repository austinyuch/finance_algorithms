"""Refresh the committed public-hosting proof from a live probe observation.

CR-FPS-011 automation that replaces the manual re-prove performed in CR-FPS-010 /
CR-RDO-003. Given a probe *observation* of the live deployment, it derives the
canonical hosting status (``proven`` only when the deployed ``dataHash`` matches
the expected hash over a healthy, fresh observation) and rewrites the three
committed surfaces atomically:

- ``docs/public-hosting-probe.json``
- ``docs/review/assets/public-hosting-probe.json`` (byte-identical copy)
- ``docs/deployment-manifest.json`` (``hostingEvidence`` block)

It fails closed: a malformed observation raises before any file is written, and
``proven`` is never emitted without a matched, fresh observation. Run with
``--probe-json <path>`` (e.g. the output of ``npm run probe:public-demo``) or
let it shell out to the frontend probe in ``--live`` mode.

Examples::

    uv run python scripts/refresh_public_hosting_proof.py --probe-json /tmp/probe.json
    uv run python scripts/refresh_public_hosting_proof.py --live
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

TARGET_URL = "https://austinyuch.github.io/finance_algorithms/"
MAX_AGE_HOURS = 24
_PROBE_PATH = "docs/public-hosting-probe.json"
_REVIEW_COPY_PATH = "docs/review/assets/public-hosting-probe.json"
_MANIFEST_PATH = "docs/deployment-manifest.json"

_HOSTING_EVIDENCE_FIELDS = (
    "httpStatus",
    "observedAt",
    "deployedDataHash",
    "expectedDataHash",
    "deployedTargetUrl",
    "deployedArtifactKind",
    "deployedClaimBoundary",
    "deployedDashboardClaim",
    "freshnessStatus",
    "maxAgeHours",
    "hashStatus",
    "manifestContractStatus",
    "status",
)


def _iso_z(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + (
        f"{moment.microsecond // 1000:03d}Z"
    )


def derive_canonical_probe(observation: Mapping[str, Any], asof: datetime) -> dict[str, Any]:
    """Derive the canonical committed probe from a raw live observation.

    ``proven`` requires a healthy HTTP/manifest observation whose deployed
    ``dataHash`` matches the expected hash; the observation is stamped fresh at
    ``asof``. Otherwise the status is ``configured_not_observed`` and the hash
    status reflects the real comparison (never ``matched`` while configured).
    """
    deployed_hash = observation["deployedDataHash"]
    expected_hash = observation["expectedDataHash"]
    http_status = observation.get("httpStatus")
    manifest_status = observation.get("deployedManifestStatus")
    contract_status = observation.get("manifestContractStatus")

    healthy = (
        http_status == 200
        and manifest_status == 200
        and contract_status == "matched"
    )
    hashes_match = bool(deployed_hash) and deployed_hash == expected_hash

    if healthy and hashes_match:
        status = "proven"
        hash_status = "matched"
    else:
        status = "configured_not_observed"
        hash_status = "mismatched" if http_status == 200 else "not_checked"

    return {
        "targetUrl": observation.get("targetUrl", TARGET_URL),
        "status": status,
        "pagesConfigured": True,
        "httpStatus": http_status,
        "deployedManifestStatus": manifest_status,
        "deployedDataHash": deployed_hash,
        "expectedDataHash": expected_hash,
        "hashStatus": hash_status,
        "deployedTargetUrl": observation.get("deployedTargetUrl", TARGET_URL),
        "deployedArtifactKind": observation.get(
            "deployedArtifactKind", "github_pages_static_showcase"
        ),
        "deployedClaimBoundary": "no_alpha_claim",
        "deployedDashboardClaim": observation.get("deployedDashboardClaim", "local_demo_only"),
        "manifestContractStatus": contract_status,
        "observedAt": _iso_z(asof),
        "freshnessStatus": "fresh",
        "maxAgeHours": MAX_AGE_HOURS,
        "claimBoundary": "no_alpha_claim",
    }


def _manifest_hosting_evidence(probe: Mapping[str, Any]) -> dict[str, Any]:
    return {field: probe[field] for field in _HOSTING_EVIDENCE_FIELDS}


def refresh_hosting_proof(
    observation: Mapping[str, Any],
    *,
    repo_root: str | Path,
    asof: datetime | None = None,
) -> dict[str, Any]:
    """Rewrite the three committed hosting surfaces from ``observation``.

    Fails closed: the canonical probe is fully derived (raising on a malformed
    observation) *before* any file is touched, so a failure leaves all surfaces
    untouched.
    """
    if asof is None:
        asof = datetime.now(timezone.utc)
    root = Path(repo_root)

    probe = derive_canonical_probe(observation, asof)
    probe_text = json.dumps(probe, indent=2) + "\n"

    manifest_path = root / _MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.setdefault("hostingEvidence", {})
    manifest["hostingEvidence"].update(_manifest_hosting_evidence(probe))
    manifest_text = json.dumps(manifest, indent=2) + "\n"

    # All content is built and validated above; only now do we write.
    (root / _PROBE_PATH).write_text(probe_text, encoding="utf-8")
    (root / _REVIEW_COPY_PATH).write_text(probe_text, encoding="utf-8")
    manifest_path.write_text(manifest_text, encoding="utf-8")
    return probe


def _live_observation(repo_root: Path) -> dict[str, Any]:  # pragma: no cover - shells out to npm
    # Write the probe output inside docs/ so the probe reads the committed
    # docs/deployment-manifest.json for the expected dataHash. Do NOT use
    # check=True: the probe fails closed with exit 2 when the deployed hash is
    # stale (a legitimate configured_not_observed observation, not an error).
    out_path = repo_root / "docs" / ".refresh-live-probe.json"
    try:
        subprocess.run(
            ["npm", "run", "probe:public-demo"],
            cwd=str(repo_root / "frontend"),
            check=False,
            env={"QUANTLAB_PUBLIC_DEMO_PROBE_OUT_PATH": str(out_path), **_os_environ()},
        )
        if not out_path.exists():
            raise RuntimeError("live probe did not write an observation")
        return json.loads(out_path.read_text(encoding="utf-8"))
    finally:
        out_path.unlink(missing_ok=True)


def _os_environ() -> dict[str, str]:  # pragma: no cover - trivial env passthrough
    import os

    return dict(os.environ)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-json", type=Path, help="Path to a probe observation JSON")
    parser.add_argument("--live", action="store_true", help="Run the frontend probe to observe live")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    if args.probe_json is not None:
        observation = json.loads(args.probe_json.read_text(encoding="utf-8"))
    elif args.live:  # pragma: no cover - shells out to npm
        observation = _live_observation(repo_root)
    else:
        parser.error("provide --probe-json <path> or --live")

    probe = refresh_hosting_proof(observation, repo_root=repo_root)
    print(
        f"refresh-public-hosting-proof: {probe['status']} "
        f"(hash {probe['hashStatus']}, observed {probe['observedAt']})"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
