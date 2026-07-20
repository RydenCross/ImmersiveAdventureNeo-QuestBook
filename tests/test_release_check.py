from generator.release_check import run_release_check


def test_release_check_passes_and_matches_generated_content(tmp_path) -> None:
    report = run_release_check(tmp_path / "release")

    assert report.is_clean
    assert report.chapters == 13
    assert report.quests == 656
    assert report.generated_chapters == report.chapters
    assert report.generated_quests == report.quests
    assert report.validation_errors == 0
    assert report.validation_warnings == 0
    assert report.manifest_references == 1075
    assert report.manifest_unique_items == 459
    assert report.manifest_namespaces == 7


def test_release_check_report_formats_machine_readable_json(tmp_path) -> None:
    import json

    report = run_release_check(tmp_path / "release")
    payload = json.loads(report.format_json())

    assert payload["status"] == "pass"
    assert payload["is_clean"] is True
    assert payload["quests"] == 656
    assert payload["generated_quests"] == 656
