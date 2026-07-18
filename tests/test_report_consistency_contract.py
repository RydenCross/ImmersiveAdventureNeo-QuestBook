import json
from pathlib import Path

from generator.audit_registry_contract import AUDIT_REGISTRY
from generator.report_consistency_contract import run_report_consistency_contract


def _write_reports(directory: Path, payload: dict[str, object]) -> None:
    for item in AUDIT_REGISTRY:
        if item.report:
            (directory / item.report).write_text(json.dumps(payload), encoding="utf-8")


def test_repository_report_consistency_is_clean() -> None:
    result = run_report_consistency_contract()
    assert result.is_clean
    assert result.checked_reports == 24


def test_contract_detects_pass_report_with_defects(tmp_path: Path) -> None:
    _write_reports(tmp_path, {"status": "pass", "missing_items": ["x"]})
    result = run_report_consistency_contract(tmp_path)
    assert not result.is_clean
    assert len(result.inconsistent_status) == result.checked_reports


def test_contract_detects_fail_report_without_defects(tmp_path: Path) -> None:
    _write_reports(tmp_path, {"status": "fail", "missing_items": []})
    result = run_report_consistency_contract(tmp_path)
    assert not result.is_clean
    assert len(result.inconsistent_status) == result.checked_reports


def test_contract_json_is_machine_readable() -> None:
    payload = json.loads(run_report_consistency_contract().format_json())
    assert payload["status"] == "pass"
