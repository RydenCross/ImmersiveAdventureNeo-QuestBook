from generator.desktop_launcher_contract import run_desktop_launcher_contract


def test_desktop_launcher_contract_passes() -> None:
    result = run_desktop_launcher_contract()
    assert result.is_clean, result.format()


def test_desktop_launcher_contract_json_status_matches() -> None:
    result = run_desktop_launcher_contract()
    assert '"status": "pass"' in result.format_json()
