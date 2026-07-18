import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from generator.release_archive_metadata_contract import (
    run_release_archive_metadata_contract,
    verify_release_archive_metadata,
)


def test_release_archive_metadata_contract_is_clean() -> None:
    result = run_release_archive_metadata_contract()
    assert result.is_clean
    assert result.archive_entries == result.canonical_timestamps
    assert result.archive_entries == result.canonical_permissions
    assert result.archive_entries == result.canonical_compression
    assert result.ordered_entries


def test_release_archive_metadata_detects_noncanonical_entry() -> None:
    with TemporaryDirectory() as directory:
        archive_path = Path(directory) / "release.zip"
        with ZipFile(archive_path, "w") as archive:
            archive.writestr("../unsafe.txt", "unsafe")
        result = verify_release_archive_metadata(archive_path)
        assert not result.is_clean
        assert result.unsafe_paths == ("../unsafe.txt",)
        assert result.timestamp_mismatches
        assert result.permission_mismatches
        assert result.compression_mismatches


def test_release_archive_metadata_json_is_machine_readable() -> None:
    payload = json.loads(run_release_archive_metadata_contract().format_json())
    assert payload["status"] == "pass"
    assert payload["ordered_entries"] is True
