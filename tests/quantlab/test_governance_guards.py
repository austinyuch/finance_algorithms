"""治理 guard 測試(關閉 A0 residual)。

1. import-linter:正式化框架隔離(engine/data 禁 torch/tf/jax),取代/補強 AST 測試。
2. contract drift-guard:spec SSOT 的 interfaces.py 與 quantlab 實作版 Protocol 結構須一致。
"""
from __future__ import annotations

import ast
import json
import os
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


def _current_python_mutation_count() -> int:
    registry = (ROOT / "quantlab/TESTS.md").read_text(encoding="utf-8")
    match = re.search(r"Python mutation spot checks: (?P<count>\d+)/(?P=count) configured/killed", registry)
    assert match, "quantlab/TESTS.md must publish the current Python mutation count"
    return int(match.group("count"))


def _current_python_mutation_report() -> dict[str, object]:
    report = json.loads((ROOT / "docs/review/assets/gate-python-mutation.json").read_text(encoding="utf-8"))
    assert report.get("status") in {"passed", "failed"}
    assert isinstance(report.get("total"), int)
    assert isinstance(report.get("killed"), int)
    assert isinstance(report.get("survived"), int)
    assert isinstance(report.get("mutations"), list)
    return report


def _current_pytest_count() -> int:
    registry = (ROOT / "quantlab/TESTS.md").read_text(encoding="utf-8")
    match = re.search(r"Python full suite \*\*(?P<count>\d+) passed\*\*", registry)
    assert match, "quantlab/TESTS.md must publish the current Python full-suite count"
    return int(match.group("count"))


def _current_frontend_test_count() -> int:
    gate = (ROOT / "docs/review/assets/gate-frontend-test.txt").read_text(encoding="utf-8")
    match = re.search(r"Tests\s+(?P<count>\d+) passed \((?P=count)\)", gate)
    assert match, "gate-frontend-test.txt must publish the current frontend test count"
    return int(match.group("count"))


def _current_frontend_mutation_count() -> int:
    runner = (ROOT / "frontend/scripts/run-mutation-checks.mjs").read_text(encoding="utf-8")
    count = len(re.findall(r'\n\s+name: "frontend-', runner))
    assert count > 0, "frontend mutation runner must publish configured frontend mutations"
    return count


def _current_frontend_vulnerability_count() -> int:
    audit_gate = json.loads((ROOT / "docs/review/assets/gate-frontend-audit.json").read_text(encoding="utf-8"))
    total = audit_gate["metadata"]["vulnerabilities"]["total"]
    assert isinstance(total, int) and total >= 0
    return total


def _current_frontend_line_coverage_percent() -> str:
    transcript = (ROOT / "docs/review/assets/gate-frontend-coverage.txt").read_text(encoding="utf-8")
    match = re.search(r"F Next\.js line coverage (?P<coverage>\d+\.\d+%)", transcript)
    assert match, "gate-frontend-coverage.txt must publish F Next.js line coverage"
    return match.group("coverage")


def _registry_row_pass_count(catalog: str, row_id: str) -> int:
    pattern = re.compile(rf"\| `{re.escape(row_id)}` \|[^\n]+\| (?P<count>\d+) pass(?:[^\n|]*) \|")
    match = pattern.search(catalog)
    assert match, f"missing pass-count evidence for {row_id}"
    return int(match.group("count"))


def _current_mypy_source_count() -> int:
    gate = (ROOT / "docs/review/assets/gate-mypy.txt").read_text(encoding="utf-8")
    match = re.search(r"Success: no issues found in (?P<count>\d+) source files", gate)
    assert match, "gate-mypy.txt must publish the current checked source-file count"
    return int(match.group("count"))


def _current_lint_import_counts() -> tuple[int, int]:
    gate = (ROOT / "docs/review/assets/gate-lint-imports.txt").read_text(encoding="utf-8")
    match = re.search(r"Analyzed (?P<files>\d+) files, (?P<deps>\d+) dependencies\.", gate)
    assert match, "gate-lint-imports.txt must publish analyzed file/dependency counts"
    return int(match.group("files")), int(match.group("deps"))


def _current_implemented_epic_count() -> int:
    registry = (ROOT / ".agents/specs/SPECS.md").read_text(encoding="utf-8")
    epics: set[str] = set()
    for line in registry.splitlines():
        if not (line.startswith("| [") or line.startswith("| [_")):
            continue
        cols = [col.strip() for col in line.strip("|").split("|")]
        if len(cols) < 3 or "Implemented" not in cols[2]:
            continue
        epics.update(part.strip() for part in cols[1].split("/") if part.strip())
    assert epics, "SPECS.md must publish implemented epic rows"
    return len(epics)


def _small_number_word(value: int) -> str:
    words = {
        0: "zero",
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine",
        10: "ten",
    }
    return words.get(value, str(value))


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
        "test_daily_snapshot": ROOT / "tests/test_daily_snapshot.py",
        "test_e_1_experiment_registry": ROOT / "tests/quantlab/test_e_1_experiment_registry.py",
        "test_e_production_evidence": ROOT / "tests/quantlab/test_e_production_evidence.py",
        "test_governance_guards": ROOT / "tests/quantlab/test_governance_guards.py",
        "test_mutation_spot_checks": ROOT / "tests/test_mutation_spot_checks.py",
    }

    for row_id, path in governed_rows.items():
        expected = _top_level_test_count(path)
        assert f"| `{row_id}` |" in registry
        count = _registry_row_pass_count(registry, row_id)
        assert count == expected, (
            f"quantlab/TESTS.md row {row_id} reports {count} pass, "
            f"but {path.relative_to(ROOT)} currently has {expected} tests"
        )

    workspace_rollup = (ROOT / ".agents/specs/TESTS.md").read_text(encoding="utf-8")
    f_showcase_count = _registry_row_pass_count(registry, "test_f_1_showcase_api")
    assert f"Python F {f_showcase_count} passed" in workspace_rollup
    assert "Python F 11 passed" not in workspace_rollup
    assert "no global Python line-coverage readiness threshold" in registry
    assert "focused line-coverage rows below are the current authority" in registry
    assert "--cov=quantlab --cov=scripts" in registry
    assert "must not be used as a readiness\nthreshold" in workspace_rollup


def test_local_first_ci_policy_is_repo_guided_and_skill_backed():
    """Workflow-cost policy must stay local-first unless hosted state is required."""
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    skill = (ROOT / ".agents/skills/local-first-ci/SKILL.md").read_text(encoding="utf-8")
    openai_metadata = (ROOT / ".agents/skills/local-first-ci/agents/openai.yaml").read_text(encoding="utf-8")

    assert ".agents/skills/local-first-ci/" in agents
    assert "Hosted GitHub Actions are cost-sensitive" in agents
    assert "Run the matching local gates first" in agents
    assert "do not\ntrigger or rerun GitHub Actions unless the user explicitly asks" in agents
    assert "Use local subagents or parallel local\nshells for independent CI-equivalent gates" in agents
    assert "Treat routine CI as local subagent gate\nbundles first" in agents
    assert "Python, static typing/import architecture, mutation, frontend,\nsmoke, visual, audit, and evidence-regeneration checks" in agents
    assert "Normal tests and workflow steps" in agents
    assert "would usually be queued in CI" in agents
    assert "local completion" in agents
    assert "When this repo has an equivalent command" in agents
    assert "split the gate into subagent" in agents
    assert "bundles when possible" in agents
    assert "Subagent-owned gates should return the command, exit status,\nkey evidence, and any hosted-only gap" in agents
    assert "not just a preflight before spending GitHub Actions minutes" in agents
    assert "Scope, Command, Isolation,\nEvidence, Remainder, changed files if any" in agents
    assert "fail-closed stop rule for the\nfirst unexplained failure" in agents
    assert "Completion means producing the same local pass/fail decision" in agents
    assert "not merely a preflight before Actions" in agents
    assert "If workflow or Actions cost is the concern" in agents
    assert "maximize local/subagent completion\nof the normal CI test and workflow matrix" in agents
    assert "Slow local execution is not by itself\na hosted-only gap" in agents
    assert "Treat \"CI would catch this\" as a\nlocal/subagent responsibility first" in agents
    assert "GitHub-hosted event semantics, secrets, permissions,\nartifact transport, scheduled triggers, or Pages deployment state" in agents
    assert "protected environments" in agents
    assert "remote production identity" in agents
    assert "Do not leave\nunit/integration, line coverage, PBT, mutation, smoke, build, visual, audit,\ntype/import, or generated-evidence sync gates for hosted CI" in agents
    assert "Before a push intended to trigger Actions" in agents
    assert "complete the local/subagent matrix or record the exact hosted-only gap" in agents
    assert "do not\nuse GitHub Actions as the routine queue for CI-equivalent work" in agents
    assert "For push/PR readiness, build a local CI replacement matrix" in agents
    assert "finish it before using hosted Actions for confirmation" in agents
    assert "line coverage, PBT, mutation,\nsmoke, build, visual, audit, type/import, dependency, and generated-evidence" in agents
    assert "If a remaining gate is truly hosted-only" in agents
    assert "the smallest hosted run needed" in agents
    assert "complete\nthe ordinary CI test and workflow matrix through local commands, subagents, or\nisolated local shells as far as practical" in agents
    assert "Do not leave a repo-runnable CI step\nfor Actions merely because it is slow" in agents

    assert "GitHub Actions minutes are cost-sensitive" in skill
    assert "normal CI loop as local/subagent-owned work first" in skill
    assert "same pass/fail decision CI would normally produce" in skill
    assert "Slow local runtime is not a hosted-only reason" in skill
    assert "Map each ordinary CI step to a repo-local command" in skill
    assert "Split independent read-only gates across subagents or parallel local shells" in skill
    assert "Serialize mutation, generated-artifact, and other file-mutating gates" in skill
    assert "Leave only genuinely GitHub-hosted proof in the hosted-only ledger" in skill
    assert "Unit, integration, property-based, chaos, coverage, and regression tests" in skill
    assert "Frontend unit tests, build/export, smoke, visual, audit, and frontend mutation gates" in skill
    assert "Workflow contract checks that can be proven by reading YAML" in skill
    assert "Do not push just to let Actions find ordinary failures" in skill
    assert "Use GitHub Actions only for proof that depends on GitHub-hosted state" in skill
    assert "Event payload semantics" in skill
    assert "Repository secrets, permissions, OIDC, protected environments, or deployment approvals" in skill
    assert "Artifact upload/download behavior" in skill
    assert "GitHub Pages deployment state" in skill
    assert "Remote production identity or external service binding" in skill
    assert "Before a hosted run, record the smallest remaining hosted check" in skill
    assert "Subagent Dispatch Contract" in skill
    assert "Scope: the CI job or workflow step being replaced locally" in skill
    assert "Command: exact command and working directory" in skill
    assert "Isolation: read-only, generated-artifact, mutation/file-mutating, or hosted-only" in skill
    assert "Evidence: exit status and the concise output line that matters" in skill
    assert "Remainder: hosted-only proof still required" in skill
    assert "The main agent remains responsible for changed-file scoping" in skill
    assert "Finance Algorithms Default Matrix" in skill
    assert "Python correctness:" in skill
    assert "Static architecture:" in skill
    assert "Mutation:" in skill
    assert "Frontend:" in skill
    assert "Evidence/governance:" in skill
    assert "Workflow contract:" in skill
    assert "mutation gates and generated evidence gates can edit files" in skill
    assert "Do not run them in parallel with tests or builds that read those files" in skill
    assert "Handoff Shape" in skill
    assert "`local/subagent`: ordinary gate completed locally" in skill
    assert "`serialized`: mutation or generated-artifact gate completed without racing readers" in skill
    assert "`hosted-only`: smallest remaining GitHub-hosted proof" in skill
    assert "local proof is repo-side evidence" in skill
    assert "not GitHub Actions proof, Pages proof, scheduler proof, or production proof" in skill
    assert "原本常態要給CI跑得測試and CI流程都subagent完成" in skill
    assert "workflow cost" in skill
    assert '"Actions are expensive"' in skill

    assert "Complete routine CI locally/subagent-first before Actions" in openai_metadata
    assert "locally or through subagents before spending GitHub Actions minutes" in openai_metadata
    assert "reserve Actions for hosted-only semantics" in openai_metadata


def test_github_workflows_are_hosted_only_not_routine_ci_queue():
    """Committed workflows must not hide local-testable gates in hosted Actions."""
    workflow_dir = ROOT / ".github/workflows"
    workflows = sorted(workflow_dir.glob("*.yml")) + sorted(workflow_dir.glob("*.yaml"))
    assert workflows, "repository workflow contract should stay visible to local-first CI governance"

    workflow_texts = {path: path.read_text(encoding="utf-8") for path in workflows}
    for path, text in workflow_texts.items():
        assert "local-first-ci contract:" in text, f"{path.name} must classify hosted workflow use"
        assert "hosted-only:" in text, f"{path.name} must explain why hosted proof is needed"
        assert "hosted-confirmation-only:" in text, f"{path.name} must stay confirmation-only"
        assert "local/subagent matrix must be completed before manual dispatch" in text
        assert "local-equivalent:" in text, f"{path.name} must publish local equivalents"
        assert "Routine unit/type/import/mutation/frontend/smoke gates stay local/subagent-owned" in text

    combined = "\n".join(workflow_texts.values())
    assert "hosted-only:" in combined
    assert "hosted-confirmation-only:" in combined
    assert "local-equivalent:" in combined
    assert "schedule event semantics" in combined
    assert "artifact upload transport" in combined
    assert "uv run python scripts/daily_snapshot.py --dry-run --report-json artifacts/snapshot-report.json" in combined
    assert "uv run python scripts/snapshot_schedule_report.py" in combined
    assert 'name: snapshot-schedule-proof' in combined

    routine_ci_markers = [
        "uv run pytest",
        "uv run mypy",
        "uv run lint-imports",
        "run_mutation_spot_checks.py",
        "pytest --cov",
        "coverage",
        "ruff",
        "npm test",
        "npm run test",
        "npm run build",
        "npm run smoke",
        "npm run visual",
        "npm run mutation",
        "npm audit",
        "npm run audit",
        "playwright",
        "pnpm test",
        "yarn test",
    ]
    for path, text in workflow_texts.items():
        protected_branch_confirmation = "hosted-only: branch protection status contexts" in text
        for marker in routine_ci_markers:
            if marker in text:
                assert protected_branch_confirmation, (
                    f"{marker} should stay local/subagent-owned unless {path.name} "
                    "is explicitly limited to protected-branch hosted confirmation"
                )


def test_local_ci_matrix_exposes_repo_runnable_workflow_equivalents():
    """Workflow-local equivalents must be machine-readable before hosted confirmation."""
    from scripts.local_ci_matrix import build_local_ci_matrix, matrix_payload

    gates = build_local_ci_matrix("artifacts")
    names = {gate.name for gate in gates}
    assert names == {"daily-snapshot:dry-run-report", "daily-snapshot:schedule-proof"}
    assert all(gate.isolation == "generated-artifact" for gate in gates)
    assert all(gate.workdir == "." for gate in gates)
    assert all("schedule event semantics and artifact upload transport" in gate.remainder for gate in gates)

    commands = [" ".join(gate.command) for gate in gates]
    assert "uv run python scripts/daily_snapshot.py --dry-run --report-json artifacts/snapshot-report.json" in commands
    assert any("uv run python scripts/snapshot_schedule_report.py artifacts/snapshot-report.json" in command
               for command in commands)
    assert not any("pytest" in command or "npm test" in command for command in commands)

    payload = matrix_payload("artifacts")
    assert payload["policy"] == "local-first-ci"
    assert payload["hosted_only"] == ["schedule event semantics", "artifact upload transport"]
    assert len(payload["gates"]) == 2


def test_current_mutation_count_is_single_source_synced_across_governance_surfaces():
    """Current governance artifacts must not hand-copy divergent mutation counts."""
    count = _current_python_mutation_count()
    report = _current_python_mutation_report()
    expected = f"{count}/{count}"
    assert report["status"] == "passed"
    assert report["total"] == count
    assert report["killed"] == count
    assert report["survived"] == 0
    assert len(report["mutations"]) == count
    assert all(item["status"] == "killed" for item in report["mutations"])
    surfaces = {
        "quantlab/CORRECTNESS_CHECKLIST.md": [
            f"current configured suite is {expected}",
            f"run_mutation_spot_checks.py`({expected} killed)",
        ],
        ".agents/specs/NEXT_STEPS.md": [
            f"**{expected} configured/killed**",
        ],
        ".agents/specs/RTM.md": [
            f"{expected} configured mutations killed",
        ],
        ".agents/specs/SPECS.md": [
            f"consolidated to {expected}",
        ],
        ".agents/specs/ISSUE_LOG.md": [
            f"{expected} Python mutation spot checks configured",
        ],
        "docs/FEATURES.md": [
            f"**{expected} configured/killed**",
        ],
    }

    for rel_path, snippets in surfaces.items():
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        for snippet in snippets:
            assert snippet in text, f"{rel_path} does not match current mutation evidence: {snippet}"

    mutation_name_surfaces = [
        ".agents/specs/NEXT_STEPS.md",
        ".agents/specs/RTM.md",
        "docs/FEATURES.md",
    ]
    for rel_path in mutation_name_surfaces:
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        assert text.count("`browser-visual-doc-sync-gate-regression`") == 1, (
            f"{rel_path} must not duplicate browser visual doc-sync mutation evidence"
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
        ROOT / ".agents/specs/a-torch-default-dependency-isolation/review.md",
        ROOT / ".agents/specs/a-torch-default-dependency-isolation/reports/implementation-report.md",
        ROOT / ".agents/specs/e-tier3-serving-evidence/review.md",
        ROOT / ".agents/specs/e-tier3-retraining-evidence/review.md",
        ROOT / ".agents/specs/e-tier3-retraining-evidence/reports/implementation-report.md",
        ROOT / ".agents/specs/e-tier3-production-evidence-gate/review.md",
        ROOT / ".agents/specs/e-tier3-production-evidence-gate/reports/implementation-report.md",
        ROOT / ".agents/specs/e-tier3-production-probes/review.md",
        ROOT / ".agents/specs/e-tier3-production-probes/tasks.md",
        ROOT / ".agents/specs/e-tier3-production-probes/reports/implementation-report.md",
        ROOT / ".agents/specs/e-tier3-readiness-proof-cli/review.md",
        ROOT / ".agents/specs/e-tier3-readiness-proof-cli/tasks.md",
        ROOT / ".agents/specs/e-tier3-readiness-proof-cli/reports/implementation-report.md",
        ROOT / ".agents/specs/governance-evidence-refresh/review.md",
        ROOT / ".agents/specs/governance-evidence-refresh/reports/implementation-report.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/review.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/reports/implementation-report.md",
        ROOT / ".agents/specs/f-demo-hardening/review.md",
        ROOT / ".agents/specs/f-demo-hardening/reports/implementation-report.md",
        ROOT / ".agents/specs/f-public-static-showcase/change-requests/cr-fps-008-public-probe-freshness-gate.md",
    ]
    stale_markers = [
        "190 pytest",
        "20 frontend tests",
        "stale governance guard 20 passed",
        "22 mutation",
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
        "<b>214</b><span>Python tests passing</span>",
        "266 passed",
        "242 passed",
        "241 passed",
        "231 passed",
        "238 passed",
        "237 passed",
        "240 passed",
        "239 passed",
        "23 frontend tests",
        "<b>23</b><span>frontend tests passing</span>",
        "27 frontend tests",
        "27 tests pass",
        " 33 passed",
        "16/16 killed",
        "16/16 frontend",
        "188 passed, 1 skipped",
        "200 passed, 1 skipped",
        "204 passed, 1 skipped",
        "207 passed, 1 skipped",
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
            "69/69 configured",
            "69/69 Python mutation",
            "Python mutation 69/69",
            "mutation spot checks 69/69",
            "mutation spot-checks are **69/69",
            "70/70 configured",
            "70/70 Python mutation",
            "Python mutation 70/70",
            "mutation spot checks 70/70",
            "mutation spot-checks are **70/70",
                "71/71 configured",
                "71/71 Python mutation",
                "Python mutation 71/71",
                "mutation spot checks 71/71",
                "mutation spot-checks are **71/71",
                    "76/76 configured",
                    "76/76 Python mutation",
                    "Python mutation 76/76",
                    "mutation spot checks 76/76",
                    "mutation spot-checks are **76/76",
                    "77/77 configured",
                    "77/77 Python mutation",
                    "Python mutation 77/77",
                    "mutation spot checks 77/77",
                    "mutation spot-checks are **77/77",
                    "80/80 configured",
                    "80/80 Python mutation",
                    "Python mutation 80/80",
                    "mutation spot checks 80/80",
                    "mutation spot-checks are **80/80",
                        "81/81 configured",
                        "current configured suite is 81/81",
                        "81/81 Python mutation",
                        "Python mutation 81/81",
                        "mutation spot checks 81/81",
                        "mutation spot-checks are **81/81",
                        "run_mutation_spot_checks.py`(81/81 killed)",
                        "82/82 configured",
                        "current configured suite is 82/82",
                        "82/82 Python mutation",
                        "Python mutation 82/82",
                        "mutation spot checks 82/82",
                        "mutation spot-checks are **82/82",
                        "run_mutation_spot_checks.py`(82/82 killed)",
                    "79/79 configured",
                    "79/79 Python mutation",
                    "Python mutation 79/79",
                    "mutation spot checks 79/79",
                    "mutation spot-checks are **79/79",
                    "6/6 configured",
        "kills 6/6 configured mutations",
        "mutation spot-check 5/5",
        "41/41 Python mutation",
        "236 passed",
        "included in 236 passed",
        "214 passed",
        "1 skipped",
        "264 passed",
        "275 passed",
        "`uv run pytest -q`(430 passed)",
        "275 Python tests",
        "275 suite evidence",
        "276 Python tests",
        "279 passed",
        "96/96",
        "88/88",
        "99/99",
        "total=99",
        "killed=99",
        "35/35 configured",
        "35/35 configured mutations",
        "57 source files",
        "57 files",
        "clean over 55 files",
        "55 source files",
        "clean over 51 files",
        "clean over 52 files",
        "53 files",
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
        "75 files / 186 dependencies",
        "75 files, 186 dependencies",
        "75 files / 186 deps",
        "75 files, 186 deps",
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
        "18/18 frontend mutations",
        "18/18 frontend mutation",
        "mutation 18/18 killed",
        "frontend mutation 18/18",
        "19/19 frontend mutations",
        "19/19 frontend mutation",
        "mutation 19/19 killed",
        "frontend mutation 19/19",
        "91.07% line coverage",
        "F Next.js coverage 91.07%",
        "221 / 1,296,000",
        "221/1,296,000",
        "latest 221",
        "505 / 1,296,000",
        "505/1,296,000",
        "0.0003896604938271605",
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
        "Public hosting and visual regression remain `not_proven`",
        "Public hosting and visual regression remain deferred",
        "not_proven public hosting/visual regression",
        "prove public hosting + visual regression",
        "readiness panel remains conservative (`not_proven`) by dashboard contract",
        "Static export 內嵌 readiness 面板依 dashboard contract 保守顯示 `not_proven`",
        "## Current State (2026-06-12)",
        "Latest authoritative gate evidence (2026-06-12)",
        "Captured live (2026-06-12)",
        "Gaps resolved since last check (2026-06-11 → 2026-06-12)",
        "Resolved (2026-06-11 → 2026-06-12)",
        "自上次檢查以來已解決（2026-06-11 → 2026-06-12）",
    ]

    for path in current_surfaces:
        text = path.read_text(encoding="utf-8")
        for marker in stale_markers:
            assert marker not in text, f"{path.relative_to(ROOT)} still publishes stale marker: {marker}"

    governance_count = _top_level_test_count(ROOT / "tests/quantlab/test_governance_guards.py")
    frontend_count = _current_frontend_test_count()
    governance_refresh_surfaces = [
        ROOT / ".agents/specs/governance-evidence-refresh/review.md",
        ROOT / ".agents/specs/governance-evidence-refresh/reports/implementation-report.md",
    ]
    for path in governance_refresh_surfaces:
        text = path.read_text(encoding="utf-8")
        assert (
            f"`uv run pytest -q tests/quantlab/test_governance_guards.py` -> {governance_count} passed"
            in text
        ), f"{path.relative_to(ROOT)} must track the current governance guard count"
        assert (
            f"`cd frontend && npm test -- --run` -> {frontend_count} passed" in text
            or f"Frontend unit: `cd frontend && npm test -- --run` -> {frontend_count} passed" in text
        ), f"{path.relative_to(ROOT)} must track the current frontend test count"


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


def test_evidence_metadata_contract_keeps_fixture_backed_legacy_only():
    """Current stakeholder evidence must prefer canonical result-store labels over fixtures."""
    contract = (ROOT / "docs/EVIDENCE_METADATA_CONTRACT.md").read_text(encoding="utf-8")
    taxonomy = (ROOT / "docs/DEMO_RISK_WARNING_TAXONOMY.md").read_text(encoding="utf-8")
    canonical_source_docs = [
        ROOT / "docs/manual/en/index.md",
        ROOT / "docs/manual/zh-tw/index.md",
        ROOT / "docs/manual/en/index.html",
        ROOT / "docs/manual/zh-tw/index.html",
        ROOT / "docs/FEATURES.md",
    ]
    current_docs = [
        *canonical_source_docs,
        ROOT / "docs/review/index.html",
    ]

    assert "`fixture-backed` is a legacy/retired evidence-source label" in contract
    assert "MUST use `canonical_local_result_store`" in contract
    assert "MUST NOT describe that payload as\n  fixture-backed" in contract
    assert "Do not describe current canonical local result-store payloads as fixture-backed" in taxonomy
    assert "Use conservative wording (`illustrative`, `fixture-backed`)" not in taxonomy

    for path in canonical_source_docs:
        text = path.read_text(encoding="utf-8")
        assert "canonical_local_result_store" in text

    for path in current_docs:
        text = path.read_text(encoding="utf-8")
        assert "Evidence Source: fixture-backed" not in text
        assert "Evidence Source：</b>fixture-backed" not in text
        assert "Evidence Source:</b> fixture-backed" not in text


def test_current_review_gate_transcripts_match_published_evidence():
    """Review gate transcripts and generation guides must match current evidence counts."""
    pytest_count = _current_pytest_count()
    frontend_count = _current_frontend_test_count()
    frontend_mutation_count = _current_frontend_mutation_count()
    vulnerability_count = _current_frontend_vulnerability_count()
    frontend_coverage = _current_frontend_line_coverage_percent()
    mypy_source_count = _current_mypy_source_count()
    lint_file_count, lint_dependency_count = _current_lint_import_counts()
    implemented_epic_count = _current_implemented_epic_count()
    review_html = (ROOT / "docs/review/index.html").read_text(encoding="utf-8")
    manual_guide = (ROOT / "docs/MANUAL_GENERATION_GUIDE.md").read_text(encoding="utf-8")
    review_guide = (ROOT / "docs/REVIEW_GENERATION_GUIDE.md").read_text(encoding="utf-8")
    features = (ROOT / "docs/FEATURES.md").read_text(encoding="utf-8")
    rtm = (ROOT / ".agents/specs/RTM.md").read_text(encoding="utf-8")
    quantlab_tests = (ROOT / "quantlab/TESTS.md").read_text(encoding="utf-8")
    spec_tests = (ROOT / ".agents/specs/TESTS.md").read_text(encoding="utf-8")
    next_steps = (ROOT / ".agents/specs/NEXT_STEPS.md").read_text(encoding="utf-8")
    showcase_payload = json.loads((ROOT / "docs/showcase.json").read_text(encoding="utf-8"))
    pytest_gate = (ROOT / "docs/review/assets/gate-pytest.txt").read_text(encoding="utf-8")
    frontend_gate = (ROOT / "docs/review/assets/gate-frontend-test.txt").read_text(encoding="utf-8")
    mypy_gate = (ROOT / "docs/review/assets/gate-mypy.txt").read_text(encoding="utf-8")
    lint_gate = (ROOT / "docs/review/assets/gate-lint-imports.txt").read_text(encoding="utf-8")
    audit_text = (ROOT / "docs/review/assets/gate-frontend-audit.txt").read_text(encoding="utf-8")
    audit_gate = json.loads((ROOT / "docs/review/assets/gate-frontend-audit.json").read_text(encoding="utf-8"))

    if os.environ.get("QUANTLAB_ATOMIC_PYTEST_CAPTURE") != "1":
        assert f"{pytest_count} passed" in pytest_gate
    assert f"{pytest_count} passed" in manual_guide
    assert f"{pytest_count} passed" in review_guide
    assert f"Python suite now <b>{pytest_count} passed</b>" in review_html
    assert f"<b>{pytest_count}</b><span>Python tests passing</span>" in review_html
    assert f"Tests  {frontend_count} passed ({frontend_count})" in frontend_gate
    assert f"# {frontend_count} passed, {vulnerability_count} vulnerabilities" in manual_guide
    assert f"# {frontend_count} passed     → gate-frontend-test.txt" in review_guide
    assert f"`npm test` → **{frontend_count} passed**" in features
    assert f"| Frontend unit | `cd frontend && npm test` | {frontend_count} passed |" in rtm
    assert f"Frontend <b>{frontend_count} tests pass</b>" in review_html
    assert f"frontend mutation {frontend_mutation_count}/{frontend_mutation_count} killed" in features
    assert (
        f"frontend mutation {frontend_mutation_count}/{frontend_mutation_count} killed"
        in review_html
    )
    assert "frontend-smoke-html-api-parity-regression" in features
    assert "frontend-smoke-html-api-parity-regression" in quantlab_tests
    assert "HTML/API payload parity" in review_html
    assert f"<b>{frontend_count}</b><span>frontend tests passing</span>" in review_html
    assert f"<b>{implemented_epic_count}</b><span>spec epics implemented</span>" in review_html
    assert f"{_small_number_word(implemented_epic_count)} spec epics are implemented" in review_html
    assert "27 tests pass" not in review_html
    assert "28 tests pass" not in review_html
    assert "29 tests pass" not in review_html
    assert "36 passed, 0 vulnerabilities" not in manual_guide
    assert "36 passed     → gate-frontend-test.txt" not in review_guide
    assert "`npm test` → **36 passed**" not in features
    assert "| Frontend unit | `cd frontend && npm test` | 36 passed |" not in rtm
    assert "| E registry + production evidence line coverage |" in rtm
    assert "| E registry + production evidence line coverage | `uv run pytest --cov=quantlab.mlops.experiment_registry --cov=quantlab.mlops.production_evidence --cov-report=term-missing tests/quantlab/test_e_1_experiment_registry.py tests/quantlab/test_e_production_evidence.py` | 37 passed; 99% combined line coverage |" in rtm
    assert "35 passed; 99% line coverage" not in rtm
    assert f"Success: no issues found in {mypy_source_count} source files" in mypy_gate
    assert f"clean, {mypy_source_count} files" in manual_guide
    assert f"clean {mypy_source_count} files" in review_guide
    assert f"**{mypy_source_count} source files**" in features
    assert f"Analyzed {lint_file_count} files, {lint_dependency_count} dependencies." in lint_gate
    assert f"KEPT, {lint_file_count} files / {lint_dependency_count} dependencies" in manual_guide
    assert f"KEPT, {lint_file_count} files / {lint_dependency_count} deps" in review_guide
    assert f"({lint_file_count} files, {lint_dependency_count} deps)" in features
    assert (
        f"Import-linter contract KEPT ({lint_file_count} files / {lint_dependency_count} deps)"
        in review_html
    )
    assert audit_text.strip() == f"found {vulnerability_count} vulnerabilities"
    assert audit_gate["metadata"]["vulnerabilities"]["total"] == vulnerability_count
    assert f"<b>{vulnerability_count}</b><span>frontend vulnerabilities</span>" in review_html
    assert f"Frontend audit reports {vulnerability_count} vulnerabilities" in review_html
    assert (
        f"Frontend <b>{frontend_count} tests pass</b>, coverage {frontend_coverage}, "
        f"<b>{vulnerability_count}</b> dependency vulnerabilities"
        in review_html
    )
    assert f"frontend coverage **{frontend_coverage}**" in features
    assert f"coverage {frontend_coverage}" in quantlab_tests
    assert f"{frontend_coverage} line coverage" in quantlab_tests
    assert f"{frontend_coverage} line coverage" in spec_tests
    assert f"line coverage {frontend_coverage}" in next_steps
    assert f"F Next.js coverage {frontend_coverage}" in showcase_payload["evidence"]["tests"]


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
    assert browser_diff["maxMismatchRatio"] == 0.001
    assert browser_diff["status"] == "passed"
    assert 0 <= browser_diff["mismatchedPixels"] <= browser_diff["totalPixels"]
    assert browser_diff["mismatchRatio"] == browser_diff["mismatchedPixels"] / browser_diff["totalPixels"]


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
    visual_evidence = "browser visual diff passed"

    assert frontend_showcase == showcase
    assert manual_showcase == showcase
    assert review_showcase == showcase
    assert review_public_probe == public_probe
    assert showcase["demoReadiness"]["publicHosting"] == "not_proven"
    assert showcase["demoReadiness"]["visualRegression"] == "proven"
    assert visual_evidence in showcase["evidence"]["tests"]
    assert not any(
        item.startswith("browser visual diff ") and item != visual_evidence
        for item in showcase["evidence"]["tests"]
    )
    assert (ROOT / "docs/manual/assets/dashboard-static-export.html").read_text(encoding="utf-8") == (
        ROOT / "docs/index.html"
    ).read_text(encoding="utf-8")
    assert visual_evidence in (ROOT / "docs/index.html").read_text(encoding="utf-8")
    assert re.search(
        r"browser visual diff \d+/\d+ passed",
        (ROOT / "docs/index.html").read_text(encoding="utf-8"),
    ) is None


def _assert_hash_surface_publishes_current(text: str, current_hash: str, baseline_hash: str) -> None:
    """A current hash surface must publish ``current_hash``; it must not publish a
    *distinct* stale ``baseline_hash``. CR-FBP-001: when a baseline is re-pinned in
    a deterministic-rendering environment ``baseline_hash == current_hash`` (0-pixel
    diff), so there is no distinct stale hash to forbid."""
    assert current_hash in text
    if baseline_hash != current_hash:
        assert baseline_hash not in text


def test_traceability_visual_evidence_tracks_current_pixel_diff():
    """Governance bridge docs must not publish stale browser visual mismatch counts."""
    browser_visual = json.loads((ROOT / "docs/browser-visual.json").read_text(encoding="utf-8"))
    browser_diff = json.loads((ROOT / "docs/browser-visual-diff.json").read_text(encoding="utf-8"))
    spaced = f"{browser_diff['mismatchedPixels']} / {browser_diff['totalPixels']:,}"
    compact = f"{browser_diff['mismatchedPixels']} / 1,296,000"
    current_hash = browser_visual["screenshotHash"]
    baseline_hash = browser_diff["baselineHash"]
    current_surfaces = [
        ROOT / ".agents/specs/SPECS.md",
        ROOT / ".agents/specs/RTM.md",
        ROOT / ".agents/specs/NEXT_STEPS.md",
        ROOT / ".agents/specs/governance-evidence-refresh/review.md",
        ROOT / ".agents/specs/governance-evidence-refresh/reports/implementation-report.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/review.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/reports/implementation-report.md",
        ROOT / ".agents/specs/f-public-static-showcase/change-requests/cr-fps-009-dashboard-visual-readiness-wireup.md",
        ROOT / "docs/DEMO_RISK_WARNING_TAXONOMY.md",
        ROOT / "docs/FEATURES.md",
        ROOT / "docs/manual/en/index.md",
        ROOT / "docs/manual/en/index.html",
        ROOT / "docs/manual/zh-tw/index.md",
        ROOT / "docs/manual/zh-tw/index.html",
        ROOT / "docs/review/index.html",
        ROOT / "quantlab/TESTS.md",
    ]
    current_hash_surfaces = [
        ROOT / ".agents/specs/NEXT_STEPS.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/review.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/reports/implementation-report.md",
    ]

    assert current_hash == browser_diff["currentHash"]
    for path in current_surfaces:
        text = path.read_text(encoding="utf-8")
        assert spaced in text or compact in text
        assert "0/1,296,000" not in text
        assert "1089 / 1,296,000" not in text
        assert "1089/1296000" not in text
    for path in current_hash_surfaces:
        _assert_hash_surface_publishes_current(
            path.read_text(encoding="utf-8"), current_hash, baseline_hash
        )


def test_browser_visual_smoke_fails_closed_on_stale_committed_docs():
    """The browser visual smoke gate must not pass while committed evidence is stale."""
    script = (ROOT / "frontend/scripts/browser-visual-smoke.mjs").read_text(encoding="utf-8")
    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))

    assert "QUANTLAB_BROWSER_VISUAL_UPDATE_DOCS" in script
    assert "assertCommittedDocsFresh(evidence, diff);" in script
    assert "syncCommittedDocs(evidence, diff);" in script
    assert "docs/browser-visual.json" in script
    assert "docs/review/assets/browser-visual-diff.json" in script
    assert "docs/manual/assets/dashboard-browser-visual.png" in script
    assert (
        package["scripts"]["visual:browser:update-docs"]
        == "QUANTLAB_BROWSER_VISUAL_UPDATE_DOCS=1 node scripts/browser-visual-smoke.mjs"
    )


def test_current_dashboard_source_wording_tracks_canonical_payload():
    """Current F/governance handoff surfaces must not point at the retired inline fixture."""
    current_source_surfaces = [
        ROOT / ".agents/specs/NEXT_STEPS.md",
        ROOT / ".agents/specs/a-torch-default-dependency-isolation/review.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/design.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/review.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/reports/implementation-report.md",
        ROOT / ".agents/specs/f-demo-hardening/design.md",
        ROOT / ".agents/specs/f-demo-hardening/requirements.md",
        ROOT / ".agents/specs/f-demo-hardening/tasks.md",
        ROOT / ".agents/specs/f-demo-hardening/reports/implementation-report.md",
        ROOT / ".agents/specs/f-nextjs-showcase-dashboard/design.md",
        ROOT / ".agents/specs/f-nextjs-showcase-dashboard/requirements.md",
        ROOT / ".agents/specs/f-nextjs-showcase-dashboard/tasks.md",
        ROOT / ".agents/specs/f-public-demo-readiness/review.md",
        ROOT / ".agents/specs/governance-evidence-refresh/design.md",
        ROOT / ".agents/specs/governance-evidence-refresh/tasks.md",
        ROOT / ".agents/specs/governance-evidence-refresh/review.md",
    ]
    stale_source_markers = [
        "frontend/lib/showcase-fixture.ts",
        "Fixture[showcase fixture]",
        "contract/fixture updates",
        "fixture/API/component render tests",
        "deterministic fixture",
        "fixture contract",
        "typed contract, fixture",
        "future fixtures cannot silently claim public hosting or visual regression evidence",
        "Actual public hosting and visual regression remain `not_proven`",
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


def test_f_nextjs_showcase_review_tracks_superseding_public_and_payload_lanes():
    """The original F Next.js slice must not republish stale fixture/audit/public-readiness state."""
    frontend_count = _current_frontend_test_count()
    surfaces = [
        ROOT / ".agents/specs/f-nextjs-showcase-dashboard/review.md",
        ROOT / ".agents/specs/f-nextjs-showcase-dashboard/reports/implementation-report.md",
        ROOT / ".agents/specs/f-demo-hardening/review.md",
        ROOT / ".agents/specs/f-demo-hardening/reports/implementation-report.md",
        ROOT / ".agents/specs/f-public-demo-readiness/review.md",
        ROOT / ".agents/specs/f-public-static-showcase/review.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/review.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/reports/implementation-report.md",
    ]
    audit_surfaces = [
        ROOT / ".agents/specs/f-nextjs-showcase-dashboard/review.md",
        ROOT / ".agents/specs/f-nextjs-showcase-dashboard/reports/implementation-report.md",
        ROOT / ".agents/specs/f-demo-hardening/reports/implementation-report.md",
        ROOT / ".agents/specs/f-public-demo-readiness/review.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/review.md",
        ROOT / ".agents/specs/f-browser-pixel-baseline/reports/implementation-report.md",
    ]
    stale_markers = [
        "lib/showcase-fixture.ts",
        "canonical fixture",
        "fixture-backed",
        "No public hosted URL or visual screenshot baseline is claimed",
        "npm audit` reports two moderate advisories",
        "2 moderate severity advisories",
        "`npm test -- --run` -> 4 passed",
        "80.76%",
        "3042",
        "36 passed",
    ]

    for path in surfaces:
        text = path.read_text(encoding="utf-8")
        assert f"{frontend_count} passed" in text
        for marker in stale_markers:
            assert marker not in text, f"{path.relative_to(ROOT)} still publishes stale F Next.js marker: {marker}"
    for path in audit_surfaces:
        text = path.read_text(encoding="utf-8")
        assert "0 vulnerabilities" in text


def test_next_steps_reflects_post_merge_torch_alert_state():
    """Current Torch dependency surfaces must not preserve stale rescan-pending state."""
    surfaces = [
        ROOT / ".agents/specs/NEXT_STEPS.md",
        ROOT / ".agents/specs/a-torch-default-dependency-isolation/design.md",
        ROOT / ".agents/specs/a-torch-default-dependency-isolation/review.md",
        ROOT / ".agents/specs/a-torch-default-dependency-isolation/reports/implementation-report.md",
    ]

    for path in surfaces:
        text = path.read_text(encoding="utf-8")
        assert "Commit/push `spec/a-torch-default-dependency-isolation`" not in text
        assert "implemented locally" not in text
        assert "post-merge rescan pending" not in text
        assert "alert state will remain open" not in text
        assert "must be rechecked after merge" not in text
        assert "not prove GitHub has rescanned and closed the alert yet" not in text
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


def test_current_spec_reviews_do_not_overclaim_public_hosting_from_http_200_only():
    """Current review/report surfaces must follow CR-FPS-007/008 fail-closed hosting parity."""
    current_surfaces = [
        ROOT / ".agents/specs/ops-visual-drift-artifacts/review.md",
        ROOT / ".agents/specs/ops-visual-drift-artifacts/reports/implementation-report.md",
        ROOT / ".agents/specs/next-gaps-1-6-tier3-public/review.md",
        ROOT / ".agents/specs/next-gaps-1-6-tier3-public/reports/implementation-report.md",
    ]

    for path in current_surfaces:
        text = path.read_text(encoding="utf-8")
        assert "configured_not_observed" in text, f"{path} must name current fail-closed hosting parity"
        assert "dataHash" in text, f"{path} must explain the deployed hash boundary"
        assert "proven HTTP 200" not in text
        assert "hostingEvidence.status=proven" not in text
        assert "Public static hosting is proven" not in text
        assert "Public static hosting: proven" not in text


def test_demo_risk_taxonomy_names_current_public_hosting_authority():
    """Stakeholder warning taxonomy must point at committed parity evidence."""
    text = (ROOT / "docs/DEMO_RISK_WARNING_TAXONOMY.md").read_text(encoding="utf-8")

    assert "CR-FPS-001 + CR-FPS-002 + CR-FPS-003 + CR-FPS-007 + CR-FPS-008" in text
    assert "standalone probe parity" in text
    assert "freshness" in text
    assert "docs/deployment-manifest.json" in text
    assert "docs/public-hosting-probe.json" in text
    assert "frontend/out/public-hosting-probe.json" not in text
