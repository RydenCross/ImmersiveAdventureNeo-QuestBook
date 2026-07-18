from __future__ import annotations

import json
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZipInfo

from generator.release_archive_extraction_safety_contract import (
    run_release_archive_extraction_safety_contract,
    verify_release_archive_extraction_safety,
)


def test_release_archive_extraction_safety_contract_is_clean() -> None:
    result = run_release_archive_extraction_safety_contract()
    assert result.is_clean
    assert result.archive_entries > 0


def test_release_archive_extraction_safety_detects_unsafe_and_colliding_entries() -> None:
    with TemporaryDirectory() as temporary_directory:
        archive_path = Path(temporary_directory) / "unsafe.zip"
        with ZipFile(archive_path, "w") as archive:
            archive.writestr("../escape.txt", "x")
            archive.writestr("Folder/File.txt", "a")
            archive.writestr("folder/file.txt", "b")
            link = ZipInfo("link")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(link, "target")
        result = verify_release_archive_extraction_safety(archive_path)
    assert not result.is_clean
    assert "../escape.txt" in result.unsafe_paths
    assert result.casefold_collisions
    assert result.symlink_entries == ("link",)


def test_release_archive_extraction_safety_json_is_machine_readable() -> None:
    payload = json.loads(run_release_archive_extraction_safety_contract().format_json())
    assert payload["status"] == "pass"
    assert payload["unsafe_paths"] == []
