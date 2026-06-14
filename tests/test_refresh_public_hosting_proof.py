"""CR-FPS-011: refresh automation for the committed public-hosting proof.

The refresher takes a live probe *observation* and rewrites the three committed
surfaces (standalone probe, its review copy, and the deployment manifest's
hostingEvidence). It derives ``proven`` only from a matched + fresh observation
and fails closed (no partial write) on a malformed observation.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from scripts.refresh_public_hosting_proof import refresh_hosting_proof

_ASOF = datetime(2026, 6, 14, 3, 0, 0, tzinfo=timezone.utc)
_TARGET = "https://austinyuch.github.io/finance_algorithms/"

_MATCHED = {
    "targetUrl": _TARGET,
    "httpStatus": 200,
    "deployedManifestStatus": 200,
    "manifestContractStatus": "matched",
    "deployedDataHash": "abc123",
    "expectedDataHash": "abc123",
    "deployedTargetUrl": _TARGET,
    "deployedArtifactKind": "github_pages_static_showcase",
    "deployedClaimBoundary": "no_alpha_claim",
    "deployedDashboardClaim": "local_demo_only",
}


def _seed_repo(root: Path) -> None:
    (root / "docs/review/assets").mkdir(parents=True)
    (root / "docs/public-hosting-probe.json").write_text("SENTINEL", encoding="utf-8")
    (root / "docs/review/assets/public-hosting-probe.json").write_text("SENTINEL", encoding="utf-8")
    (root / "docs/deployment-manifest.json").write_text(
        json.dumps({"dataHash": "abc123", "hostingEvidence": {"status": "old"}}),
        encoding="utf-8",
    )


def _read(root: Path, rel: str) -> dict:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def test_refresh_writes_proven_on_matched_fresh_observation(tmp_path):
    _seed_repo(tmp_path)
    probe = refresh_hosting_proof(_MATCHED, repo_root=tmp_path, asof=_ASOF)

    assert probe["status"] == "proven"
    assert probe["hashStatus"] == "matched"
    assert probe["freshnessStatus"] == "fresh"
    assert probe["observedAt"] == "2026-06-14T03:00:00.000Z"
    assert probe["claimBoundary"] == "no_alpha_claim"

    committed = _read(tmp_path, "docs/public-hosting-probe.json")
    review_copy = _read(tmp_path, "docs/review/assets/public-hosting-probe.json")
    assert committed == probe
    # Byte-identical copy.
    assert (tmp_path / "docs/public-hosting-probe.json").read_text(encoding="utf-8") == (
        tmp_path / "docs/review/assets/public-hosting-probe.json"
    ).read_text(encoding="utf-8")
    assert review_copy == probe

    manifest = _read(tmp_path, "docs/deployment-manifest.json")
    assert manifest["hostingEvidence"]["status"] == "proven"
    assert manifest["hostingEvidence"]["hashStatus"] == "matched"


def test_refresh_downgrades_to_configured_on_hash_mismatch(tmp_path):
    _seed_repo(tmp_path)
    observation = dict(_MATCHED, deployedDataHash="stale-deploy")
    probe = refresh_hosting_proof(observation, repo_root=tmp_path, asof=_ASOF)

    assert probe["status"] == "configured_not_observed"
    assert probe["hashStatus"] == "mismatched"
    manifest = _read(tmp_path, "docs/deployment-manifest.json")
    assert manifest["hostingEvidence"]["status"] == "configured_not_observed"


def test_refresh_fails_closed_without_partial_write(tmp_path):
    _seed_repo(tmp_path)
    bad = dict(_MATCHED)
    del bad["expectedDataHash"]
    with pytest.raises((ValueError, KeyError)):
        refresh_hosting_proof(bad, repo_root=tmp_path, asof=_ASOF)
    # No surface was mutated.
    assert (tmp_path / "docs/public-hosting-probe.json").read_text(encoding="utf-8") == "SENTINEL"
    assert (tmp_path / "docs/review/assets/public-hosting-probe.json").read_text(encoding="utf-8") == "SENTINEL"
    assert _read(tmp_path, "docs/deployment-manifest.json")["hostingEvidence"]["status"] == "old"


def test_refresh_proven_probe_passes_scenario_validation(tmp_path):
    """The proof the refresher emits must satisfy the consumer's validator."""
    from quantlab.showcase.scenario import _validate_public_hosting_probe

    _seed_repo(tmp_path)
    probe = refresh_hosting_proof(_MATCHED, repo_root=tmp_path, asof=_ASOF)
    assert _validate_public_hosting_probe(probe, asof=_ASOF) == "fresh"


def test_cli_refresh_from_probe_json(tmp_path):
    from scripts.refresh_public_hosting_proof import main

    _seed_repo(tmp_path)
    probe_input = tmp_path / "observation.json"
    probe_input.write_text(json.dumps(_MATCHED), encoding="utf-8")

    exit_code = main(
        ["--probe-json", str(probe_input), "--repo-root", str(tmp_path)]
    )
    assert exit_code == 0
    assert _read(tmp_path, "docs/public-hosting-probe.json")["status"] == "proven"


def test_cli_requires_a_source(tmp_path):
    from scripts.refresh_public_hosting_proof import main

    with pytest.raises(SystemExit):
        main(["--repo-root", str(tmp_path)])
