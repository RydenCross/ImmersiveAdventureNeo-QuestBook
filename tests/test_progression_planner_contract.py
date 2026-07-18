import json

from generator.progression_planner_contract import run_progression_planner_contract


def test_progression_planner_contract_is_clean() -> None:
    result = run_progression_planner_contract()
    assert result.is_clean
    assert result.blueprint_generated
    assert result.dependencies_preserved
    assert result.deterministic_output


def test_progression_planner_contract_json_is_machine_readable() -> None:
    payload = json.loads(run_progression_planner_contract().format_json())
    assert payload["status"] == "pass"
    assert payload["dangling_dependencies"] == []
