import json

from generator.release_report_finalization_contract import run_release_report_finalization_contract


def test_release_report_finalization_contract_is_clean() -> None:
    result = run_release_report_finalization_contract()
    assert result.is_clean
    assert result.archive_reports == (
        "release-artifact-audit.json",
        "release-reproducibility-audit.json",
    )
    assert not result.missing_archive_reports
    assert not result.archive_reports_not_final
    assert not result.final_archive_reports_changed


def test_release_report_finalization_report_is_machine_readable() -> None:
    result = run_release_report_finalization_contract()
    payload = json.loads(result.format_json())
    assert payload["status"] == "pass"
    assert payload["refresh_converged"] is True
