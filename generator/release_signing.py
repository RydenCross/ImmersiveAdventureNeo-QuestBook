from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import subprocess
from typing import Callable, Sequence

_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _regular_file(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.is_symlink() or not resolved.is_file():
        raise ValueError(f"artifact must be a regular file: {resolved}")
    return resolved


def _portable_name(name: str) -> str:
    if not name or name in {".", ".."}:
        raise ValueError("artifact filename must be portable")
    if PurePosixPath(name).name != name or PureWindowsPath(name).name != name:
        raise ValueError("artifact filename must not contain path components")
    if any(ord(ch) < 32 for ch in name):
        raise ValueError("artifact filename contains a control character")
    return name


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with _regular_file(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_checksum_manifest(artifacts: Sequence[Path]) -> str:
    selected = sorted((_regular_file(path) for path in artifacts), key=lambda p: p.name.casefold())
    if not selected:
        raise ValueError("at least one artifact is required")
    names = [_portable_name(path.name) for path in selected]
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError("artifact filenames must be unique")
    return "".join(f"{sha256_file(path)}  {path.name}\n" for path in selected)


def write_checksum_manifest(path: Path, artifacts: Sequence[Path]) -> Path:
    target = path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(create_checksum_manifest(artifacts), encoding="utf-8", newline="\n")
    temporary.replace(target)
    return target


def verify_checksum_manifest(manifest: Path, artifact_directory: Path) -> tuple[str, ...]:
    source = _regular_file(manifest)
    root = artifact_directory.expanduser().resolve()
    errors: list[str] = []
    seen: set[str] = set()
    for number, raw in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not raw:
            continue
        if "  " not in raw:
            errors.append(f"line {number}: invalid checksum record")
            continue
        digest, name = raw.split("  ", 1)
        try:
            _portable_name(name)
        except ValueError as exc:
            errors.append(f"line {number}: {exc}")
            continue
        if not _SHA256.fullmatch(digest):
            errors.append(f"line {number}: invalid SHA-256 digest")
            continue
        key = name.casefold()
        if key in seen:
            errors.append(f"line {number}: duplicate artifact: {name}")
            continue
        seen.add(key)
        candidate = root / name
        try:
            actual = sha256_file(candidate)
        except ValueError:
            errors.append(f"missing or unsafe artifact: {name}")
            continue
        if actual != digest:
            errors.append(f"checksum mismatch: {name}")
    if not seen:
        errors.append("checksum manifest contains no artifacts")
    return tuple(errors)


@dataclass(frozen=True, slots=True)
class AttestationVerificationPlan:
    repository: str
    commands: tuple[tuple[str, ...], ...]

    def format(self) -> str:
        return "\n".join(" ".join(command) for command in self.commands)


def create_attestation_verification_plan(
    artifacts: Sequence[Path], *, repository: str
) -> AttestationVerificationPlan:
    if not _REPOSITORY.fullmatch(repository):
        raise ValueError("repository must use owner/name syntax")
    selected = sorted((_regular_file(path) for path in artifacts), key=lambda p: p.name.casefold())
    if not selected:
        raise ValueError("at least one artifact is required")
    commands = tuple(("gh", "attestation", "verify", str(path), "--repo", repository) for path in selected)
    return AttestationVerificationPlan(repository=repository, commands=commands)


def verify_github_attestations(
    artifacts: Sequence[Path],
    *,
    repository: str,
    execute: bool = False,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> AttestationVerificationPlan:
    plan = create_attestation_verification_plan(artifacts, repository=repository)
    if execute:
        for command in plan.commands:
            completed = runner(command, check=False, capture_output=True, text=True)
            if completed.returncode != 0:
                detail = (completed.stderr or completed.stdout or "verification failed").strip()
                raise RuntimeError(detail)
    return plan
