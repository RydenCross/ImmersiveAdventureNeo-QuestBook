import json

from generator.ftb_blueprint_exporter_contract import run_ftb_blueprint_exporter_contract


def test_ftb_blueprint_exporter_contract_is_clean() -> None:
    result = run_ftb_blueprint_exporter_contract()
    assert result.is_clean
    assert result.round_trip_valid
    assert result.dependencies_preserved
    assert result.deterministic_tree


def test_ftb_blueprint_exporter_contract_json_is_machine_readable() -> None:
    payload = json.loads(run_ftb_blueprint_exporter_contract().format_json())
    assert payload["status"] == "pass"
    assert payload["stale_files_removed"] is True
