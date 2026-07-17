import json
from pathlib import Path
import zipfile

from generator.release_reproducibility_audit import (
    compare_release_archives,
    run_release_reproducibility_audit,
)


def _zip(path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)


def test_repository_release_is_reproducible() -> None:
    result = run_release_reproducibility_audit()
    assert result.is_clean
    assert result.archive_entries > 0
    assert result.first_tree_sha256 == result.second_tree_sha256


def test_comparison_detects_changed_entries(tmp_path: Path) -> None:
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    _zip(first, {"file.txt": b"one"})
    _zip(second, {"file.txt": b"two"})
    result = compare_release_archives(first, second)
    assert result.changed_entries == ("file.txt",)


def test_comparison_detects_missing_and_unexpected_entries(tmp_path: Path) -> None:
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    _zip(first, {"old.txt": b"same"})
    _zip(second, {"new.txt": b"same"})
    result = compare_release_archives(first, second)
    assert result.missing_entries == ("old.txt",)
    assert result.unexpected_entries == ("new.txt",)


def test_json_output_is_machine_readable() -> None:
    payload = json.loads(run_release_reproducibility_audit().format_json())
    assert payload["status"] == "pass"
    assert payload["first_tree_sha256"] == payload["second_tree_sha256"]
