from generator.desktop_packages_contract import run_desktop_packages_contract


def test_desktop_packages_contract_passes() -> None:
    result = run_desktop_packages_contract()
    assert result.is_clean


def test_desktop_packages_contract_json_status_matches() -> None:
    assert '"status": "pass"' in run_desktop_packages_contract().format_json()
