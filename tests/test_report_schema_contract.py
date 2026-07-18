import json
from pathlib import Path

from generator.report_schema_contract import run_report_schema_contract


def test_repository_report_schemas_are_clean() -> None:
    result = run_report_schema_contract()
    assert result.is_clean
    assert result.checked_reports == 36


def test_schema_contract_detects_missing_and_invalid_reports(tmp_path: Path) -> None:
    (tmp_path / "release-guard.json").write_text("[]", encoding="utf-8")
    result = run_report_schema_contract(tmp_path)
    assert not result.is_clean
    assert "release-guard.json" in result.non_object_reports
    assert result.missing_reports


def test_schema_contract_detects_invalid_status(tmp_path: Path) -> None:
    from generator.audit_registry_contract import AUDIT_REGISTRY

    for registration in AUDIT_REGISTRY:
        if registration.report:
            (tmp_path / registration.report).write_text(
                json.dumps({"status": "unknown"}), encoding="utf-8"
            )
    result = run_report_schema_contract(tmp_path)
    assert not result.is_clean
    assert len(result.invalid_status) == result.checked_reports


def test_schema_contract_json_is_machine_readable() -> None:
    payload = json.loads(run_report_schema_contract().format_json())
    assert payload["status"] == "pass"
