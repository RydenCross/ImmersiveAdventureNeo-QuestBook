from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile

from generator.release_artifact_audit import DEFAULT_ROOT, _release_files


@dataclass(frozen=True, slots=True)
class ReleaseReproducibilityAudit:
    archive_entries: int
    first_archive_sha256: str
    second_archive_sha256: str
    first_tree_sha256: str
    second_tree_sha256: str
    missing_entries: tuple[str, ...]
    unexpected_entries: tuple[str, ...]
    changed_entries: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.missing_entries, self.unexpected_entries, self.changed_entries))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "archive_entries": self.archive_entries,
            "first_archive_sha256": self.first_archive_sha256,
            "second_archive_sha256": self.second_archive_sha256,
            "first_tree_sha256": self.first_tree_sha256,
            "second_tree_sha256": self.second_tree_sha256,
            "missing_entries": list(self.missing_entries),
            "unexpected_entries": list(self.unexpected_entries),
            "changed_entries": list(self.changed_entries),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Release reproducibility audit: {'PASS' if self.is_clean else 'FAIL'}",
                f"Archive entries: {self.archive_entries}.",
                f"Missing entries: {len(self.missing_entries)}.",
                f"Unexpected entries: {len(self.unexpected_entries)}.",
                f"Changed entries: {len(self.changed_entries)}.",
                f"First tree SHA-256: {self.first_tree_sha256}.",
                f"Second tree SHA-256: {self.second_tree_sha256}.",
            )
        )


def _build_archive(root: Path, destination: Path) -> tuple[str, dict[str, str], str]:
    files = _release_files(root)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(root).as_posix())

    archive_digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    entry_digests: dict[str, str] = {}
    with zipfile.ZipFile(destination) as archive:
        for name in sorted(archive.namelist()):
            entry_digests[name] = hashlib.sha256(archive.read(name)).hexdigest()

    tree_hash = hashlib.sha256()
    for name, digest in sorted(entry_digests.items()):
        tree_hash.update(name.encode("utf-8"))
        tree_hash.update(b"\0")
        tree_hash.update(digest.encode("ascii"))
        tree_hash.update(b"\n")
    return archive_digest, entry_digests, tree_hash.hexdigest()


def compare_release_archives(first: Path, second: Path) -> ReleaseReproducibilityAudit:
    def read(path: Path) -> tuple[str, dict[str, str], str]:
        archive_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries: dict[str, str] = {}
        with zipfile.ZipFile(path) as archive:
            for name in sorted(archive.namelist()):
                entries[name] = hashlib.sha256(archive.read(name)).hexdigest()
        tree_hash = hashlib.sha256()
        for name, digest in sorted(entries.items()):
            tree_hash.update(name.encode("utf-8"))
            tree_hash.update(b"\0")
            tree_hash.update(digest.encode("ascii"))
            tree_hash.update(b"\n")
        return archive_digest, entries, tree_hash.hexdigest()

    first_archive, first_entries, first_tree = read(first)
    second_archive, second_entries, second_tree = read(second)
    first_names = set(first_entries)
    second_names = set(second_entries)
    changed = tuple(
        sorted(
            name
            for name in first_names & second_names
            if first_entries[name] != second_entries[name]
        )
    )
    return ReleaseReproducibilityAudit(
        archive_entries=len(first_entries),
        first_archive_sha256=first_archive,
        second_archive_sha256=second_archive,
        first_tree_sha256=first_tree,
        second_tree_sha256=second_tree,
        missing_entries=tuple(sorted(first_names - second_names)),
        unexpected_entries=tuple(sorted(second_names - first_names)),
        changed_entries=changed,
    )


def run_release_reproducibility_audit(root: Path = DEFAULT_ROOT) -> ReleaseReproducibilityAudit:
    root = root.resolve()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        first = temp / "first.zip"
        second = temp / "second.zip"
        _build_archive(root, first)
        _build_archive(root, second)
        return compare_release_archives(first, second)
