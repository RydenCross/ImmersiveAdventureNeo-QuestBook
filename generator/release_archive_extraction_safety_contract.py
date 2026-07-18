from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import posixpath
import stat
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from generator.release_reproducibility_audit import _build_archive


@dataclass(frozen=True, slots=True)
class ReleaseArchiveExtractionSafetyContract:
    archive_entries: int
    unsafe_paths: tuple[str, ...]
    normalized_collisions: tuple[str, ...]
    casefold_collisions: tuple[str, ...]
    symlink_entries: tuple[str, ...]
    special_file_entries: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((
            self.unsafe_paths,
            self.normalized_collisions,
            self.casefold_collisions,
            self.symlink_entries,
            self.special_file_entries,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "archive_entries": self.archive_entries,
            "unsafe_paths": list(self.unsafe_paths),
            "normalized_collisions": list(self.normalized_collisions),
            "casefold_collisions": list(self.casefold_collisions),
            "symlink_entries": list(self.symlink_entries),
            "special_file_entries": list(self.special_file_entries),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Release archive extraction safety contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Archive entries: {self.archive_entries}.",
            f"Unsafe paths: {len(self.unsafe_paths)}.",
            f"Normalized path collisions: {len(self.normalized_collisions)}.",
            f"Case-folding collisions: {len(self.casefold_collisions)}.",
            f"Symlink entries: {len(self.symlink_entries)}.",
            f"Special-file entries: {len(self.special_file_entries)}.",
        ))


def _collision_descriptions(groups: dict[str, list[str]]) -> tuple[str, ...]:
    return tuple(sorted(
        f"{key}: {', '.join(sorted(values))}"
        for key, values in groups.items()
        if len(values) > 1
    ))


def verify_release_archive_extraction_safety(archive_path: Path) -> ReleaseArchiveExtractionSafetyContract:
    unsafe: list[str] = []
    normalized: dict[str, list[str]] = {}
    casefolded: dict[str, list[str]] = {}
    symlinks: list[str] = []
    special: list[str] = []

    with ZipFile(archive_path) as archive:
        infos = archive.infolist()
        for info in infos:
            name = info.filename
            pure = PurePosixPath(name)
            normalized_name = posixpath.normpath(name)
            if (
                not name
                or name.startswith(("/", "\\"))
                or "\\" in name
                or pure.is_absolute()
                or ".." in pure.parts
                or normalized_name in (".", "..")
                or normalized_name.startswith("../")
                or ":" in pure.parts[0]
            ):
                unsafe.append(name)

            normalized.setdefault(normalized_name, []).append(name)
            casefolded.setdefault(normalized_name.casefold(), []).append(name)

            mode = (info.external_attr >> 16) & 0xFFFF
            file_type = stat.S_IFMT(mode)
            if file_type == stat.S_IFLNK:
                symlinks.append(name)
            elif file_type not in (0, stat.S_IFREG, stat.S_IFDIR):
                special.append(name)

    return ReleaseArchiveExtractionSafetyContract(
        archive_entries=len(infos),
        unsafe_paths=tuple(sorted(set(unsafe))),
        normalized_collisions=_collision_descriptions(normalized),
        casefold_collisions=_collision_descriptions(casefolded),
        symlink_entries=tuple(sorted(symlinks)),
        special_file_entries=tuple(sorted(special)),
    )


def run_release_archive_extraction_safety_contract() -> ReleaseArchiveExtractionSafetyContract:
    with TemporaryDirectory() as temporary_directory:
        archive_path = Path(temporary_directory) / "release.zip"
        _build_archive(Path.cwd(), archive_path)
        return verify_release_archive_extraction_safety(archive_path)
