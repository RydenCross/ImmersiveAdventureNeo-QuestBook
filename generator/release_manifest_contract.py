from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from generator.release_reproducibility_audit import _build_archive


@dataclass(frozen=True, slots=True)
class ReleaseManifestEntry:
    path: str
    bytes: int
    sha256: str

    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "bytes": self.bytes, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class ReleaseManifestContract:
    archive_entries: int
    archive_sha256: str
    tree_sha256: str
    manifest_entries: tuple[ReleaseManifestEntry, ...]
    missing_entries: tuple[str, ...]
    unexpected_entries: tuple[str, ...]
    size_mismatches: tuple[str, ...]
    digest_mismatches: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((
            self.missing_entries,
            self.unexpected_entries,
            self.size_mismatches,
            self.digest_mismatches,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "archive_entries": self.archive_entries,
            "archive_sha256": self.archive_sha256,
            "tree_sha256": self.tree_sha256,
            "manifest_entries": [entry.to_dict() for entry in self.manifest_entries],
            "missing_entries": list(self.missing_entries),
            "unexpected_entries": list(self.unexpected_entries),
            "size_mismatches": list(self.size_mismatches),
            "digest_mismatches": list(self.digest_mismatches),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Release manifest contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Archive entries: {self.archive_entries}.",
            f"Manifest entries: {len(self.manifest_entries)}.",
            f"Missing entries: {len(self.missing_entries)}.",
            f"Unexpected entries: {len(self.unexpected_entries)}.",
            f"Size mismatches: {len(self.size_mismatches)}.",
            f"Digest mismatches: {len(self.digest_mismatches)}.",
            f"Tree SHA-256: {self.tree_sha256}.",
        ))


def verify_release_manifest(
    archive_path: Path,
    manifest_entries: tuple[ReleaseManifestEntry, ...],
    archive_sha256: str,
    tree_sha256: str,
) -> ReleaseManifestContract:
    expected = {entry.path: entry for entry in manifest_entries}
    with ZipFile(archive_path) as archive:
        actual_names = set(archive.namelist())
        actual = {
            info.filename: (
                info.file_size,
                hashlib.sha256(archive.read(info.filename)).hexdigest(),
            )
            for info in archive.infolist()
        }
    expected_names = set(expected)
    common = expected_names & actual_names
    return ReleaseManifestContract(
        archive_entries=len(actual),
        archive_sha256=archive_sha256,
        tree_sha256=tree_sha256,
        manifest_entries=manifest_entries,
        missing_entries=tuple(sorted(expected_names - actual_names)),
        unexpected_entries=tuple(sorted(actual_names - expected_names)),
        size_mismatches=tuple(sorted(
            name for name in common if expected[name].bytes != actual[name][0]
        )),
        digest_mismatches=tuple(sorted(
            name for name in common if expected[name].sha256 != actual[name][1]
        )),
    )


def run_release_manifest_contract(root: Path = Path('.')) -> ReleaseManifestContract:
    root = root.resolve()
    with TemporaryDirectory() as temporary_directory:
        archive_path = Path(temporary_directory) / "release.zip"
        archive_sha256, entry_digests, tree_sha256 = _build_archive(root, archive_path)
        with ZipFile(archive_path) as archive:
            sizes = {info.filename: info.file_size for info in archive.infolist()}
        manifest_entries = tuple(
            ReleaseManifestEntry(path=name, bytes=sizes[name], sha256=digest)
            for name, digest in sorted(entry_digests.items())
        )
        return verify_release_manifest(
            archive_path,
            manifest_entries,
            archive_sha256,
            tree_sha256,
        )
