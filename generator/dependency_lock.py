from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable

_LOCK_LINE = re.compile(
    r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)==(?P<version>[^\s]+)"
    r"(?:\s+--hash=sha256:(?P<hash>[0-9a-f]{64}))+$"
)
_HASH = re.compile(r"--hash=sha256:([0-9a-f]{64})")


@dataclass(frozen=True, slots=True)
class LockedDependency:
    name: str
    version: str
    hashes: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "version": self.version, "hashes": list(self.hashes)}


@dataclass(frozen=True, slots=True)
class DependencyLockResult:
    dependencies: tuple[LockedDependency, ...]
    duplicate_names: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return bool(self.dependencies) and not self.duplicate_names

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "dependency_count": len(self.dependencies),
            "duplicate_names": list(self.duplicate_names),
            "dependencies": [item.to_dict() for item in self.dependencies],
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Dependency lock policy: {'PASS' if self.is_clean else 'FAIL'}",
                f"Locked dependencies: {len(self.dependencies)}.",
                f"Duplicate package names: {len(self.duplicate_names)}.",
            )
        )


def parse_hashed_lock(path: Path) -> DependencyLockResult:
    source = path.expanduser().resolve()
    items: list[LockedDependency] = []
    seen: dict[str, int] = {}
    for line_number, raw in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _LOCK_LINE.fullmatch(line)
        if match is None:
            raise ValueError(
                f"{source.name}:{line_number}: entries must be exact pins with sha256 hashes"
            )
        hashes = tuple(sorted(set(_HASH.findall(line))))
        if not hashes:
            raise ValueError(f"{source.name}:{line_number}: at least one sha256 hash is required")
        name = match.group("name")
        key = name.casefold().replace("_", "-")
        seen[key] = seen.get(key, 0) + 1
        items.append(LockedDependency(name, match.group("version"), hashes))
    ordered = tuple(sorted(items, key=lambda item: (item.name.casefold(), item.version)))
    duplicates = tuple(sorted(key for key, count in seen.items() if count > 1))
    return DependencyLockResult(ordered, duplicates)


def lock_digest(path: Path) -> str:
    source = path.expanduser().resolve()
    return hashlib.sha256(source.read_bytes()).hexdigest()


def reproducible_install_plan(
    path: Path, *, python_executable: str = "python"
) -> tuple[str, ...]:
    result = parse_hashed_lock(path)
    if not result.is_clean:
        raise ValueError("dependency lock contains duplicate package names")
    source = path.expanduser().resolve()
    return (
        python_executable,
        "-m",
        "pip",
        "install",
        "--require-hashes",
        "--no-deps",
        "--only-binary=:all:",
        "-r",
        str(source),
    )


def write_lock_manifest(path: Path, output: Path) -> Path:
    source = path.expanduser().resolve()
    result = parse_hashed_lock(source)
    if not result.is_clean:
        raise ValueError("dependency lock is not clean")
    target = output.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    payload = {
        "schema_version": 1,
        "lock_file": source.name,
        "sha256": lock_digest(source),
        "dependency_count": len(result.dependencies),
        "dependencies": [item.to_dict() for item in result.dependencies],
    }
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(target)
    return target
