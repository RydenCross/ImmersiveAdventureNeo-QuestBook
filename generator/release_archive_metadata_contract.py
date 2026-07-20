from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from generator.release_reproducibility_audit import _build_archive

CANONICAL_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
CANONICAL_MODE = 0o100644


@dataclass(frozen=True, slots=True)
class ReleaseArchiveMetadataContract:
    archive_entries: int
    canonical_timestamps: int
    canonical_permissions: int
    canonical_compression: int
    ordered_entries: bool
    duplicate_entries: tuple[str, ...]
    unsafe_paths: tuple[str, ...]
    timestamp_mismatches: tuple[str, ...]
    permission_mismatches: tuple[str, ...]
    compression_mismatches: tuple[str, ...]
    encrypted_entries: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return (
            self.ordered_entries
            and not any((
                self.duplicate_entries,
                self.unsafe_paths,
                self.timestamp_mismatches,
                self.permission_mismatches,
                self.compression_mismatches,
                self.encrypted_entries,
            ))
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "archive_entries": self.archive_entries,
            "canonical_timestamps": self.canonical_timestamps,
            "canonical_permissions": self.canonical_permissions,
            "canonical_compression": self.canonical_compression,
            "ordered_entries": self.ordered_entries,
            "duplicate_entries": list(self.duplicate_entries),
            "unsafe_paths": list(self.unsafe_paths),
            "timestamp_mismatches": list(self.timestamp_mismatches),
            "permission_mismatches": list(self.permission_mismatches),
            "compression_mismatches": list(self.compression_mismatches),
            "encrypted_entries": list(self.encrypted_entries),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Release archive metadata contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Archive entries: {self.archive_entries}.",
            f"Canonical timestamps: {self.canonical_timestamps}.",
            f"Canonical permissions: {self.canonical_permissions}.",
            f"Canonical compression: {self.canonical_compression}.",
            f"Ordered entries: {'yes' if self.ordered_entries else 'no'}.",
            f"Duplicate entries: {len(self.duplicate_entries)}.",
            f"Unsafe paths: {len(self.unsafe_paths)}.",
            f"Encrypted entries: {len(self.encrypted_entries)}.",
        ))


def verify_release_archive_metadata(archive_path: Path) -> ReleaseArchiveMetadataContract:
    with ZipFile(archive_path) as archive:
        infos = archive.infolist()
    names = [info.filename for info in infos]
    duplicates = tuple(sorted({name for name in names if names.count(name) > 1}))
    unsafe = tuple(sorted(
        name for name in names
        if name.startswith(("/", "\\"))
        or "\\" in name
        or any(part in {"", ".", ".."} for part in PurePosixPath(name).parts)
    ))
    timestamp_mismatches = tuple(
        info.filename for info in infos if info.date_time != CANONICAL_TIMESTAMP
    )
    permission_mismatches = tuple(
        info.filename for info in infos
        if info.create_system != 3 or (info.external_attr >> 16) != CANONICAL_MODE
    )
    compression_mismatches = tuple(
        info.filename for info in infos if info.compress_type != ZIP_DEFLATED
    )
    encrypted = tuple(info.filename for info in infos if info.flag_bits & 0x1)
    return ReleaseArchiveMetadataContract(
        archive_entries=len(infos),
        canonical_timestamps=len(infos) - len(timestamp_mismatches),
        canonical_permissions=len(infos) - len(permission_mismatches),
        canonical_compression=len(infos) - len(compression_mismatches),
        ordered_entries=names == sorted(names),
        duplicate_entries=duplicates,
        unsafe_paths=unsafe,
        timestamp_mismatches=timestamp_mismatches,
        permission_mismatches=permission_mismatches,
        compression_mismatches=compression_mismatches,
        encrypted_entries=encrypted,
    )


def run_release_archive_metadata_contract(
    root: Path = Path('.'),
) -> ReleaseArchiveMetadataContract:
    root = root.resolve()
    with TemporaryDirectory() as directory:
        archive_path = Path(directory) / "release.zip"
        _build_archive(root, archive_path)
        return verify_release_archive_metadata(archive_path)
