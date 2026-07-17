import json

from generator.cli import main
from generator.release_compare import compare_release_reports, load_release_report


def report(**overrides):
    payload = {
        "status": "pass",
        "is_clean": True,
        "chapters": 13,
        "quests": 656,
        "optional_quests": 223,
        "generated_chapters": 13,
        "generated_quests": 656,
        "validation_errors": 0,
        "validation_warnings": 0,
        "empty_descriptions": 0,
        "taskless_quests": 0,
        "duplicate_titles": 0,
        "manifest_references": 1075,
        "manifest_unique_items": 459,
        "manifest_namespaces": 7,
    }
    payload.update(overrides)
    return payload


def test_release_comparison_accepts_growth_without_quality_regressions() -> None:
    comparison = compare_release_reports(report(), report(quests=657, generated_quests=657))

    assert comparison.is_clean
    assert comparison.deltas["quests"] == 1
    assert comparison.regressions == ()


def test_release_comparison_flags_content_and_quality_regressions() -> None:
    comparison = compare_release_reports(
        report(),
        report(quests=655, generated_quests=655, validation_warnings=1),
    )

    assert not comparison.is_clean
    assert any("quests decreased" in issue for issue in comparison.regressions)
    assert any("validation warnings increased" in issue for issue in comparison.regressions)


def test_release_report_loader_validates_required_fields(tmp_path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({"quests": 1}), encoding="utf-8")

    try:
        load_release_report(path)
    except ValueError as exc:
        assert "missing field" in str(exc)
    else:
        raise AssertionError("Expected an invalid report to raise ValueError")


def test_release_compare_cli_writes_json_and_enforces_strict_mode(tmp_path) -> None:
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    output = tmp_path / "comparison.json"
    baseline.write_text(json.dumps(report()), encoding="utf-8")
    current.write_text(json.dumps(report(duplicate_titles=1)), encoding="utf-8")

    result = main(
        [
            "release-compare",
            str(baseline),
            str(current),
            "--format",
            "json",
            "--output",
            str(output),
            "--strict",
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert result == 1
    assert payload["status"] == "fail"
    assert payload["deltas"]["duplicate_titles"] == 1
