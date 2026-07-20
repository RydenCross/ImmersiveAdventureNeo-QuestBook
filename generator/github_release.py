from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Callable, Sequence

_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_TAG = re.compile(r"^v?[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$")


@dataclass(frozen=True, slots=True)
class ReleaseAsset:
    path: str
    filename: str
    size_bytes: int
    sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class GitHubReleasePlan:
    repository: str
    tag: str
    title: str
    notes_file: str
    prerelease: bool
    draft: bool
    assets: tuple[ReleaseAsset, ...]
    command: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return bool(self.repository and self.tag and self.assets)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "repository": self.repository,
            "tag": self.tag,
            "title": self.title,
            "notes_file": self.notes_file,
            "prerelease": self.prerelease,
            "draft": self.draft,
            "assets": [asset.to_dict() for asset in self.assets],
            "command": list(self.command),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True, slots=True)
class GitHubReleasePublish:
    plan: GitHubReleasePlan
    executed: bool
    return_code: int | None
    errors: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return self.plan.is_clean and not self.errors and (not self.executed or self.return_code == 0)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "executed": self.executed,
            "return_code": self.return_code,
            "errors": list(self.errors),
            "plan": self.plan.to_dict(),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _asset(path: Path) -> ReleaseAsset:
    resolved = path.expanduser().resolve()
    if not resolved.is_file() or resolved.is_symlink():
        raise ValueError(f"release asset must be a regular file: {resolved}")
    if resolved.name in (".", "..") or "/" in resolved.name or "\\" in resolved.name:
        raise ValueError(f"unsafe release asset filename: {resolved.name}")
    return ReleaseAsset(
        path=str(resolved),
        filename=resolved.name,
        size_bytes=resolved.stat().st_size,
        sha256=_digest(resolved),
    )


def create_github_release_plan(
    repository: str,
    tag: str,
    assets: Sequence[Path],
    *,
    notes_file: Path,
    title: str | None = None,
    prerelease: bool = False,
    draft: bool = False,
) -> GitHubReleasePlan:
    if not _REPOSITORY.fullmatch(repository):
        raise ValueError("repository must use owner/name format")
    if not _TAG.fullmatch(tag):
        raise ValueError("tag must be a semantic version such as v1.2.3")
    notes = notes_file.expanduser().resolve()
    if not notes.is_file() or notes.is_symlink():
        raise ValueError(f"release notes must be a regular file: {notes}")
    selected = tuple(sorted((_asset(path) for path in assets), key=lambda item: item.filename.casefold()))
    if not selected:
        raise ValueError("at least one release asset is required")
    names = [item.filename.casefold() for item in selected]
    if len(names) != len(set(names)):
        raise ValueError("release asset filenames must be unique")
    release_title = title or f"FTB Quest Maker {tag}"
    command = [
        "gh", "release", "create", tag,
        "--repo", repository,
        "--title", release_title,
        "--notes-file", str(notes),
        "--verify-tag",
    ]
    if prerelease:
        command.append("--prerelease")
    if draft:
        command.append("--draft")
    command.extend(item.path for item in selected)
    return GitHubReleasePlan(
        repository=repository,
        tag=tag,
        title=release_title,
        notes_file=str(notes),
        prerelease=prerelease,
        draft=draft,
        assets=selected,
        command=tuple(command),
    )


def publish_github_release(
    plan: GitHubReleasePlan,
    *,
    execute: bool = False,
    runner: Callable[[Sequence[str]], int] | None = None,
) -> GitHubReleasePublish:
    if not execute:
        return GitHubReleasePublish(plan=plan, executed=False, return_code=None)
    selected_runner = runner or (lambda command: subprocess.run(command, check=False).returncode)
    try:
        code = int(selected_runner(plan.command))
    except (OSError, TypeError, ValueError) as exc:
        return GitHubReleasePublish(plan=plan, executed=True, return_code=None, errors=(str(exc),))
    errors = () if code == 0 else (f"gh release create exited with status {code}",)
    return GitHubReleasePublish(plan=plan, executed=True, return_code=code, errors=errors)
