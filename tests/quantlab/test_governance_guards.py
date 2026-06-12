"""治理 guard 測試(關閉 A0 residual)。

1. import-linter:正式化框架隔離(engine/data 禁 torch/tf/jax),取代/補強 AST 測試。
2. contract drift-guard:spec SSOT 的 interfaces.py 與 quantlab 實作版 Protocol 結構須一致。
"""
from __future__ import annotations

import ast
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
        ROOT / ".agents/specs/NEXT_STEPS.md",
        ROOT / ".agents/specs/ISSUE_LOG.md",
        ROOT / "quantlab/CORRECTNESS_CHECKLIST.md",
    ]
    stale_markers = [
        "190 pytest",
        "20 frontend",
        "22 mutation",
        "66 passed",
        "mutation spot-check 5/5",
    ]

    for path in current_surfaces:
        text = path.read_text(encoding="utf-8")
        for marker in stale_markers:
            assert marker not in text, f"{path.relative_to(ROOT)} still publishes stale marker: {marker}"


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
    assert "PR #29" in text
    assert "PR #30" in text
    assert "schedule_run_count=0" not in text
    assert "27392471359" in text
    assert "schedule_run_count=1" in text


def test_next_steps_reflects_post_merge_governance_sync_state():
    """NEXT_STEPS should advance after the post-merge governance sync has landed."""
    text = (ROOT / ".agents/specs/NEXT_STEPS.md").read_text(encoding="utf-8")

    assert "Open/promote `spec/post-merge-scheduled-observer-sync`" not in text
    assert "PR #31" in text
    assert "PR #32" in text
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
    assert "PR #35" in text
    assert "PR #36" in text
    assert "PR #39" in text
    assert "PR #40" in text
    assert "PR #44" in text
    assert "PR #45" in text
    assert "PR #48" in text
    assert "PR #49" in text
    assert "PR #55" in text
    assert "PR #56" in text
    assert "not_ready" in text


def test_next_steps_reflects_post_merge_live_write_smoke_state():
    """NEXT_STEPS should reflect CR-B12 after both dev and main promotions."""
    text = (ROOT / ".agents/specs/NEXT_STEPS.md").read_text(encoding="utf-8")

    assert "Current branch lane:** none after `e-tier3-readiness-proof-cli` promotion" not in text
    assert "Current branch lane:** none after CR-B12 promotion" not in text
    assert "Current branch lane:** none after CR-B13 promotion" not in text
    assert "Current branch lane:** none after CR-B14 promotion" not in text
    assert "Current branch lane:** none." in text
    assert "PR #61" in text
    assert "PR #62" in text
    assert "PR #61 squash-merged CR-B12 scoped live write smoke to `dev` as `0f3af09`" in text
    assert "PR #62 squash-merged CR-B12 scoped live write smoke to `main` as `4f2f58a`" in text


def test_next_steps_reflects_post_merge_cr_b13_state():
    """NEXT_STEPS should retain CR-B13 promotion proof without making it current."""
    text = (ROOT / ".agents/specs/NEXT_STEPS.md").read_text(encoding="utf-8")

    assert "CR-B13 post live-write governance sync is implemented locally" not in text
    assert "Current branch lane:** none after CR-B13 promotion" not in text
    assert "PR #63 squash-merged CR-B13 post live-write governance sync to `dev` as `8c5b3f1`" in text
    assert "PR #64 squash-merged CR-B13 post live-write governance sync to `main` as `aea683f`" in text
    assert "8c5b3f1" in text
    assert "aea683f" in text


def test_next_steps_reflects_post_merge_cr_b14_state():
    """NEXT_STEPS should retain CR-B14 proof without a self-staling current lane."""
    text = (ROOT / ".agents/specs/NEXT_STEPS.md").read_text(encoding="utf-8")

    assert "CR-B14 post CR-B13 governance sync is implemented locally" not in text
    assert "Current branch lane:** none after CR-B14 promotion" not in text
    assert "Current branch lane:** none." in text
    assert "PR #65 squash-merged CR-B14 post CR-B13 governance sync to `dev` as `05485cc`" in text
    assert "PR #66 squash-merged CR-B14 post CR-B13 governance sync to `main` as `c1e1591`" in text
    assert "05485cc" in text
    assert "c1e1591" in text
