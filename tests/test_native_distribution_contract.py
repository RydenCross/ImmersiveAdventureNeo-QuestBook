from generator.native_distribution_contract import run_native_distribution_contract


def test_native_distribution_contract_passes() -> None:
    result = run_native_distribution_contract()
    assert result.is_clean, result.format()


def test_native_distribution_contract_json_status_matches() -> None:
    assert '"status": "pass"' in run_native_distribution_contract().format_json()
