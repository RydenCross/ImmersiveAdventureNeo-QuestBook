from pathlib import Path

from generator.report_freshness import compare_report_payloads, run_report_freshness_guard


def test_compare_report_payloads_accepts_matching_json(tmp_path: Path) -> None:
    (tmp_path / "one.json").write_text('{"value": 1}\n', encoding="utf-8")
    result = compare_report_payloads(tmp_path, {"one.json": lambda: '{"value": 1}'})
    assert result.is_clean
    assert result.fresh_reports == ("one.json",)


def test_compare_report_payloads_detects_stale_report(tmp_path: Path) -> None:
    (tmp_path / "one.json").write_text('{"value": 1}\n', encoding="utf-8")
    result = compare_report_payloads(tmp_path, {"one.json": lambda: '{"value": 2}'})
    assert result.stale_reports == ("one.json",)
    assert not result.is_clean


def test_compare_report_payloads_detects_missing_and_invalid_reports(tmp_path: Path) -> None:
    (tmp_path / "invalid.json").write_text("not-json", encoding="utf-8")
    result = compare_report_payloads(
        tmp_path,
        {
            "invalid.json": lambda: "{}",
            "missing.json": lambda: "{}",
        },
    )
    assert result.invalid_reports == ("invalid.json",)
    assert result.missing_reports == ("missing.json",)


def test_report_freshness_formats_machine_readable_status(tmp_path: Path) -> None:
    (tmp_path / "one.json").write_text("{}", encoding="utf-8")
    result = compare_report_payloads(tmp_path, {"one.json": lambda: "{}"})
    assert '"status": "pass"' in result.format_json()
    assert "Report freshness guard: PASS" in result.format()


def test_checked_in_reports_are_fresh() -> None:
    assert run_report_freshness_guard().is_clean
