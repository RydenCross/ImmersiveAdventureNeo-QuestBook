from pathlib import Path

from generator.inventory_contract import run_test_inventory_contract


def test_repository_test_inventory_is_clean() -> None:
    result = run_test_inventory_contract()
    assert result.is_clean
    assert result.registered_audits == 64
    assert len(result.expected_test_files) == 64


def test_inventory_reports_missing_test_file(tmp_path: Path) -> None:
    result = run_test_inventory_contract(tmp_path)
    assert not result.is_clean
    assert result.missing_test_files


def test_inventory_json_is_machine_readable() -> None:
    assert '"status": "pass"' in run_test_inventory_contract().format_json()
