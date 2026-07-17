from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tomllib

DEFAULT_PYPROJECT_PATH = Path("pyproject.toml")
REQUIRED_PACKAGES = ("content*", "generator*", "model*")


@dataclass(frozen=True, slots=True)
class PackagingAudit:
    project_name: str
    package_patterns: tuple[str, ...]
    console_script: str | None
    errors: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "project_name": self.project_name,
            "package_patterns": list(self.package_patterns),
            "console_script": self.console_script,
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Packaging audit: {'PASS' if self.is_clean else 'FAIL'}",
            f"Project: {self.project_name or '<missing>'}.",
            f"Package patterns: {', '.join(self.package_patterns) or '<missing>'}.",
            f"Console script: {self.console_script or '<missing>'}.",
            f"Errors: {len(self.errors)}.",
        ]
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


def run_packaging_audit(path: Path = DEFAULT_PYPROJECT_PATH) -> PackagingAudit:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    setuptools = data.get("tool", {}).get("setuptools", {})
    find = setuptools.get("packages", {}).get("find", {})
    patterns = tuple(find.get("include", ()))
    scripts = project.get("scripts", {})
    console_script = scripts.get("immersive-adventure-quests")

    errors: list[str] = []
    if not project.get("name"):
        errors.append("project.name is missing")
    for pattern in REQUIRED_PACKAGES:
        if pattern not in patterns:
            errors.append(f"missing package discovery pattern: {pattern}")
    if console_script != "generator.cli:main":
        errors.append("immersive-adventure-quests must point to generator.cli:main")

    return PackagingAudit(
        project_name=str(project.get("name", "")),
        package_patterns=patterns,
        console_script=console_script,
        errors=tuple(errors),
    )
