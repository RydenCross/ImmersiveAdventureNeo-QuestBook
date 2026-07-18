from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

DEFAULT_ROOT = Path(".")
DEFAULT_MAX_FILE_BYTES = 1_000_000

_REQUIRED_GITIGNORE_PATTERNS = (
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    ".ruff_cache/",
    ".venv/",
    ".quest-editor/",
    ".recovery/",
    "output/",
    "dist/",
    "build/",
    "*.egg-info/",
    ".env",
    "*.pem",
    "*.key",
)

_IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".quest-editor",
    ".recovery",
    "__pycache__",
}

_FORBIDDEN_DIRECTORY_NAMES = {
    "dist",
    "build",
}

_FORBIDDEN_FILE_NAMES = {
    ".DS_Store",
    ".coverage",
    ".env",
    "id_rsa",
    "id_ed25519",
}

_FORBIDDEN_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pem",
    ".key",
}


@dataclass(frozen=True, slots=True)
class RepositoryHygieneAudit:
    scanned_files: int
    missing_gitignore_patterns: tuple[str, ...]
    forbidden_paths: tuple[str, ...]
    secret_like_paths: tuple[str, ...]
    oversized_files: tuple[str, ...]
    max_file_bytes: int

    @property
    def is_clean(self) -> bool:
        return not any(
            (
                self.missing_gitignore_patterns,
                self.forbidden_paths,
                self.secret_like_paths,
                self.oversized_files,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "scanned_files": self.scanned_files,
            "max_file_bytes": self.max_file_bytes,
            "missing_gitignore_patterns": list(self.missing_gitignore_patterns),
            "forbidden_paths": list(self.forbidden_paths),
            "secret_like_paths": list(self.secret_like_paths),
            "oversized_files": list(self.oversized_files),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Repository hygiene audit: {'PASS' if self.is_clean else 'FAIL'}",
            f"Files scanned: {self.scanned_files}.",
            f"Missing .gitignore patterns: {len(self.missing_gitignore_patterns)}.",
            f"Forbidden paths: {len(self.forbidden_paths)}.",
            f"Secret-like paths: {len(self.secret_like_paths)}.",
            f"Oversized files: {len(self.oversized_files)}.",
        ]
        lines.extend(f"Missing ignore pattern: {item}" for item in self.missing_gitignore_patterns)
        lines.extend(f"Forbidden path: {item}" for item in self.forbidden_paths)
        lines.extend(f"Secret-like path: {item}" for item in self.secret_like_paths)
        lines.extend(f"Oversized file: {item}" for item in self.oversized_files)
        return "\n".join(lines)


def run_repository_hygiene_audit(
    root: Path = DEFAULT_ROOT,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> RepositoryHygieneAudit:
    root = root.resolve()
    gitignore_path = root / ".gitignore"
    try:
        ignore_lines = {
            line.strip()
            for line in gitignore_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
    except OSError:
        ignore_lines = set()

    missing_patterns = tuple(
        pattern for pattern in _REQUIRED_GITIGNORE_PATTERNS if pattern not in ignore_lines
    )
    forbidden: list[str] = []
    secret_like: list[str] = []
    oversized: list[str] = []
    scanned = 0

    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        parts = relative.parts
        if any(part in _IGNORED_DIRECTORY_NAMES for part in parts):
            continue

        if path.is_dir():
            if path.name in _FORBIDDEN_DIRECTORY_NAMES or path.name.endswith(".egg-info"):
                forbidden.append(relative.as_posix() + "/")
            continue

        if not path.is_file():
            continue
        if relative.as_posix() == "reports/repository-hygiene-audit.json":
            continue

        scanned += 1
        name = path.name
        lowered = name.lower()
        if name in _FORBIDDEN_FILE_NAMES or path.suffix.lower() in _FORBIDDEN_SUFFIXES:
            forbidden.append(relative.as_posix())
        if lowered.startswith(".env") or lowered in {"id_rsa", "id_ed25519"}:
            secret_like.append(relative.as_posix())
        if path.stat().st_size > max_file_bytes:
            oversized.append(f"{relative.as_posix()} ({path.stat().st_size} bytes)")

    return RepositoryHygieneAudit(
        scanned_files=scanned,
        missing_gitignore_patterns=missing_patterns,
        forbidden_paths=tuple(sorted(set(forbidden))),
        secret_like_paths=tuple(sorted(set(secret_like))),
        oversized_files=tuple(sorted(oversized)),
        max_file_bytes=max_file_bytes,
    )
