from generator.cli_exit_code_contract import run_cli_exit_code_contract


def test_cli_exit_code_contract_is_clean() -> None:
    result = run_cli_exit_code_contract()
    assert result.is_clean
    assert result.commands_checked == 47


def test_cli_exit_code_contract_serializes_status() -> None:
    payload = run_cli_exit_code_contract().to_dict()
    assert payload["status"] == "pass"
    assert payload["failing_exit_mismatches"] == []
