"""治理 guard 測試(關閉 A0 residual)。

1. import-linter:正式化框架隔離(engine/data 禁 torch/tf/jax),取代/補強 AST 測試。
2. contract drift-guard:spec SSOT 的 interfaces.py 與 quantlab 實作版 Protocol 結構須一致。
"""
from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_import_linter_contract_kept():
    """engine/data 框架隔離契約須 KEPT(import-linter)。"""
    exe = shutil.which("lint-imports") or "lint-imports"
    proc = subprocess.run([exe], cwd=ROOT, capture_output=True, text=True)
    assert "Contracts:" in proc.stdout, f"lint-imports 未實際執行:\n{proc.stdout}\n{proc.stderr}"
    assert proc.returncode == 0, f"import-linter 契約被破壞:\n{proc.stdout}\n{proc.stderr}"


def _protocol_surface(path: Path) -> dict:
    """{ClassName: [sorted method names]},供結構比對(忽略註解/docstring/header)。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            out[node.name] = sorted(
                n.name for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
    return out


def test_contract_interfaces_no_drift():
    """spec contract SSOT 與 quantlab 實作版的 Protocol 結構不得漂移。"""
    spec = _protocol_surface(ROOT / ".agents/specs/a0-backtest-foundation/contract/interfaces.py")
    impl = _protocol_surface(ROOT / "quantlab/contracts/interfaces.py")
    assert spec, "spec SSOT interfaces.py 應含 Protocol"
    assert spec == impl, f"contract 漂移:\nSSOT={spec}\nIMPL={impl}"


def test_current_governance_surfaces_do_not_publish_stale_gate_counts():
    """Current governance surfaces must not advertise superseded readiness evidence."""
    current_surfaces = [
        ROOT / ".agents/specs/SPECS.md",
        ROOT / ".agents/specs/NEXT_STEPS.md",
        ROOT / ".agents/specs/RTM.md",
        ROOT / ".agents/specs/TESTS.md",
        ROOT / ".agents/specs/ISSUE_LOG.md",
        ROOT / "quantlab/CORRECTNESS_CHECKLIST.md",
        ROOT / "quantlab/TESTS.md",
        ROOT / "docs/FEATURES.md",
        ROOT / "docs/manual/en/index.md",
        ROOT / "docs/manual/en/index.html",
        ROOT / "docs/manual/zh-tw/index.md",
        ROOT / "docs/manual/zh-tw/index.html",
        ROOT / "docs/review/index.html",
    ]
    stale_markers = [
        "190 pytest",
        "20 frontend",
        "22 mutation",
        "66 passed",
        "231 passed",
        "238 passed",
        "237 passed",
        "239 passed",
        "23 frontend tests",
        "27 frontend tests",
        "46/46 configured",
        "46/46 Python mutation",
        "Python mutation 46/46",
        "mutation spot checks 46/46",
        "mutation spot-checks are **46/46",
        "47/47 configured",
        "47/47 Python mutation",
        "Python mutation 47/47",
        "mutation spot checks 47/47",
        "mutation spot-checks are **47/47",
        "48/48 configured",
        "48/48 Python mutation",
        "Python mutation 48/48",
        "mutation spot checks 48/48",
        "mutation spot-checks are **48/48",
        "49/49 configured",
        "49/49 Python mutation",
        "Python mutation 49/49",
        "mutation spot checks 49/49",
        "mutation spot-checks are **49/49",
        "mutation spot-check 5/5",
        "41/41 Python mutation",
        "236 passed",
        "included in 236 passed",
        "clean over 55 files",
        "55 source files",
        "73 files, 177 deps",
        "91.81% line coverage",
        "12 frontend mutations",
        "mutation 12/12 killed",
        "frontend mutation 12/12",
        "221 / 1,296,000",
        "221/1,296,000",
        "latest 221",
        "1019 / 1,296,000",
        "1019/1,296,000",
        "0.0007862654320987655",
        "2bbe4348ca8c005bd6db5b472e7fa1c468fba1249c3288fe2319d1656131f493",
        "1022 / 1,296,000",
        "1022/1,296,000",
        "0.0007885802469135803",
        "38f9d1e6cc5d7a3dc9e395db41ee5dc5c2464e618062cf305f1f473db49d333e",
        "1028 / 1,296,000",
        "1028/1,296,000",
        "0.0007932098765432099",
        "51c691630c253843f92d748330814b4b0b0834939f1d7140a8bbb47a8dc96d03",
        "4dd46e2c4cb2ceafc868888c9f28c969a71db408c1c2fa8aa87cd1aaecc92074",
        "1030 / 1,296,000",
        "1030/1,296,000",
        "0.0007947530864197531",
        "0898127d2d7192df7344c34736a89ce5623a7ca362923e2dcc7a6bc91e10fff9",
        "bd09929c62f6874ac9753154272ae2ae27d51522d997e85a85ec190f1718b633",
        "refreshed to 236",
        "8e7b66b604482811081cf199063bf0bd89e4071a751d12c2bbac65fb0eaf2a88",
    ]

    for path in current_surfaces:
        text = path.read_text(encoding="utf-8")
        for marker in stale_markers:
            assert marker not in text, f"{path.relative_to(ROOT)} still publishes stale marker: {marker}"


def test_current_visual_evidence_assets_are_synchronized():
    """Stakeholder review/manual assets must match the current browser visual evidence."""
    browser_visual = json.loads((ROOT / "docs/browser-visual.json").read_text(encoding="utf-8"))
    review_browser_visual = json.loads(
        (ROOT / "docs/review/assets/browser-visual.json").read_text(encoding="utf-8")
    )
    browser_diff = json.loads((ROOT / "docs/browser-visual-diff.json").read_text(encoding="utf-8"))
    review_browser_diff = json.loads(
        (ROOT / "docs/review/assets/browser-visual-diff.json").read_text(encoding="utf-8")
    )

    assert review_browser_visual == browser_visual
    assert review_browser_diff == browser_diff
    assert (ROOT / "docs/manual/assets/dashboard-browser-visual.png").read_bytes() == (
        ROOT / "docs/browser-visual.png"
    ).read_bytes()
    assert (ROOT / "docs/review/assets/dashboard-browser-visual.png").read_bytes() == (
        ROOT / "docs/browser-visual.png"
    ).read_bytes()
    assert browser_visual["screenshotHash"] == browser_diff["currentHash"]
    assert browser_diff["mismatchedPixels"] == 976
    assert browser_diff["maxMismatchRatio"] == 0.001


def test_current_stakeholder_payload_assets_are_synchronized():
    """Copied stakeholder payload assets must not drift from committed docs artifacts."""
    showcase = json.loads((ROOT / "docs/showcase.json").read_text(encoding="utf-8"))
    manual_showcase = json.loads((ROOT / "docs/manual/assets/showcase.json").read_text(encoding="utf-8"))
    review_showcase = json.loads((ROOT / "docs/review/assets/showcase.json").read_text(encoding="utf-8"))
    public_probe = json.loads((ROOT / "docs/public-hosting-probe.json").read_text(encoding="utf-8"))
    review_public_probe = json.loads(
        (ROOT / "docs/review/assets/public-hosting-probe.json").read_text(encoding="utf-8")
    )

    assert manual_showcase == showcase
    assert review_showcase == showcase
    assert review_public_probe == public_probe
    assert (ROOT / "docs/manual/assets/dashboard-static-export.html").read_text(encoding="utf-8") == (
        ROOT / "docs/index.html"
    ).read_text(encoding="utf-8")


def test_next_steps_reflects_post_merge_torch_alert_state():
    """NEXT_STEPS should be a live resume memo, not a stale local-lane checklist."""
    text = (ROOT / ".agents/specs/NEXT_STEPS.md").read_text(encoding="utf-8")

    assert "Commit/push `spec/a-torch-default-dependency-isolation`" not in text
    assert "implemented locally" not in text
    assert "post-merge rescan pending" not in text
    assert "Dependabot alert #7 fixed" in text


def test_next_steps_reflects_post_merge_scheduled_observer_state():
    """NEXT_STEPS should not ask future agents to promote already-merged observer work."""
    text = (ROOT / ".agents/specs/NEXT_STEPS.md").read_text(encoding="utf-8")

    assert "Commit/push `spec/scheduled-run-observer`" not in text
    assert "promote it through `dev`/`main`" not in text
    assert "observer should keep status `pending`" not in text
    assert "schedule_run_count=0" not in text
    assert "27392471359" in text
    assert "schedule_run_count=1" in text


def test_next_steps_reflects_post_merge_governance_sync_state():
    """NEXT_STEPS should advance after the post-merge governance sync has landed."""
    text = (ROOT / ".agents/specs/NEXT_STEPS.md").read_text(encoding="utf-8")

    assert "Open/promote `spec/post-merge-scheduled-observer-sync`" not in text
    assert "E Tier3" in text
    assert "serving, retraining, and automated drift monitoring" in text


def test_next_steps_reflects_post_merge_e_gate_state():
    """NEXT_STEPS should not ask future agents to promote the already-merged E gate."""
    text = (ROOT / ".agents/specs/NEXT_STEPS.md").read_text(encoding="utf-8")

    assert "Commit/push `spec/e-tier3-readiness-gate`" not in text
    assert "open the usual squash PRs for `dev` and `main`" not in text
    assert "Current branch lane:** `spec/e-tier3-serving-evidence`" not in text
    assert "Current branch lane:** `spec/e-tier3-retraining-evidence`" not in text
    assert "Current branch lane:** `spec/e-tier3-production-evidence-gate`" not in text
    assert "Current branch lane:** `spec/e-tier3-readiness-proof-cli`" not in text
    assert "not_ready" in text


def test_next_steps_uses_non_self_staling_promotion_boundary():
    """NEXT_STEPS should not be an exhaustive squash-PR ledger."""
    text = (ROOT / ".agents/specs/NEXT_STEPS.md").read_text(encoding="utf-8")

    assert "Current branch lane:** none after `e-tier3-readiness-proof-cli` promotion" not in text
    assert "Current branch lane:** none after CR-B12 promotion" not in text
    assert "Current branch lane:** none after CR-B13 promotion" not in text
    assert "Current branch lane:** none after CR-B14 promotion" not in text
    assert "Current branch lane:** none after CR-B13 promotion" not in text
    assert "Current branch lane:** none after CR-B16 promotion" not in text
    assert "Current branch lane:** none after CR-B17 promotion" not in text
    assert "Current branch lane:** none after CR-FPS-001 promotion" not in text
    assert re.search(r"Current branch lane:\*\* (none\.|`spec/[^`]+`)", text)
    assert "CR-B12 scoped live write smoke is implemented locally" not in text
    assert "CR-B13 post live-write governance sync is implemented locally" not in text
    assert "CR-B14 post CR-B13 governance sync is implemented locally" not in text
    assert "CR-B15 post CR-B14 governance sync is implemented locally" not in text
    assert "CR-B16 post CR-B15 governance sync is implemented locally" not in text
    assert "CR-B17 governance sync is implemented locally" not in text
    assert "CR-FPS-001 hosting manifest proof sync is implemented locally" not in text
    assert "- **Merged:**" not in text
    assert "squash-merged" not in text
    assert "PR #75" not in text
    assert "PR #76" not in text
    assert "**Promotion proof boundary:**" in text
    assert "do not append every squash PR to this rolling memo" in text
    assert "GitHub PR state and spec-local reports" in text


def test_public_hosting_manifest_carries_observed_proof():
    """The committed public demo manifest must not overclaim hosting parity."""
    manifest = json.loads((ROOT / "docs/deployment-manifest.json").read_text(encoding="utf-8"))
    probe = json.loads((ROOT / "docs/public-hosting-probe.json").read_text(encoding="utf-8"))
    review_probe = json.loads(
        (ROOT / "docs/review/assets/public-hosting-probe.json").read_text(encoding="utf-8")
    )
    hosting = manifest.get("hostingEvidence") or {}

    assert review_probe == probe
    assert manifest.get("targetUrl") == "https://austinyuch.github.io/finance_algorithms/"
    assert manifest.get("claimBoundary") == "no_alpha_claim"
    assert probe.get("targetUrl") == manifest.get("targetUrl")
    assert probe.get("claimBoundary") == "no_alpha_claim"
    assert hosting.get("sourcePath") == "docs/"
    assert hosting.get("publishMode") == "github_pages_branch_source"
    assert hosting.get("httpStatus") == 200
    assert probe.get("httpStatus") == 200
    assert probe.get("deployedManifestStatus") == 200
    assert isinstance(hosting.get("observedAt"), str)
    assert hosting["observedAt"].endswith("Z")
    assert hosting.get("manifestContractStatus") == "matched"
    assert hosting.get("expectedDataHash") == manifest.get("dataHash")
    assert hosting.get("deployedTargetUrl") == manifest.get("targetUrl")
    assert hosting.get("deployedArtifactKind") == manifest.get("artifactKind")
    assert hosting.get("deployedClaimBoundary") == manifest.get("claimBoundary")
    assert hosting.get("deployedDashboardClaim") == manifest.get("dashboardClaim")
    assert probe.get("deployedTargetUrl") == manifest.get("targetUrl")
    assert probe.get("deployedArtifactKind") == manifest.get("artifactKind")
    assert probe.get("deployedClaimBoundary") == manifest.get("claimBoundary")
    assert probe.get("deployedDashboardClaim") == manifest.get("dashboardClaim")
    assert probe.get("expectedDataHash") == manifest.get("dataHash")
    assert probe.get("manifestContractStatus") == "matched"
    if hosting.get("deployedDataHash") == manifest.get("dataHash"):
        assert hosting.get("status") == "proven"
        assert hosting.get("hashStatus") == "matched"
        assert probe.get("status") == "proven"
        assert probe.get("hashStatus") == "matched"
        assert probe.get("deployedDataHash") == manifest.get("dataHash")
    else:
        assert hosting.get("status") == "configured_not_observed"
        assert hosting.get("hashStatus") == "mismatched"
        assert probe.get("status") == "configured_not_observed"
        assert probe.get("hashStatus") == "mismatched"
        assert probe.get("deployedDataHash") != manifest.get("dataHash")


def test_demo_risk_taxonomy_names_current_public_hosting_authority():
    """Stakeholder warning taxonomy must point at committed parity evidence."""
    text = (ROOT / "docs/DEMO_RISK_WARNING_TAXONOMY.md").read_text(encoding="utf-8")

    assert "CR-FPS-001 + CR-FPS-002 + CR-FPS-003 + CR-FPS-007" in text
    assert "standalone probe parity" in text
    assert "docs/deployment-manifest.json" in text
    assert "docs/public-hosting-probe.json" in text
    assert "frontend/out/public-hosting-probe.json" not in text
