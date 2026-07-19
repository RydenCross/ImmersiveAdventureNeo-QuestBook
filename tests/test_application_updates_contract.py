from generator.application_updates_contract import run_application_updates_contract


def test_application_updates_contract_passes() -> None:
    assert run_application_updates_contract().is_clean


def test_application_updates_contract_json_status_matches() -> None:
    assert '"status": "pass"' in run_application_updates_contract().format_json()
