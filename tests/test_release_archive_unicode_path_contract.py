from pathlib import Path
from zipfile import ZipFile, ZipInfo

from generator.release_archive_unicode_path_contract import (
    run_release_archive_unicode_path_contract,
    verify_release_archive_unicode_paths,
)


def test_repository_release_unicode_paths_are_clean() -> None:
    result = run_release_archive_unicode_path_contract()
    assert result.is_clean
    assert result.archive_entries > 0


def test_unicode_path_contract_detects_ambiguous_names(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr(ZipInfo("caf\u00e9.txt"), b"a")
        archive.writestr(ZipInfo("cafe\u0301.txt"), b"b")
        archive.writestr(ZipInfo("safe\u202efile.txt"), b"c")
        archive.writestr(ZipInfo("trail. "), b"d")
    result = verify_release_archive_unicode_paths(archive_path)
    assert not result.is_clean
    assert result.non_nfc_paths
    assert result.compatibility_collisions
    assert result.bidi_control_paths
    assert result.non_portable_segments
