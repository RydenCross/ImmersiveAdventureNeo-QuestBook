from generator.update_application_contract import run_update_application_contract


def test_update_application_contract() -> None:
    result = run_update_application_contract()
    assert result.is_clean, result.to_dict()
