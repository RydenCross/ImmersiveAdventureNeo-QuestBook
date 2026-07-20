import json

from generator.modpack_content_scanner_contract import run_modpack_content_scanner_contract


def test_modpack_content_scanner_contract_is_clean() -> None:
    result = run_modpack_content_scanner_contract()
    assert result.is_clean
    assert result.recipes_detected
    assert result.dependency_chain_detected
    assert result.corrupt_json_isolated


def test_modpack_content_scanner_contract_json_is_machine_readable() -> None:
    payload = json.loads(run_modpack_content_scanner_contract().format_json())
    assert payload["status"] == "pass"
    assert payload["jar_code_not_executed"] is True
