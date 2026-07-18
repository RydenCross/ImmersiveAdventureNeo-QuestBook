from __future__ import annotations

from generator.cli_output_contract import run_cli_output_contract


def test_cli_output_contract_is_clean() -> None:
    result = run_cli_output_contract()
    assert result.is_clean
    assert result.commands_checked == 52


def test_cli_output_contract_serializes_status() -> None:
    payload = run_cli_output_contract().to_dict()
    assert payload["status"] == "pass"
    assert payload["output_mismatches"] == []
