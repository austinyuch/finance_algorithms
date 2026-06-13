"""Atomically refresh the committed pytest gate transcript."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs/review/assets/gate-pytest.txt"
DEFAULT_COMMAND = ("uv", "run", "pytest", "-q")


def capture_gate(command: list[str], output_path: Path, *, cwd: Path = ROOT) -> int:
    """Run command and replace output_path only after a successful run."""
    env = os.environ.copy()
    env["QUANTLAB_ATOMIC_PYTEST_CAPTURE"] = "1"
    proc = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        return proc.returncode

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(proc.stdout)
        temp_name = handle.name

    os.replace(temp_name, output_path)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="gate transcript to replace after successful pytest completion",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="optional command after --; defaults to `uv run pytest -q`",
    )
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        command = list(DEFAULT_COMMAND)

    return capture_gate(command, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
