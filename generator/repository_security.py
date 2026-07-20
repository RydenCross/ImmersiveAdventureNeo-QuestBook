from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b")),
    ("github-fine-grained-token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
)
_DEFAULT_EXCLUDED_PARTS = {".git", ".pytest_cache", "__pycache__", ".ruff_cache", ".mypy_cache"}
_TEXT_SUFFIXES = {
    ".cfg", ".ini", ".json", ".jsonl", ".md", ".py", ".rst", ".sh", ".toml", ".txt", ".yaml", ".yml"
}


@dataclass(frozen=True, slots=True)
class SecretFinding:
    path: str
    line: int
    kind: str

    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "line": self.line, "kind": self.kind}


@dataclass(frozen=True, slots=True)
class RepositorySecurityResult:
    scanned_files: int
    findings: tuple[SecretFinding, ...]
    workflow_errors: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.findings and not self.workflow_errors

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "scanned_files": self.scanned_files,
            "finding_count": len(self.findings),
            "findings": [item.to_dict() for item in self.findings],
            "workflow_errors": list(self.workflow_errors),
        }

    def format(self) -> str:
        lines = [
            f"Repository secret scanning and workflow permission policy: {'PASS' if self.is_clean else 'FAIL'}",
            f"Scanned files: {self.scanned_files}.",
            f"Secret findings: {len(self.findings)}.",
            f"Workflow errors: {len(self.workflow_errors)}.",
        ]
        lines.extend(f"Secret: {item.path}:{item.line} ({item.kind})" for item in self.findings)
        lines.extend(f"Workflow: {item}" for item in self.workflow_errors)
        return "\n".join(lines)

    def format_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _is_text_candidate(path: Path) -> bool:
    return path.name in {"Dockerfile", "Makefile"} or path.suffix.casefold() in _TEXT_SUFFIXES


def scan_repository_secrets(
    root: Path = Path("."),
    *,
    excluded_paths: Iterable[str] = (),
    maximum_file_bytes: int = 1_000_000,
) -> tuple[int, tuple[SecretFinding, ...]]:
    source = root.expanduser().resolve()
    if maximum_file_bytes <= 0:
        raise ValueError("maximum_file_bytes must be positive")
    excluded = {item.replace("\\", "/").strip("/") for item in excluded_paths if item.strip("/")}
    scanned = 0
    findings: list[SecretFinding] = []
    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if not path.is_file() or any(part in _DEFAULT_EXCLUDED_PARTS for part in path.parts):
            continue
        relative = path.relative_to(source).as_posix()
        if relative in excluded or any(relative.startswith(item + "/") for item in excluded):
            continue
        if not _is_text_candidate(path) or path.stat().st_size > maximum_file_bytes:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        scanned += 1
        for line_number, line in enumerate(text.splitlines(), start=1):
            for kind, pattern in _SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(SecretFinding(relative, line_number, kind))
    return scanned, tuple(sorted(findings, key=lambda item: (item.path.casefold(), item.line, item.kind)))


def validate_workflow_permissions(workflow_directory: Path = Path(".github/workflows")) -> tuple[str, ...]:
    root = workflow_directory.expanduser().resolve()
    errors: list[str] = []
    for path in sorted((*root.glob("*.yml"), *root.glob("*.yaml")), key=lambda item: item.name.casefold()):
        text = path.read_text(encoding="utf-8")
        lowered = text.casefold()
        if "permissions: write-all" in lowered or "permissions: read-all" in lowered:
            errors.append(f"{path.name}: broad permissions shortcut is forbidden")
        if "pull_request_target:" in lowered:
            errors.append(f"{path.name}: pull_request_target requires an explicit security review")
        if "${{ secrets." in lowered and "persist-credentials: false" not in lowered:
            errors.append(f"{path.name}: secret-consuming workflows must disable checkout credential persistence")
        if path.name == "ci.yml" and "permissions:\n  contents: read" not in text:
            errors.append("ci.yml: top-level contents: read permission is required")
        if path.name == "publish-release.yml":
            required = ("contents: write", "id-token: write", "attestations: write")
            for permission in required:
                if permission not in text:
                    errors.append(f"publish-release.yml: missing {permission}")
    return tuple(sorted(errors, key=str.casefold))


def run_repository_security_policy(
    root: Path = Path("."), *, excluded_paths: Iterable[str] = ()
) -> RepositorySecurityResult:
    scanned, findings = scan_repository_secrets(root, excluded_paths=excluded_paths)
    workflow_errors = validate_workflow_permissions(root / ".github" / "workflows")
    return RepositorySecurityResult(scanned, findings, workflow_errors)
