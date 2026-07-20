import json
from pathlib import Path

from generator.release_artifact_audit import run_release_artifact_audit


def test_repository_release_artifact_is_clean() -> None:
    result = run_release_artifact_audit()
    assert result.is_clean
    assert result.archive_entries > 0


def test_audit_detects_invalid_json_and_empty_files(tmp_path: Path) -> None:
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports/generated-output-manifest.json").write_text(
        '{"files": {}}', encoding="utf-8"
    )
    (tmp_path / "broken.json").write_text("{", encoding="utf-8")
    (tmp_path / "reports/empty.txt").write_bytes(b"")
    result = run_release_artifact_audit(tmp_path)
    assert "broken.json" in result.invalid_json_files
    assert "reports/empty.txt" in result.empty_files


def test_audit_detects_forbidden_entries(tmp_path: Path) -> None:
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports/generated-output-manifest.json").write_text(
        '{"files": {}}', encoding="utf-8"
    )
    cache = tmp_path / "package.egg-info"
    cache.mkdir()
    (cache / "PKG-INFO").write_text("metadata", encoding="utf-8")
    result = run_release_artifact_audit(tmp_path)
    assert result.is_clean  # ignored build metadata is excluded from the release artifact


def test_json_output_is_machine_readable() -> None:
    payload = json.loads(run_release_artifact_audit().format_json())
    assert payload["status"] == "pass"
    assert payload["archive_entries"] > 0
