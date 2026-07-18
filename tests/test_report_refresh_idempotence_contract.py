from pathlib import Path

from generator.report_refresh import refresh_reports
from generator.report_refresh_idempotence_contract import run_report_refresh_idempotence_contract


def test_report_refresh_idempotence_contract_is_clean() -> None:
    result = run_report_refresh_idempotence_contract()
    assert result.is_clean
    assert result.second_refresh_passes == 1
    assert result.files_changed == ()


def test_converged_refresh_is_a_noop(tmp_path: Path) -> None:
    renderers = {"report.json": lambda: '{"status":"pass","value":1}'}
    first = refresh_reports(tmp_path, renderers=renderers)
    before = (tmp_path / "report.json").stat().st_mtime_ns
    second = refresh_reports(tmp_path, renderers=renderers)
    after = (tmp_path / "report.json").stat().st_mtime_ns
    assert first.is_clean
    assert second.is_clean
    assert second.passes == 1
    assert second.changed_reports_last_pass == ()
    assert before == after


def test_idempotence_report_is_machine_readable() -> None:
    payload = run_report_refresh_idempotence_contract().to_dict()
    assert payload["status"] == "pass"
    assert payload["files_changed"] == []
