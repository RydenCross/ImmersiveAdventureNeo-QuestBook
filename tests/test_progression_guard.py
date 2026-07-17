from __future__ import annotations

from dataclasses import replace
import json

from content import create_project
from generator.cli import main
from generator.progression_guard import (
    ProgressionBudget,
    guard_progression,
    load_progression_budget,
    run_progression_guard,
)
from generator.progression_metrics import analyze_progression


def test_checked_in_progression_budget_passes() -> None:
    result = run_progression_guard()
    assert result.is_clean
    assert result.violations == ()


def test_guard_detects_complexity_regressions() -> None:
    metrics = analyze_progression(create_project())
    budget = ProgressionBudget(
        minimum_quests=metrics.quests + 1,
        minimum_dependencies=metrics.dependencies + 1,
        maximum_depth=metrics.maximum_depth - 1,
        maximum_bottlenecks=len(metrics.bottlenecks) - 1,
        maximum_direct_dependants=5,
        maximum_chapter_transitions=len(metrics.chapter_transitions) - 1,
    )
    result = guard_progression(metrics, budget)
    assert not result.is_clean
    assert len(result.violations) == 6


def test_cli_writes_machine_readable_guard_report(tmp_path) -> None:
    output = tmp_path / "progression-guard.json"
    assert main(["progression-guard", "--format", "json", "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["status"] == "pass"
    assert payload["metrics"]["quests"] == 656


def test_cli_fails_when_budget_is_exceeded(tmp_path) -> None:
    budget = load_progression_budget()
    strict_budget = replace(budget, maximum_depth=budget.maximum_depth - 1)
    path = tmp_path / "budget.json"
    path.write_text(json.dumps(strict_budget.__dict__ if hasattr(strict_budget, '__dict__') else {
        "minimum_quests": strict_budget.minimum_quests,
        "minimum_dependencies": strict_budget.minimum_dependencies,
        "maximum_depth": strict_budget.maximum_depth,
        "maximum_bottlenecks": strict_budget.maximum_bottlenecks,
        "maximum_direct_dependants": strict_budget.maximum_direct_dependants,
        "maximum_chapter_transitions": strict_budget.maximum_chapter_transitions,
    }))
    assert main(["progression-guard", str(path)]) == 1
