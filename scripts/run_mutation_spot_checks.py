"""Run deterministic mutation spot-checks for critical QuantLab logic.

This is a repo-local fallback for cases where mutmut's sandbox layout is too narrow
for top-level imports. Each mutation is applied, its targeted tests must fail, and
the original file is restored before the next check.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class MutationSpec:
    name: str
    path: str
    original: str
    mutated: str
    test_command: tuple[str, ...]


@dataclass(frozen=True)
class MutationToken:
    path: Path
    original_text: str


MUTATIONS: tuple[MutationSpec, ...] = (
    MutationSpec(
        name="engine-regime-selector",
        path="quantlab/engine/vectorized.py",
        original="return select_rebalance_dates(candidates, labels, frequency=frequency)",
        mutated="return candidates",
        test_command=("uv", "run", "pytest", "-q", "tests/quantlab/test_a0_2_engine.py", "-k", "regime_rebalance"),
    ),
    MutationSpec(
        name="c3-regime-change",
        path="quantlab/portfolio/rebalance.py",
        original="regime_changed = previous_label is not None and label != previous_label",
        mutated="regime_changed = previous_label is not None and label == previous_label",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/quantlab/test_c_3_rebalance.py::test_pbt_regime_rebalance_is_ordered_subset_and_captures_changes"),
    ),
    MutationSpec(
        name="yahoo-latest-close",
        path="scripts/daily_snapshot.py",
        original="valid = [(ts, close) for ts, close in zip(timestamps, closes) if close is not None]",
        mutated="valid = [(ts, close) for ts, close in zip(timestamps, closes)]",
        test_command=("uv", "run", "pytest", "-q",
                      "tests/test_daily_snapshot.py::test_pbt_yahoo_latest_event_date_matches_last_valid_close"),
    ),
)


def apply_mutation(root: Path, spec: MutationSpec) -> MutationToken:
    path = root / spec.path
    text = path.read_text(encoding="utf-8")
    occurrences = text.count(spec.original)
    if occurrences != 1:
        raise ValueError(f"{spec.name}: original text must occur exactly once, found {occurrences}")
    path.write_text(text.replace(spec.original, spec.mutated, 1), encoding="utf-8")
    return MutationToken(path=path, original_text=text)


def restore_mutation(token: MutationToken) -> None:
    token.path.write_text(token.original_text, encoding="utf-8")


def selected_specs(names: Sequence[str]) -> list[MutationSpec]:
    if not names:
        return list(MUTATIONS)
    wanted = set(names)
    found = [spec for spec in MUTATIONS if spec.name in wanted]
    missing = wanted - {spec.name for spec in found}
    if missing:
        raise ValueError(f"unknown mutation(s): {', '.join(sorted(missing))}")
    return found


def run_mutation(root: Path, spec: MutationSpec) -> bool:
    token = apply_mutation(root, spec)
    try:
        result = subprocess.run(spec.test_command, cwd=root)
        killed = result.returncode != 0
        status = "KILLED" if killed else "SURVIVED"
        print(f"{spec.name}: {status}")
        return killed
    finally:
        restore_mutation(token)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list available mutation names")
    parser.add_argument("--only", action="append", default=[], help="run one mutation by name; repeatable")
    args = parser.parse_args(argv)

    if args.list:
        for spec in MUTATIONS:
            print(spec.name)
        return 0

    root = Path(__file__).resolve().parents[1]
    specs = selected_specs(args.only)
    results = [run_mutation(root, spec) for spec in specs]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
