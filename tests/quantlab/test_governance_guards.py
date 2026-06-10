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
