from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.build import build


@dataclass(frozen=True, slots=True)
class DeterminismAudit:
    file_count: int
    total_bytes: int
    tree_digest: str
    missing_from_second: tuple[str, ...]
    added_in_second: tuple[str, ...]
    changed_files: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.missing_from_second, self.added_in_second, self.changed_files))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
            "tree_digest": self.tree_digest,
            "missing_from_second": list(self.missing_from_second),
            "added_in_second": list(self.added_in_second),
            "changed_files": list(self.changed_files),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Build determinism audit: {'PASS' if self.is_clean else 'FAIL'}",
            f"Compared {self.file_count} generated files ({self.total_bytes} bytes).",
            f"Tree SHA-256: {self.tree_digest}",
            f"Missing from second build: {len(self.missing_from_second)}.",
            f"Added in second build: {len(self.added_in_second)}.",
            f"Changed files: {len(self.changed_files)}.",
        ]
        lines.extend(f"Missing: {path}" for path in self.missing_from_second)
        lines.extend(f"Added: {path}" for path in self.added_in_second)
        lines.extend(f"Changed: {path}" for path in self.changed_files)
        return "\n".join(lines)


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def compare_generated_trees(first: Path, second: Path) -> DeterminismAudit:
    first_files = _snapshot(first)
    second_files = _snapshot(second)
    first_names = set(first_files)
    second_names = set(second_files)
    shared = first_names & second_names

    missing = tuple(sorted(first_names - second_names))
    added = tuple(sorted(second_names - first_names))
    changed = tuple(sorted(path for path in shared if first_files[path] != second_files[path]))

    digest = sha256()
    for path in sorted(first_files):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(first_files[path])
        digest.update(b"\0")

    return DeterminismAudit(
        file_count=len(first_files),
        total_bytes=sum(len(value) for value in first_files.values()),
        tree_digest=digest.hexdigest(),
        missing_from_second=missing,
        added_in_second=added,
        changed_files=changed,
    )


def run_determinism_audit() -> DeterminismAudit:
    with TemporaryDirectory(prefix="quest-build-a-") as first_tmp, TemporaryDirectory(
        prefix="quest-build-b-"
    ) as second_tmp:
        first = build(Path(first_tmp), quiet=True)
        second = build(Path(second_tmp), quiet=True)
        return compare_generated_trees(first, second)
