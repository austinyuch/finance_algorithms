from __future__ import annotations

import sys

from scripts.capture_pytest_gate import capture_gate


def test_capture_pytest_gate_replaces_transcript_after_success(tmp_path):
    output = tmp_path / "gate-pytest.txt"
    output.write_text("old transcript\n283 passed in 1.00s\n", encoding="utf-8")

    code = capture_gate(
        [sys.executable, "-c", "print('new transcript')\nprint('284 passed in 2.00s')"],
        output,
        cwd=tmp_path,
    )

    assert code == 0
    assert output.read_text(encoding="utf-8") == "new transcript\n284 passed in 2.00s\n"


def test_capture_pytest_gate_preserves_transcript_after_failure(tmp_path):
    output = tmp_path / "gate-pytest.txt"
    original = "old transcript\n283 passed in 1.00s\n"
    output.write_text(original, encoding="utf-8")

    code = capture_gate(
        [sys.executable, "-c", "print('partial transcript')\nraise SystemExit(3)"],
        output,
        cwd=tmp_path,
    )

    assert code == 3
    assert output.read_text(encoding="utf-8") == original


def test_capture_pytest_gate_sets_capture_mode_env(tmp_path):
    output = tmp_path / "gate-pytest.txt"
    output.write_text("old transcript\n283 passed in 1.00s\n", encoding="utf-8")

    code = capture_gate(
        [
            sys.executable,
            "-c",
            "import os\n"
            "assert os.environ.get('QUANTLAB_ATOMIC_PYTEST_CAPTURE') == '1'\n"
            "print('capture mode observed')",
        ],
        output,
        cwd=tmp_path,
    )

    assert code == 0
    assert output.read_text(encoding="utf-8") == "capture mode observed\n"
