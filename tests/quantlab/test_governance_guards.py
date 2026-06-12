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


def _top_level_test_count(path: Path) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return sum(
        1
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    )


def test_contract_interfaces_no_drift():
    """spec contract SSOT 與 quantlab 實作版的 Protocol 結構不得漂移。"""
    spec = _protocol_surface(ROOT / ".agents/specs/a0-backtest-foundation/contract/interfaces.py")
    impl = _protocol_surface(ROOT / "quantlab/contracts/interfaces.py")
    assert spec, "spec SSOT interfaces.py 應含 Protocol"
    assert spec == impl, f"contract 漂移:\nSSOT={spec}\nIMPL={impl}"


def test_quantlab_test_registry_governance_rows_match_current_test_inventory():
    """Governance-heavy row counts must track the current test inventory."""
    registry = (ROOT / "quantlab/TESTS.md").read_text(encoding="utf-8")
    governed_rows = {
        "test_governance_guards": ROOT / "tests/quantlab/test_governance_guards.py",
        "test_mutation_spot_checks": ROOT / "tests/test_mutation_spot_checks.py",
    }

    for row_id, path in governed_rows.items():
        expected = _top_level_test_count(path)
        assert f"| `{row_id}` |" in registry
        pattern = re.compile(rf"\| `{re.escape(row_id)}` \|[^\n]+\| (?P<count>\d+) pass \|")
        match = pattern.search(registry)
        assert match, f"missing pass-count evidence for {row_id}"
        assert int(match.group("count")) == expected, (
            f"quantlab/TESTS.md row {row_id} reports {match.group('count')} pass, "
            f"but {path.relative_to(ROOT)} currently has {expected} tests"
        )


def test_current_governance_surfaces_do_not_publish_stale_gate_counts():
    """Current governance surfaces must not advertise superseded readiness evidence."""
    current_surfaces = [
        ROOT / ".agents/specs/SPECS.md",
        ROOT / ".agents/specs/NEXT_STEPS.md",
        ROOT / ".agents/specs/RTM.md",
        ROOT / ".agents/specs/TESTS.md",
        ROOT / ".agents/specs/ISSUE_LOG.md",
        ROOT / ".agents/specs/a0-backtest-foundation/review.md",
        ROOT / ".agents/specs/a-tsmc-hedge-slice/design.md",
        ROOT / ".agents/specs/a-tsmc-hedge-slice/review.md",
        ROOT / "quantlab/CORRECTNESS_CHECKLIST.md",
        ROOT / "quantlab/TESTS.md",
        ROOT / "docs/FEATURES.md",
        ROOT / "docs/manual/en/index.md",
        ROOT / "docs/manual/en/index.html",
        ROOT / "docs/manual/zh-tw/index.md",
        ROOT / "docs/manual/zh-tw/index.html",
        ROOT / "docs/review/index.html",
        ROOT / "docs/MANUAL_GENERATION_GUIDE.md",
        ROOT / "docs/REVIEW_GENERATION_GUIDE.md",
        ROOT / "docs/review/assets/gate-pytest.txt",
        ROOT / "docs/review/assets/gate-frontend-test.txt",
        ROOT / "docs/review/assets/gate-frontend-audit.txt",
        ROOT / ".agents/specs/f-browser-pixel-baseline/review.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/reports/implementation-report.md",
        ROOT / ".agents/specs/f-demo-hardening/review.md",
        ROOT / ".agents/specs/f-demo-hardening/reports/implementation-report.md",
    ]
    stale_markers = [
        "190 pytest",
        "20 frontend",
        "22 mutation",
        "66 passed",
        "156 passed",
        "243 passed",
        "244 passed",
        "245 passed",
        "246 passed",
        "246 suite evidence",
        "247 passed",
        "247 suite evidence",
        "248 passed",
        "included in 245 passed",
        "242 passed",
        "241 passed",
        "231 passed",
        "238 passed",
        "237 passed",
        "240 passed",
        "239 passed",
        "23 frontend tests",
        "27 frontend tests",
        "27 tests pass",
        "found 1 vulnerability",
        "1 vulnerability",
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
        "50/50 configured",
        "50/50 Python mutation",
        "Python mutation 50/50",
        "mutation spot checks 50/50",
        "mutation spot-checks are **50/50",
        "51/51 configured",
        "51/51 Python mutation",
        "Python mutation 51/51",
        "mutation spot checks 51/51",
        "mutation spot-checks are **51/51",
        "52/52 configured",
        "52/52 Python mutation",
        "Python mutation 52/52",
        "mutation spot checks 52/52",
        "mutation spot-checks are **52/52",
        "53/53 configured",
        "53/53 Python mutation",
        "Python mutation 53/53",
        "mutation spot checks 53/53",
        "mutation spot-checks are **53/53",
        "57/57 configured",
        "57/57 Python mutation",
        "Python mutation 57/57",
        "mutation spot checks 57/57",
        "mutation spot-checks are **57/57",
        "61/61 configured",
        "61/61 Python mutation",
        "Python mutation 61/61",
        "mutation spot checks 61/61",
        "mutation spot-checks are **61/61",
        "62/62 configured",
        "62/62 Python mutation",
        "Python mutation 62/62",
        "mutation spot checks 62/62",
        "mutation spot-checks are **62/62",
        "63/63 configured",
        "63/63 Python mutation",
        "Python mutation 63/63",
        "mutation spot checks 63/63",
        "mutation spot-checks are **63/63",
        "64/64 configured",
        "64/64 Python mutation",
        "Python mutation 64/64",
        "mutation spot checks 64/64",
        "mutation spot-checks are **64/64",
        "65/65 configured",
        "65/65 Python mutation",
        "Python mutation 65/65",
        "mutation spot checks 65/65",
        "mutation spot-checks are **65/65",
        "66/66 configured",
        "66/66 Python mutation",
        "Python mutation 66/66",
        "mutation spot checks 66/66",
        "mutation spot-checks are **66/66",
            "67/67 configured",
            "67/67 Python mutation",
            "Python mutation 67/67",
            "mutation spot checks 67/67",
            "mutation spot-checks are **67/67",
            "68/68 configured",
            "68/68 Python mutation",
            "Python mutation 68/68",
            "mutation spot checks 68/68",
            "mutation spot-checks are **68/68",
            "6/6 configured",
        "kills 6/6 configured mutations",
        "mutation spot-check 5/5",
        "41/41 Python mutation",
        "236 passed",
        "included in 236 passed",
        "clean over 55 files",
        "55 source files",
        "73 files, 177 deps",
        "3/3 configured mutations",
        "3/3 configured/killed",
        "import-linter 正式化列為待辦",
        "import-linter 待正式化",
        "(residual PR#3)",
        "drift-guard 測試列為待辦",
        "74 files / 185 dependencies",
        "74 files, 185 dependencies",
        "74 files / 185 deps",
        "74 files, 185 deps",
        "91.81% line coverage",
        "91.42% line coverage",
        "84.37% line coverage",
        "mutation 8/8 killed",
        "8/8 killed",
        "12 frontend mutations",
        "mutation 12/12 killed",
        "frontend mutation 12/12",
        "28 frontend tests",
        "28 tests pass",
        "23 tests passed",
        "13 frontend mutations",
        "mutation 13/13 killed",
        "frontend mutation 13/13",
        "29 frontend tests",
        "frontend 29",
        "29 tests pass",
        "14 frontend mutations",
        "mutation 14/14 killed",
        "frontend mutation 14/14",
        "91.07% line coverage",
        "F Next.js coverage 91.07%",
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
        "976 / 1,296,000",
        "976/1,296,000",
        "0.0007530864197530864",
        "1dfe0f883def3a9e62a2579cadf5dfb2e3484976d5c57ca48db1e3e05a123615",
        "c50441599f2d9962eaa0037afa73fbbd54a0863f845b6cd7664abf45f7ec279f",
        "aee424d0dbe186047e9c322ffdf0ad1ab533d927ed14c28b3003714a16fe687c",
        "957 / 1,296,000",
        "957/1,296,000",
        "0.0007384259259259259",
        "132387264370da6f7be62d80a48083cbabde04108bff37d585ac065bfc30a3b7",
        "c660658743856add81851bd3d822133bfec2aabbf84a1ab2c0ecd62d8754b4cc",
        "e5d0eb89f0ca0a54b4668c5fd6c7d5b3cf0f64ee5c74a67c8479267e404ba9d5",
        "38474295d540374507c2ba45b5c370054526a785bef2c1e7c731caa8b31654f4",
        "b882f8668327a705364f60d55787e66b85fd59a01e933369868cbb07eee3bb3f",
        "7ecee9da57399c11ddc531c82438b3143897df3e05f75eafd7b708aba6dff5a8",
        "45f35838a658b63377f34ea58c514e6889d89c808794c4d2f0bbc746c0505c89",
        "75cee9526ae96f63cb9ff95901cf1931a5a34a4f3bbcb89c1af33946ba617b0a",
        "966 / 1,296,000",
        "966/1,296,000",
        "1051 / 1,296,000",
        "1051/1,296,000",
        "0.0008109567901234568",
        "1041 / 1,296,000",
        "1041/1,296,000",
        "1049/1296000",
        "0.0008032407407407408",
        "be7d0618d726253c38af6eb3ab005372848f715f7872efe0fbb63f36a48b9d02",
        "9c2e5fe8651694969deafe256918c113c9f189823102da3554840bfe644bc4f3",
        "1036 / 1,296,000",
        "1036/1,296,000",
        "0.0007993827160493827",
        "c1c0cb85d2d9f1ac2df037399b856845705bc225998af0b73a64f65715875037",
        "901f8b3c89a8ace220c667ff88771884fdd26b04da599889cd225f9a4d947ab7",
        "1055 / 1,296,000",
        "1055/1,296,000",
        "0.0008140432098765432",
        "7a3494c6f713743b76a5b5c25d1e3b3cb4fa5e3a9c0defa8b4581f460eba5b6e",
        "1057 / 1,296,000",
        "1057/1,296,000",
        "0.0008155864197530864",
        "6b8ecfa0d7ab74ca50cb773de4021f7a1b164224e6b77a463708134cbcaffaba",
        "1063 / 1,296,000",
        "1063/1,296,000",
        "0.000820216049382716",
        "472dfef3cbd34ae9d09979a333366bc1054cd9f2379a3869e04aae8cede47cad",
        "3e94cdbe790007dfe7f8a58d4aa45ebc39fd709f88152d351b089339761d71b1",
        "700134c3e1504b866e395f4e7c1465d7a1e094eade4a71960890b1b89c90922c",
        "0c05cc97a692623ce1226ff0a15332063c8265ea3bdf78b27596d51ac604c7c4",
        "47be766e853053e34fb2fe331caf8f337090bee5b6315fc057bc5c7350e1d423",
        "refreshed to 236",
        "8e7b66b604482811081cf199063bf0bd89e4071a751d12c2bbac65fb0eaf2a88",
        "8acc4d0a14aeca1cc95edfcb402dcd72a41f035b5e367e497634839301fb7c29",
        "221 / 1,296,000",
        "221/1,296,000",
        "0 / 1,296,000",
        "0/1,296,000",
    ]

    for path in current_surfaces:
        text = path.read_text(encoding="utf-8")
        for marker in stale_markers:
            assert marker not in text, f"{path.relative_to(ROOT)} still publishes stale marker: {marker}"


def test_f_public_static_showcase_crs_do_not_republish_superseded_fixture_boundary():
    """F public-static CR overlays must not describe the current payload as fixture-backed."""
    cr_surfaces = sorted(
        (ROOT / ".agents/specs/f-public-static-showcase/change-requests").glob("cr-fps-*.md")
    )
    assert cr_surfaces
    stale_markers = [
        "The dashboard remains fixture-backed",
        "The dashboard payload remains fixture-backed",
        "fixture-backed local demo evidence",
        "`local_demo_only` / fixture-backed boundary",
        "Refreshed `frontend/lib/showcase-fixture.ts` evidence strings",
    ]

    for path in cr_surfaces:
        text = path.read_text(encoding="utf-8")
        for marker in stale_markers:
            assert marker not in text, (
                f"{path.relative_to(ROOT)} republishes superseded F fixture boundary: {marker}"
            )


def test_current_review_gate_transcripts_match_published_evidence():
    """Review gate transcripts and generation guides must match current evidence counts."""
    review_html = (ROOT / "docs/review/index.html").read_text(encoding="utf-8")
    manual_guide = (ROOT / "docs/MANUAL_GENERATION_GUIDE.md").read_text(encoding="utf-8")
    review_guide = (ROOT / "docs/REVIEW_GENERATION_GUIDE.md").read_text(encoding="utf-8")
    pytest_gate = (ROOT / "docs/review/assets/gate-pytest.txt").read_text(encoding="utf-8")
    frontend_gate = (ROOT / "docs/review/assets/gate-frontend-test.txt").read_text(encoding="utf-8")
    mypy_gate = (ROOT / "docs/review/assets/gate-mypy.txt").read_text(encoding="utf-8")
    lint_gate = (ROOT / "docs/review/assets/gate-lint-imports.txt").read_text(encoding="utf-8")
    audit_text = (ROOT / "docs/review/assets/gate-frontend-audit.txt").read_text(encoding="utf-8")
    audit_gate = json.loads((ROOT / "docs/review/assets/gate-frontend-audit.json").read_text(encoding="utf-8"))

    assert "251 passed" in pytest_gate
    assert "251 passed" in manual_guide
    assert "251 passed" in review_guide
    assert "Python suite now <b>251 passed</b>" in review_html
    assert "Tests  32 passed (32)" in frontend_gate
    assert "Frontend <b>32 tests pass</b>" in review_html
    assert "27 tests pass" not in review_html
    assert "28 tests pass" not in review_html
    assert "29 tests pass" not in review_html
    assert "Success: no issues found in 57 source files" in mypy_gate
    assert "Analyzed 75 files, 186 dependencies." in lint_gate
    assert audit_text.strip() == "found 0 vulnerabilities"
    assert audit_gate["metadata"]["vulnerabilities"]["total"] == 0


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
    assert browser_diff["mismatchedPixels"] == 1007
    assert browser_diff["maxMismatchRatio"] == 0.001


def test_current_stakeholder_payload_assets_are_synchronized():
    """Copied stakeholder and app payload assets must not drift from committed docs artifacts."""
    showcase = json.loads((ROOT / "docs/showcase.json").read_text(encoding="utf-8"))
    frontend_showcase = json.loads((ROOT / "frontend/lib/showcase-payload.json").read_text(encoding="utf-8"))
    manual_showcase = json.loads((ROOT / "docs/manual/assets/showcase.json").read_text(encoding="utf-8"))
    review_showcase = json.loads((ROOT / "docs/review/assets/showcase.json").read_text(encoding="utf-8"))
    public_probe = json.loads((ROOT / "docs/public-hosting-probe.json").read_text(encoding="utf-8"))
    review_public_probe = json.loads(
        (ROOT / "docs/review/assets/public-hosting-probe.json").read_text(encoding="utf-8")
    )
    browser_diff = json.loads((ROOT / "docs/browser-visual-diff.json").read_text(encoding="utf-8"))
    visual_evidence = (
        f"browser visual diff {browser_diff['mismatchedPixels']}/{browser_diff['totalPixels']} passed"
    )

    assert frontend_showcase == showcase
    assert manual_showcase == showcase
    assert review_showcase == showcase
    assert review_public_probe == public_probe
    assert visual_evidence in showcase["evidence"]["tests"]
    assert (ROOT / "docs/manual/assets/dashboard-static-export.html").read_text(encoding="utf-8") == (
        ROOT / "docs/index.html"
    ).read_text(encoding="utf-8")
    assert visual_evidence in (ROOT / "docs/index.html").read_text(encoding="utf-8")


def test_traceability_visual_evidence_tracks_current_pixel_diff():
    """Governance bridge docs must not publish stale browser visual mismatch counts."""
    browser_diff = json.loads((ROOT / "docs/browser-visual-diff.json").read_text(encoding="utf-8"))
    spaced = f"{browser_diff['mismatchedPixels']} / {browser_diff['totalPixels']:,}"
    compact = f"{browser_diff['mismatchedPixels']} / 1,296,000"
    current_surfaces = [
        ROOT / ".agents/specs/RTM.md",
        ROOT / "docs/DEMO_RISK_WARNING_TAXONOMY.md",
    ]

    assert browser_diff["mismatchedPixels"] == 1007
    for path in current_surfaces:
        text = path.read_text(encoding="utf-8")
        assert spaced in text or compact in text
        assert "1089 / 1,296,000" not in text
        assert "1089/1296000" not in text


def test_current_dashboard_source_wording_tracks_canonical_payload():
    """Current F/governance handoff surfaces must not point at the retired inline fixture."""
    current_source_surfaces = [
        ROOT / ".agents/specs/NEXT_STEPS.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/design.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/review.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/reports/implementation-report.md",
        ROOT / ".agents/specs/f-demo-hardening/design.md",
        ROOT / ".agents/specs/f-demo-hardening/reports/implementation-report.md",
        ROOT / ".agents/specs/governance-evidence-refresh/design.md",
        ROOT / ".agents/specs/governance-evidence-refresh/tasks.md",
        ROOT / ".agents/specs/governance-evidence-refresh/review.md",
    ]
    stale_source_markers = [
        "frontend/lib/showcase-fixture.ts",
        "Fixture[showcase fixture]",
        "contract/fixture updates",
        "fixture/API/component render tests",
        "dashboard still uses fixture-backed showcase data",
        "Still fixture-backed",
        "fixture-driven/read-only",
        "Static showcase fixture evidence",
        "Dashboard data remains fixture-driven",
        "static dashboard remains fixture-driven",
        "static showcase fixture evidence",
    ]

    for path in current_source_surfaces:
        text = path.read_text(encoding="utf-8")
        assert "local_result_store" in text or "local result-store" in text
        for marker in stale_source_markers:
            assert marker not in text, f"{path.relative_to(ROOT)} still publishes stale source marker: {marker}"


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
    assert hosting.get("freshnessStatus") == "fresh"
    assert hosting.get("maxAgeHours") == 24
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
    assert probe.get("freshnessStatus") == hosting.get("freshnessStatus")
    assert probe.get("freshnessStatus") == "fresh"
    assert probe.get("maxAgeHours") == hosting.get("maxAgeHours")
    assert probe.get("maxAgeHours") == 24
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

    assert "CR-FPS-001 + CR-FPS-002 + CR-FPS-003 + CR-FPS-007 + CR-FPS-008" in text
    assert "standalone probe parity" in text
    assert "freshness" in text
    assert "docs/deployment-manifest.json" in text
    assert "docs/public-hosting-probe.json" in text
    assert "frontend/out/public-hosting-probe.json" not in text
