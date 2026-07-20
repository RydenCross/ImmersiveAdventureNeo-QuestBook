import json

from generator.report_provenance_contract import run_report_provenance_contract


def test_repository_report_provenance_is_clean() -> None:
    result = run_report_provenance_contract()
    assert result.is_clean
    assert result.tracked_reports == 62
    assert ("release-artifact-audit.json", "release-artifact-audit") in result.provenance


def test_provenance_json_is_machine_readable() -> None:
    payload = json.loads(run_report_provenance_contract().format_json())
    assert payload["status"] == "pass"
    assert all(entry["command"] and entry["report"] for entry in payload["provenance"])


def test_provenance_text_includes_reproduction_command() -> None:
    rendered = run_report_provenance_contract().format()
    assert "python -m generator release-artifact-audit" in rendered
