from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile

from generator.dependency_security import (
    dependency_inventory,
    evaluate_pip_audit_report,
    load_declared_dependencies,
    write_dependency_inventory,
)


@dataclass(frozen=True, slots=True)
class DependencySecurityContract:
    deterministic_inventory: bool
    dependency_groups_preserved: bool
    atomic_inventory_write: bool
    clean_report_passes: bool
    vulnerability_detected: bool
    explicit_ignore_supported: bool
    malformed_report_rejected: bool
    ci_integrated: bool

    @property
    def is_clean(self) -> bool:
        return all(getattr(self, field) for field in self.__dataclass_fields__)

    def to_dict(self) -> dict[str, object]:
        return {"status": "pass" if self.is_clean else "fail", **{field: getattr(self, field) for field in self.__dataclass_fields__}}

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return f"Dependency vulnerability policy and CI scanning contract: {'PASS' if self.is_clean else 'FAIL'}"


def run_dependency_security_contract() -> DependencySecurityContract:
    first = dependency_inventory()
    second = dependency_inventory()
    dependencies = load_declared_dependencies()
    with tempfile.TemporaryDirectory(prefix="ftbq-dependency-security-") as temporary:
        root = Path(temporary)
        output = write_dependency_inventory(root / "nested" / "dependency-inventory.json")
        clean = root / "clean.json"
        clean.write_text(json.dumps({"dependencies": [{"name": "pytest", "version": "1", "vulns": []}]}), encoding="utf-8")
        vulnerable = root / "vulnerable.json"
        vulnerable.write_text(json.dumps({"dependencies": [{"name": "pytest", "version": "1", "vulns": [{"id": "PYSEC-2026-1", "fix_versions": ["2"]}]}]}), encoding="utf-8")
        clean_result = evaluate_pip_audit_report(clean)
        vulnerable_result = evaluate_pip_audit_report(vulnerable)
        ignored_result = evaluate_pip_audit_report(vulnerable, ["PYSEC-2026-1"])
        malformed_rejected = False
        malformed = root / "malformed.json"
        malformed.write_text("{}", encoding="utf-8")
        try:
            evaluate_pip_audit_report(malformed)
        except ValueError:
            malformed_rejected = True
        workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
        return DependencySecurityContract(
            deterministic_inventory=first == second,
            dependency_groups_preserved=bool(dependencies) and {"dev", "desktop"}.issubset({group for item in dependencies for group in item.groups}),
            atomic_inventory_write=output.is_file() and not output.with_name(output.name + ".tmp").exists(),
            clean_report_passes=clean_result.is_clean,
            vulnerability_detected=not vulnerable_result.is_clean and vulnerable_result.actionable[0].vulnerability_id == "PYSEC-2026-1",
            explicit_ignore_supported=ignored_result.is_clean,
            malformed_report_rejected=malformed_rejected,
            ci_integrated=("pip-audit" in workflow and "quest-maker-vulnerability-policy" in workflow and "dependency-audit.json" in workflow),
        )
