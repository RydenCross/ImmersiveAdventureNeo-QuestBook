from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Callable, Mapping

from content import create_project
from generator.chapter_audit import run_chapter_audit
from generator.audit_registry_contract import run_audit_registry_contract
from generator.audit_performance_contract import run_audit_performance_contract
from generator.audit_dependency_contract import run_audit_dependency_contract
from generator.cli_audit import run_cli_audit
from generator.contract_guard import run_contract_guard
from generator.dependency_audit import audit_dependencies
from generator.determinism_audit import run_determinism_audit
from generator.documentation_audit import run_documentation_audit
from generator.identity_guard import run_identity_guard
from generator.output_manifest import run_output_manifest_guard
from generator.packaging_audit import run_packaging_audit
from generator.progression_guard import run_progression_guard
from generator.release_guard import run_release_guard
from generator.release_artifact_audit import run_release_artifact_audit
from generator.release_reproducibility_audit import run_release_reproducibility_audit
from generator.report_freshness import run_report_freshness_guard
from generator.repository_hygiene import run_repository_hygiene_audit
from generator.reward_audit import run_reward_audit
from generator.task_audit import run_task_audit
from generator.text_audit import run_text_audit
from generator.inventory_contract import run_test_inventory_contract
from generator.report_schema_contract import run_report_schema_contract
from generator.report_consistency_contract import run_report_consistency_contract
from generator.report_provenance_contract import run_report_provenance_contract
from generator.report_determinism_contract import run_report_determinism_contract
from generator.cli_output_contract import run_cli_output_contract
from generator.cli_exit_code_contract import run_cli_exit_code_contract
from generator.report_write_safety_contract import run_report_write_safety_contract
from generator.report_refresh_order_contract import run_report_refresh_order_contract
from generator.report_refresh_contract import run_report_refresh_contract
from generator.report_refresh_convergence_contract import run_report_refresh_convergence_contract
from generator.report_refresh_idempotence_contract import run_report_refresh_idempotence_contract
from generator.report_refresh_cache_contract import run_report_refresh_cache_contract
from generator.release_report_finalization_contract import run_release_report_finalization_contract
from generator.release_package_verification_contract import run_release_package_verification_contract
from generator.release_manifest_contract import run_release_manifest_contract
from generator.release_archive_metadata_contract import run_release_archive_metadata_contract
from generator.release_archive_extraction_safety_contract import run_release_archive_extraction_safety_contract
from generator.release_archive_unicode_path_contract import run_release_archive_unicode_path_contract
from generator.release_archive_compression_contract import run_release_archive_compression_contract
from generator.mod_compatibility_contract import run_mod_compatibility_contract
from generator.modpack_scanner_contract import run_modpack_scanner_contract
from generator.modpack_content_scanner_contract import run_modpack_content_scanner_contract
from generator.progression_planner_contract import run_progression_planner_contract


@dataclass(frozen=True, slots=True)
class QualityCheck:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": "pass" if self.passed else "fail",
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class QualityGate:
    checks: tuple[QualityCheck, ...]

    @property
    def is_clean(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def passed_count(self) -> int:
        return sum(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> tuple[str, ...]:
        return tuple(check.name for check in self.checks if not check.passed)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "checked": len(self.checks),
            "passed": self.passed_count,
            "failed": len(self.failed_checks),
            "failed_checks": list(self.failed_checks),
            "checks": [check.to_dict() for check in self.checks],
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Quality gate: {'PASS' if self.is_clean else 'FAIL'}",
            f"Checks: {len(self.checks)}.",
            f"Passed: {self.passed_count}.",
            f"Failed: {len(self.failed_checks)}.",
        ]
        lines.extend(
            f"[{'PASS' if check.passed else 'FAIL'}] {check.name}: {check.detail}"
            for check in self.checks
        )
        return "\n".join(lines)


def _default_checks() -> dict[str, Callable[[], object]]:
    project = create_project()
    return {
        "release guard": run_release_guard,
        "dependency audit": lambda: audit_dependencies(project),
        "progression guard": run_progression_guard,
        "identity guard": run_identity_guard,
        "contract guard": run_contract_guard,
        "reward audit": run_reward_audit,
        "task audit": run_task_audit,
        "chapter audit": run_chapter_audit,
        "text audit": run_text_audit,
        "determinism audit": run_determinism_audit,
        "output manifest guard": run_output_manifest_guard,
        "report freshness guard": run_report_freshness_guard,
        "packaging audit": run_packaging_audit,
        "CLI contract audit": run_cli_audit,
        "documentation contract audit": run_documentation_audit,
        "repository hygiene audit": run_repository_hygiene_audit,
        "release artifact audit": run_release_artifact_audit,
        "release reproducibility audit": run_release_reproducibility_audit,
        "audit registry contract": run_audit_registry_contract,
        "test inventory contract": run_test_inventory_contract,
        "report schema contract": run_report_schema_contract,
        "report consistency contract": run_report_consistency_contract,
        "report provenance contract": run_report_provenance_contract,
        "report determinism contract": run_report_determinism_contract,
        "CLI output contract": run_cli_output_contract,
        "CLI exit-code contract": run_cli_exit_code_contract,
        "report write-safety contract": run_report_write_safety_contract,
        "report refresh order contract": run_report_refresh_order_contract,
        "report refresh contract": run_report_refresh_contract,
        "report refresh convergence contract": run_report_refresh_convergence_contract,
        "report refresh idempotence contract": run_report_refresh_idempotence_contract,
        "report refresh cache contract": run_report_refresh_cache_contract,
        "release report finalization contract": run_release_report_finalization_contract,
        "release package verification contract": run_release_package_verification_contract,
        "release manifest contract": run_release_manifest_contract,
        "release archive metadata contract": run_release_archive_metadata_contract,
        "release archive extraction safety contract": run_release_archive_extraction_safety_contract,
        "release archive Unicode path contract": run_release_archive_unicode_path_contract,
        "release archive compression contract": run_release_archive_compression_contract,
        "mod compatibility contract": run_mod_compatibility_contract,
        "modpack scanner contract": run_modpack_scanner_contract,
        "modpack content scanner contract": run_modpack_content_scanner_contract,
        "progression planner contract": run_progression_planner_contract,
        "audit performance contract": run_audit_performance_contract,
        "audit dependency contract": run_audit_dependency_contract,
    }


def run_checks(checks: Mapping[str, Callable[[], object]]) -> QualityGate:
    results: list[QualityCheck] = []
    for name, runner in checks.items():
        try:
            result = runner()
            passed = bool(getattr(result, "is_clean"))
            detail = "clean" if passed else "reported defects"
        except (OSError, TypeError, ValueError) as exc:
            passed = False
            detail = f"error: {exc}"
        results.append(QualityCheck(name=name, passed=passed, detail=detail))
    return QualityGate(checks=tuple(results))


def run_quality_gate() -> QualityGate:
    return run_checks(_default_checks())
