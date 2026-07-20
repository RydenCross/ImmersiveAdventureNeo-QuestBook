import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from generator.release_archive_compression_contract import (
    run_release_archive_compression_contract,
    verify_release_archive_compression,
)


def test_release_archive_compression_contract_is_clean() -> None:
    result = run_release_archive_compression_contract()
    assert result.is_clean
    assert result.archive_entries > 0
    assert result.savings_ratio >= 0.05
    assert not result.stored_entries


def test_release_archive_compression_detects_stored_and_budget_failures() -> None:
    with TemporaryDirectory() as directory:
        archive_path = Path(directory) / "release.zip"
        with ZipFile(archive_path, "w") as archive:
            archive.writestr("stored.txt", "x" * 100, compress_type=ZIP_STORED)
            archive.writestr("large.txt", "y" * 200, compress_type=ZIP_DEFLATED)
        result = verify_release_archive_compression(
            archive_path,
            max_archive_bytes=1,
            max_entry_bytes=150,
            min_savings_ratio=0.99,
        )
        assert not result.is_clean
        assert result.stored_entries == ("stored.txt",)
        assert result.oversized_entries == ("large.txt",)
        assert result.archive_budget_exceeded
        assert result.savings_budget_missed


def test_release_archive_compression_json_is_machine_readable() -> None:
    payload = json.loads(run_release_archive_compression_contract().format_json())
    assert payload["status"] == "pass"
    assert payload["archive_entries"] > 0
