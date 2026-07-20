from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import tomllib
from typing import Iterable, Mapping

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_VULNERABILITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


@dataclass(frozen=True, slots=True)
class DeclaredDependency:
    name: str
    requirement: str
    groups: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "requirement": self.requirement, "groups": list(self.groups)}


def _dependency_name(requirement: str) -> str:
    candidate = re.split(r"[<>=!~;\[\s]", requirement.strip(), maxsplit=1)[0]
    if not _NAME.fullmatch(candidate):
        raise ValueError(f"invalid dependency requirement: {requirement}")
    return candidate


def load_declared_dependencies(path: Path = Path("pyproject.toml")) -> tuple[DeclaredDependency, ...]:
    source = path.expanduser().resolve()
    payload = tomllib.loads(source.read_text(encoding="utf-8"))
    project = payload.get("project", {})
    grouped: dict[tuple[str, str], set[str]] = {}

    def add(requirements: Iterable[object], group: str) -> None:
        for raw in requirements:
            if not isinstance(raw, str) or not raw.strip():
                raise ValueError(f"dependency in group {group} must be a non-empty string")
            requirement = raw.strip()
            name = _dependency_name(requirement)
            grouped.setdefault((name.casefold(), requirement), set()).add(group)

    add(project.get("dependencies", ()), "runtime")
    optional = project.get("optional-dependencies", {})
    if not isinstance(optional, Mapping):
        raise ValueError("project.optional-dependencies must be a table")
    for group, requirements in optional.items():
        if not isinstance(group, str) or not isinstance(requirements, list):
            raise ValueError("optional dependency groups must contain arrays")
        add(requirements, group)

    return tuple(
        DeclaredDependency(name=_dependency_name(requirement), requirement=requirement, groups=tuple(sorted(groups)))
        for (_, requirement), groups in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1]))
    )


def dependency_inventory(path: Path = Path("pyproject.toml")) -> dict[str, object]:
    dependencies = load_declared_dependencies(path)
    groups = sorted({group for dependency in dependencies for group in dependency.groups})
    return {
        "schema_version": 1,
        "dependency_count": len(dependencies),
        "groups": groups,
        "dependencies": [dependency.to_dict() for dependency in dependencies],
    }


def write_dependency_inventory(output: Path, path: Path = Path("pyproject.toml")) -> Path:
    target = output.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(
        json.dumps(dependency_inventory(path), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(target)
    return target


@dataclass(frozen=True, slots=True)
class VulnerabilityFinding:
    dependency: str
    version: str
    vulnerability_id: str
    fix_versions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "dependency": self.dependency,
            "version": self.version,
            "vulnerability_id": self.vulnerability_id,
            "fix_versions": list(self.fix_versions),
        }


@dataclass(frozen=True, slots=True)
class VulnerabilityPolicyResult:
    findings: tuple[VulnerabilityFinding, ...]
    ignored_ids: tuple[str, ...]
    actionable: tuple[VulnerabilityFinding, ...]

    @property
    def is_clean(self) -> bool:
        return not self.actionable

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "finding_count": len(self.findings),
            "ignored_ids": list(self.ignored_ids),
            "actionable_count": len(self.actionable),
            "actionable": [finding.to_dict() for finding in self.actionable],
            "findings": [finding.to_dict() for finding in self.findings],
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Dependency vulnerability policy: {'PASS' if self.is_clean else 'FAIL'}",
                f"Findings: {len(self.findings)}.",
                f"Ignored vulnerability IDs: {len(self.ignored_ids)}.",
                f"Actionable findings: {len(self.actionable)}.",
            )
        )


def evaluate_pip_audit_report(report: Path, ignored_ids: Iterable[str] = ()) -> VulnerabilityPolicyResult:
    source = report.expanduser().resolve()
    payload = json.loads(source.read_text(encoding="utf-8"))
    dependencies = payload.get("dependencies") if isinstance(payload, dict) else payload
    if not isinstance(dependencies, list):
        raise ValueError("pip-audit report must contain a dependency list")
    ignored = tuple(sorted(set(ignored_ids), key=str.casefold))
    if any(not _VULNERABILITY.fullmatch(item) for item in ignored):
        raise ValueError("ignored vulnerability IDs must be portable identifiers")
    ignored_folded = {item.casefold() for item in ignored}
    findings: list[VulnerabilityFinding] = []
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            raise ValueError("dependency records must be objects")
        name = dependency.get("name")
        version = dependency.get("version")
        vulnerabilities = dependency.get("vulns", [])
        if not isinstance(name, str) or not _NAME.fullmatch(name) or not isinstance(version, str):
            raise ValueError("dependency records require a valid name and version")
        if not isinstance(vulnerabilities, list):
            raise ValueError("dependency vulnerabilities must be a list")
        for vulnerability in vulnerabilities:
            if not isinstance(vulnerability, dict):
                raise ValueError("vulnerability records must be objects")
            identifier = vulnerability.get("id")
            fixes = vulnerability.get("fix_versions", [])
            if not isinstance(identifier, str) or not _VULNERABILITY.fullmatch(identifier):
                raise ValueError("vulnerability records require a portable id")
            if not isinstance(fixes, list) or any(not isinstance(item, str) for item in fixes):
                raise ValueError("fix_versions must be a string list")
            findings.append(
                VulnerabilityFinding(name, version, identifier, tuple(sorted(set(fixes))))
            )
    ordered = tuple(sorted(findings, key=lambda item: (item.dependency.casefold(), item.vulnerability_id.casefold(), item.version)))
    actionable = tuple(item for item in ordered if item.vulnerability_id.casefold() not in ignored_folded)
    return VulnerabilityPolicyResult(ordered, ignored, actionable)
