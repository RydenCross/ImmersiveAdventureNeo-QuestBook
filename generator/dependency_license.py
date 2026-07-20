from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping

from generator.dependency_lock import parse_hashed_lock


@dataclass(frozen=True, slots=True)
class LicensedDependency:
    name: str
    version: str
    license_expression: str
    exception_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "name": self.name,
            "version": self.version,
            "license": self.license_expression,
            "status": "reviewed-exception" if self.exception_reason else "allowed",
        }
        if self.exception_reason:
            data["exception_reason"] = self.exception_reason
        return data


@dataclass(frozen=True, slots=True)
class DependencyLicenseResult:
    dependencies: tuple[LicensedDependency, ...]
    missing_packages: tuple[str, ...]
    denied_packages: tuple[str, ...]
    invalid_exceptions: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not (self.missing_packages or self.denied_packages or self.invalid_exceptions)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "dependency_count": len(self.dependencies),
            "missing_packages": list(self.missing_packages),
            "denied_packages": list(self.denied_packages),
            "invalid_exceptions": list(self.invalid_exceptions),
            "dependencies": [item.to_dict() for item in self.dependencies],
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Dependency license policy: {'PASS' if self.is_clean else 'FAIL'}",
            f"Dependencies: {len(self.dependencies)}.",
            f"Missing licenses: {len(self.missing_packages)}.",
            f"Denied licenses: {len(self.denied_packages)}.",
            f"Invalid exceptions: {len(self.invalid_exceptions)}.",
        ))


def evaluate_dependency_licenses(lock_path: Path, policy_path: Path) -> DependencyLicenseResult:
    locked = parse_hashed_lock(lock_path)
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    packages: Mapping[str, str] = payload.get("packages", {})
    policy = payload.get("policy", {})
    allowed = set(policy.get("allowed_spdx", []))
    denied = set(policy.get("denied_spdx", []))
    exceptions: Mapping[str, str] = payload.get("reviewed_exceptions", {})
    missing: list[str] = []
    blocked: list[str] = []
    invalid: list[str] = []
    items: list[LicensedDependency] = []
    locked_names = {item.name.casefold().replace("_", "-") for item in locked.dependencies}
    for name in exceptions:
        if name.casefold().replace("_", "-") not in locked_names or not str(exceptions[name]).strip():
            invalid.append(name)
    for dep in locked.dependencies:
        key = dep.name.casefold().replace("_", "-")
        expression = packages.get(key)
        if not expression:
            missing.append(dep.name)
            continue
        reason = exceptions.get(key)
        base = expression.split(" WITH ", 1)[0]
        if (expression in denied or base in denied or expression not in allowed) and not reason:
            blocked.append(f"{dep.name}:{expression}")
        items.append(LicensedDependency(dep.name, dep.version, expression, reason))
    return DependencyLicenseResult(
        tuple(sorted(items, key=lambda item: item.name.casefold())),
        tuple(sorted(missing, key=str.casefold)),
        tuple(sorted(blocked, key=str.casefold)),
        tuple(sorted(invalid, key=str.casefold)),
    )


def write_license_inventory(lock_path: Path, policy_path: Path, output: Path) -> Path:
    result = evaluate_dependency_licenses(lock_path, policy_path)
    if not result.is_clean:
        raise ValueError("dependency license policy is not clean")
    target = output.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(result.format_json() + "\n", encoding="utf-8", newline="\n")
    temporary.replace(target)
    return target
