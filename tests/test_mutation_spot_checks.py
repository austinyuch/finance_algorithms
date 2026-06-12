"""Mutation spot-check runner tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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
    assert "engine-event-driven-date-gate" in result.stdout
    assert "yahoo-latest-close" in result.stdout
    assert "showcase-claim-boundary" in result.stdout
    assert "d2-forecast-claim-boundary" in result.stdout
    assert "d3-robust-claim-boundary" in result.stdout
    assert "e-registry-claim-boundary" in result.stdout
    assert "e-tier3-readiness-gate" in result.stdout
    assert "e-tier3-production-tier-gate" in result.stdout
    assert "e-serving-smoke-health-gate" in result.stdout
    assert "e-retraining-smoke-status-gate" in result.stdout
    assert "e-automated-drift-status-gate" in result.stdout
    assert "e-production-serving-endpoint-gate" in result.stdout
    assert "e-production-retraining-status-gate" in result.stdout
    assert "e-tier3-cli-serving-validator" in result.stdout
    assert "b-source-health-claim-boundary" in result.stdout
    assert "snapshot-report-stooq-default" in result.stdout
    assert "snapshot-scoped-source-health" in result.stdout
    assert "showcase-experiment-readiness" in result.stdout
    assert "g-alt-data-pit-gate" in result.stdout
    assert "root-torch-default-dependency" in result.stdout
    assert "governance-stale-next-steps-alert" in result.stdout
    assert "governance-stale-post-merge-sync-promotion" in result.stdout
    assert "governance-stale-cron-proof-pending" in result.stdout
    assert "governance-stale-mutation-count-regression" in result.stdout
    assert "governance-stale-dashboard-source-wording" in result.stdout
    assert "governance-f-cr-superseded-fixture-boundary" in result.stdout
    assert "public-hosting-probe-expected-hash-drift" in result.stdout
    assert "governance-test-registry-count-drift" in result.stdout
    assert "mutation-test-registry-count-drift" in result.stdout
    assert "b-scheduled-observer-manual-pending" in result.stdout
    assert "manual-showcase-payload-sync-regression" in result.stdout
    assert "frontend-showcase-payload-sync-regression" in result.stdout
    assert "review-pytest-gate-transcript-regression" in result.stdout
    assert "review-frontend-count-shorthand-regression" in result.stdout
    assert "review-audit-gate-transcript-regression" in result.stdout


def test_selected_specs_rejects_unknown_name():
    from scripts.run_mutation_spot_checks import selected_specs

    with pytest.raises(ValueError, match="unknown mutation"):
        selected_specs(["missing"])


def test_public_probe_expected_hash_mutation_tracks_current_artifact():
    from scripts.run_mutation_spot_checks import selected_specs

    probe = json.loads(Path("docs/public-hosting-probe.json").read_text(encoding="utf-8"))
    spec = selected_specs(["public-hosting-probe-expected-hash-drift"])[0]

    assert probe["expectedDataHash"] in spec.original
    assert probe["expectedDataHash"] not in Path("scripts/run_mutation_spot_checks.py").read_text(
        encoding="utf-8"
    )


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
    assert "engine-event-driven-date-gate" in out
    assert "showcase-claim-boundary" in out
    assert "d2-forecast-claim-boundary" in out
    assert "d3-robust-claim-boundary" in out
    assert "e-registry-claim-boundary" in out
    assert "e-tier3-readiness-gate" in out
    assert "e-tier3-production-tier-gate" in out
    assert "e-serving-smoke-health-gate" in out
    assert "e-retraining-smoke-status-gate" in out
    assert "e-automated-drift-status-gate" in out
    assert "e-production-serving-endpoint-gate" in out
    assert "e-production-retraining-status-gate" in out
    assert "e-tier3-cli-serving-validator" in out
    assert "b-source-health-claim-boundary" in out
    assert "snapshot-report-stooq-default" in out
    assert "snapshot-scoped-source-health" in out
    assert "showcase-experiment-readiness" in out
    assert "g-alt-data-pit-gate" in out
    assert "root-torch-default-dependency" in out
    assert "governance-stale-next-steps-alert" in out
    assert "governance-stale-post-merge-sync-promotion" in out
    assert "governance-stale-cron-proof-pending" in out
    assert "governance-stale-mutation-count-regression" in out
    assert "governance-stale-dashboard-source-wording" in out
    assert "governance-f-cr-superseded-fixture-boundary" in out
    assert "review-public-hosting-probe-status-overclaim" in out
    assert "public-hosting-probe-expected-hash-drift" in out
    assert "governance-test-registry-count-drift" in out
    assert "mutation-test-registry-count-drift" in out
    assert "b-scheduled-observer-manual-pending" in out
    assert "manual-showcase-payload-sync-regression" in out
    assert "frontend-showcase-payload-sync-regression" in out
    assert "f-showcase-retired-fixture-marker" in out
    assert "review-pytest-gate-transcript-regression" in out
    assert "review-frontend-count-shorthand-regression" in out
    assert "review-audit-gate-transcript-regression" in out
