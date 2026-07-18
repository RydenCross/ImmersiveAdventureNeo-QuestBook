from generator.editor_service_contract import run_editor_service_contract


def test_editor_service_contract_is_clean() -> None:
    result = run_editor_service_contract()
    assert result.is_clean
    assert result.http_round_trip
    assert result.workspace_escape_rejected
