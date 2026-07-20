from generator.editor_model_contract import run_editor_model_contract


def test_editor_model_contract_passes() -> None:
    result = run_editor_model_contract()
    assert result.is_clean, result.format()
