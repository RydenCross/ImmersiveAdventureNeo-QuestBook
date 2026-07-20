import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from generator.release_manifest_contract import (
    ReleaseManifestEntry,
    run_release_manifest_contract,
    verify_release_manifest,
)


def test_release_manifest_contract_is_clean() -> None:
    result = run_release_manifest_contract()
    assert result.is_clean
    assert result.archive_entries == len(result.manifest_entries)
    assert not result.missing_entries
    assert not result.unexpected_entries
    assert not result.size_mismatches
    assert not result.digest_mismatches


def test_release_manifest_detects_digest_mismatch() -> None:
    with TemporaryDirectory() as directory:
        archive_path = Path(directory) / "release.zip"
        with ZipFile(archive_path, "w") as archive:
            archive.writestr("example.txt", "actual")
        result = verify_release_manifest(
            archive_path,
            (ReleaseManifestEntry("example.txt", 6, "0" * 64),),
            "1" * 64,
            "2" * 64,
        )
        assert not result.is_clean
        assert result.digest_mismatches == ("example.txt",)


def test_release_manifest_json_is_machine_readable() -> None:
    payload = json.loads(run_release_manifest_contract().format_json())
    assert payload["status"] == "pass"
    assert payload["archive_entries"] == len(payload["manifest_entries"])
    assert all(len(entry["sha256"]) == 64 for entry in payload["manifest_entries"])
