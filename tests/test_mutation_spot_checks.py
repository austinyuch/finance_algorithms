"""Mutation spot-check runner tests."""
from __future__ import annotations

import subprocess
import sys

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    prefix=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), max_size=30),
    suffix=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), max_size=30),
)
def test_pbt_mutation_apply_restore_roundtrip(tmp_path, prefix, suffix):
    from scripts.run_mutation_spot_checks import MutationSpec, apply_mutation, restore_mutation

    target = tmp_path / "sample.py"
    original = "return left != right"
    mutated = "return left == right"
    target.write_text(prefix + original + suffix, encoding="utf-8")
    spec = MutationSpec(
        name="demo",
        path="sample.py",
        original=original,
        mutated=mutated,
        test_command=(sys.executable, "-c", "raise SystemExit(1)"),
    )

    token = apply_mutation(tmp_path, spec)
    assert target.read_text(encoding="utf-8") == prefix + mutated + suffix

    restore_mutation(token)
    assert target.read_text(encoding="utf-8") == prefix + original + suffix


def test_mutation_apply_rejects_ambiguous_original(tmp_path):
    from scripts.run_mutation_spot_checks import MutationSpec, apply_mutation

    target = tmp_path / "sample.py"
    target.write_text("x = 1\nx = 1\n", encoding="utf-8")
    spec = MutationSpec(
        name="ambiguous",
        path="sample.py",
        original="x = 1",
        mutated="x = 2",
        test_command=(sys.executable, "-c", "raise SystemExit(1)"),
    )

    with pytest.raises(ValueError, match="exactly once"):
        apply_mutation(tmp_path, spec)


def test_mutation_runner_list_smoke():
    result = subprocess.run(
        [sys.executable, "scripts/run_mutation_spot_checks.py", "--list"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "engine-regime-selector" in result.stdout
    assert "yahoo-latest-close" in result.stdout
    assert "showcase-claim-boundary" in result.stdout
    assert "d2-forecast-claim-boundary" in result.stdout
    assert "d3-robust-claim-boundary" in result.stdout
    assert "e-registry-claim-boundary" in result.stdout
    assert "b-source-health-claim-boundary" in result.stdout
    assert "snapshot-report-stooq-default" in result.stdout
    assert "showcase-experiment-readiness" in result.stdout
    assert "g-alt-data-pit-gate" in result.stdout
    assert "root-torch-default-dependency" in result.stdout
    assert "governance-stale-next-steps-alert" in result.stdout


def test_selected_specs_rejects_unknown_name():
    from scripts.run_mutation_spot_checks import selected_specs

    with pytest.raises(ValueError, match="unknown mutation"):
        selected_specs(["missing"])


def test_purge_python_bytecode_removes_pycache(tmp_path):
    from scripts.run_mutation_spot_checks import purge_python_bytecode

    cache = tmp_path / "pkg" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "module.cpython-313.pyc").write_bytes(b"stale")

    purge_python_bytecode(tmp_path)

    assert not cache.exists()


def test_run_mutation_returns_true_when_test_command_fails_and_restores(tmp_path):
    from scripts.run_mutation_spot_checks import MutationSpec, run_mutation

    target = tmp_path / "sample.py"
    target.write_text("return left != right", encoding="utf-8")
    spec = MutationSpec(
        name="demo",
        path="sample.py",
        original="return left != right",
        mutated="return left == right",
        test_command=(sys.executable, "-c", "raise SystemExit(1)"),
    )

    assert run_mutation(tmp_path, spec) is True
    assert target.read_text(encoding="utf-8") == "return left != right"


def test_run_mutation_returns_false_when_test_command_passes_and_restores(tmp_path):
    from scripts.run_mutation_spot_checks import MutationSpec, run_mutation

    target = tmp_path / "sample.py"
    target.write_text("return left != right", encoding="utf-8")
    spec = MutationSpec(
        name="demo",
        path="sample.py",
        original="return left != right",
        mutated="return left == right",
        test_command=(sys.executable, "-c", "raise SystemExit(0)"),
    )

    assert run_mutation(tmp_path, spec) is False
    assert target.read_text(encoding="utf-8") == "return left != right"


def test_main_list_prints_mutation_names(capsys):
    from scripts.run_mutation_spot_checks import main

    assert main(["--list"]) == 0
    out = capsys.readouterr().out
    assert "engine-regime-selector" in out
    assert "showcase-claim-boundary" in out
    assert "d2-forecast-claim-boundary" in out
    assert "d3-robust-claim-boundary" in out
    assert "e-registry-claim-boundary" in out
    assert "b-source-health-claim-boundary" in out
    assert "snapshot-report-stooq-default" in out
    assert "showcase-experiment-readiness" in out
    assert "g-alt-data-pit-gate" in out
    assert "root-torch-default-dependency" in out
    assert "governance-stale-next-steps-alert" in out
