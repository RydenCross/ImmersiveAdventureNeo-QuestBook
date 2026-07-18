import json
from pathlib import Path

from generator.report_refresh import refresh_reports
from generator.report_refresh_contract import run_report_refresh_contract


def test_report_refresh_contract_is_clean() -> None:
    result = run_report_refresh_contract()
    assert result.is_clean
    assert result.missing_renderers == ()
    assert result.unexpected_renderers == ()


def test_refresh_reports_uses_requested_order(tmp_path: Path) -> None:
    renderers = {
        "b.json": lambda: '{"status":"pass","name":"b"}',
        "a.json": lambda: '{"status":"pass","name":"a"}',
    }
    result = refresh_reports(tmp_path, renderers=renderers, order=("a.json", "b.json"))
    assert result.is_clean
    assert result.refreshed_reports == ("a.json", "b.json")
    assert json.loads((tmp_path / "a.json").read_text())['name'] == "a"


def test_refresh_reports_rejects_invalid_json(tmp_path: Path) -> None:
    result = refresh_reports(tmp_path, renderers={"bad.json": lambda: "not json"})
    assert not result.is_clean
    assert result.failed_reports == ("bad.json",)
    assert not (tmp_path / "bad.json").exists()
