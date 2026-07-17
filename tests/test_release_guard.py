import json

import pytest

from generator.cli import main
from generator.release_check import ReleaseCheckReport
from generator.release_guard import refresh_release_baseline, run_release_guard


def clean_report(**overrides) -> ReleaseCheckReport:
    values = {
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
    values.update(overrides)
    return ReleaseCheckReport(**values)


def test_release_guard_passes_against_matching_baseline(tmp_path, monkeypatch) -> None:
    baseline = tmp_path / "release-baseline.json"
    baseline.write_text(clean_report().format_json(), encoding="utf-8")
    monkeypatch.setattr("generator.release_guard.run_release_check", lambda output=None: clean_report())

    result = run_release_guard(baseline)

    assert result.is_clean
    assert "Release guard: PASS" in result.format()


def test_release_guard_detects_regression(tmp_path, monkeypatch) -> None:
    baseline = tmp_path / "release-baseline.json"
    baseline.write_text(clean_report().format_json(), encoding="utf-8")
    monkeypatch.setattr(
        "generator.release_guard.run_release_check",
        lambda output=None: clean_report(quests=655, generated_quests=655),
    )

    result = run_release_guard(baseline)

    assert not result.is_clean
    assert any("quests decreased" in item for item in result.comparison.regressions)


def test_baseline_refresh_creates_parent_directories(tmp_path, monkeypatch) -> None:
    destination = tmp_path / "nested" / "release-baseline.json"
    monkeypatch.setattr("generator.release_guard.run_release_check", lambda output=None: clean_report())

    report = refresh_release_baseline(destination)

    assert report.is_clean
    assert json.loads(destination.read_text(encoding="utf-8"))["quests"] == 656


def test_baseline_refresh_refuses_failed_release(tmp_path, monkeypatch) -> None:
    destination = tmp_path / "release-baseline.json"
    monkeypatch.setattr(
        "generator.release_guard.run_release_check",
        lambda output=None: clean_report(validation_errors=1),
    )

    with pytest.raises(ValueError, match="Refusing"):
        refresh_release_baseline(destination)

    assert not destination.exists()


def test_release_guard_cli_writes_json(tmp_path, monkeypatch) -> None:
    baseline = tmp_path / "release-baseline.json"
    output = tmp_path / "release-guard.json"
    baseline.write_text(clean_report().format_json(), encoding="utf-8")
    monkeypatch.setattr("generator.release_guard.run_release_check", lambda output=None: clean_report())

    result = main(["release-guard", str(baseline), "--format", "json", "--output", str(output)])

    assert result == 0
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "pass"
