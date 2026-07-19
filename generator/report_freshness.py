from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
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
from generator.progression_metrics import analyze_progression
from generator.release_guard import run_release_guard
from generator.release_artifact_audit import run_release_artifact_audit
from generator.release_reproducibility_audit import run_release_reproducibility_audit
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
from generator.quest_description_contract import run_quest_description_contract
from generator.ftb_blueprint_exporter_contract import run_ftb_blueprint_exporter_contract
from generator.questbook_review_contract import run_questbook_review_contract
from generator.reward_planner_contract import run_reward_planner_contract
from generator.editor_model_contract import run_editor_model_contract
from generator.editor_service_contract import run_editor_service_contract
from generator.editor_ui_contract import run_editor_ui_contract
from generator.editor_workspace_contract import run_editor_workspace_contract
from generator.editor_recovery_contract import run_editor_recovery_contract
from generator.editor_jobs_contract import run_editor_jobs_contract
from generator.project_bundle_contract import run_project_bundle_contract
from generator.desktop_launcher_contract import run_desktop_launcher_contract
from generator.native_distribution_contract import run_native_distribution_contract
from generator.desktop_packages_contract import run_desktop_packages_contract

DEFAULT_REPORT_DIRECTORY = Path("reports")


@dataclass(frozen=True, slots=True)
class ReportFreshness:
    checked_reports: int
    fresh_reports: tuple[str, ...]
    stale_reports: tuple[str, ...]
    missing_reports: tuple[str, ...]
    invalid_reports: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.stale_reports, self.missing_reports, self.invalid_reports))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "checked_reports": self.checked_reports,
            "fresh_reports": list(self.fresh_reports),
            "stale_reports": list(self.stale_reports),
            "missing_reports": list(self.missing_reports),
            "invalid_reports": list(self.invalid_reports),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Report freshness guard: {'PASS' if self.is_clean else 'FAIL'}",
            f"Checked reports: {self.checked_reports}.",
            f"Fresh reports: {len(self.fresh_reports)}.",
            f"Stale reports: {len(self.stale_reports)}.",
            f"Missing reports: {len(self.missing_reports)}.",
            f"Invalid reports: {len(self.invalid_reports)}.",
        ]
        lines.extend(f"Stale: {name}" for name in self.stale_reports)
        lines.extend(f"Missing: {name}" for name in self.missing_reports)
        lines.extend(f"Invalid: {name}" for name in self.invalid_reports)
        return "\n".join(lines)


def _default_renderers() -> dict[str, Callable[[], str]]:
    project = create_project()
    return {
        "release-guard.json": lambda: run_release_guard().format_json(),
        "dependency-audit.json": lambda: audit_dependencies(project).format_json(),
        "progression-metrics.json": lambda: analyze_progression(project).format_json(),
        "progression-guard.json": lambda: run_progression_guard().format_json(),
        "identity-guard.json": lambda: run_identity_guard().format_json(),
        "contract-guard.json": lambda: run_contract_guard().format_json(),
        "reward-audit.json": lambda: run_reward_audit().format_json(),
        "task-audit.json": lambda: run_task_audit().format_json(),
        "chapter-audit.json": lambda: run_chapter_audit().format_json(),
        "text-audit.json": lambda: run_text_audit().format_json(),
        "determinism-audit.json": lambda: run_determinism_audit().format_json(),
        "output-manifest-guard.json": lambda: run_output_manifest_guard().format_json(),
        "packaging-audit.json": lambda: run_packaging_audit().format_json(),
        "cli-audit.json": lambda: run_cli_audit().format_json(),
        "documentation-audit.json": lambda: run_documentation_audit().format_json(),
        "repository-hygiene-audit.json": lambda: run_repository_hygiene_audit().format_json(),
        "audit-registry-audit.json": lambda: run_audit_registry_contract().format_json(),
        "test-inventory-audit.json": lambda: run_test_inventory_contract().format_json(),
        "report-schema-audit.json": lambda: run_report_schema_contract().format_json(),
        "report-consistency-audit.json": lambda: run_report_consistency_contract().format_json(),
        "report-provenance-audit.json": lambda: run_report_provenance_contract().format_json(),
        "report-determinism-audit.json": lambda: run_report_determinism_contract().format_json(),
        "cli-output-audit.json": lambda: run_cli_output_contract().format_json(),
        "cli-exit-code-audit.json": lambda: run_cli_exit_code_contract().format_json(),
        "report-write-safety-audit.json": lambda: run_report_write_safety_contract().format_json(),
        "report-refresh-order-audit.json": lambda: run_report_refresh_order_contract().format_json(),
        "report-refresh-audit.json": lambda: run_report_refresh_contract().format_json(),
        "report-refresh-convergence-audit.json": lambda: run_report_refresh_convergence_contract().format_json(),
        "report-refresh-idempotence-audit.json": lambda: run_report_refresh_idempotence_contract().format_json(),
        "report-refresh-cache-audit.json": lambda: run_report_refresh_cache_contract().format_json(),
        "release-report-finalization-audit.json": lambda: run_release_report_finalization_contract().format_json(),
        "release-package-verification-audit.json": lambda: run_release_package_verification_contract().format_json(),
        "release-manifest-audit.json": lambda: run_release_manifest_contract().format_json(),
        "release-archive-metadata-audit.json": lambda: run_release_archive_metadata_contract().format_json(),
        "release-archive-extraction-safety-audit.json": lambda: run_release_archive_extraction_safety_contract().format_json(),
        "release-archive-unicode-path-audit.json": lambda: run_release_archive_unicode_path_contract().format_json(),
        "release-archive-compression-audit.json": lambda: run_release_archive_compression_contract().format_json(),
        "mod-compatibility-audit.json": lambda: run_mod_compatibility_contract().format_json(),
        "modpack-scanner-audit.json": lambda: run_modpack_scanner_contract().format_json(),
        "modpack-content-scanner-audit.json": lambda: run_modpack_content_scanner_contract().format_json(),
        "progression-planner-audit.json": lambda: run_progression_planner_contract().format_json(),
        "quest-description-audit.json": lambda: run_quest_description_contract().format_json(),
        "ftb-blueprint-exporter-audit.json": lambda: run_ftb_blueprint_exporter_contract().format_json(),
        "questbook-review-audit.json": lambda: run_questbook_review_contract().format_json(),
        "reward-planner-audit.json": lambda: run_reward_planner_contract().format_json(),
        "editor-model-audit.json": lambda: run_editor_model_contract().format_json(),
        "editor-service-audit.json": lambda: run_editor_service_contract().format_json(),
        "editor-ui-audit.json": lambda: run_editor_ui_contract().format_json(),
        "editor-workspace-audit.json": lambda: run_editor_workspace_contract().format_json(),
        "editor-recovery-audit.json": lambda: run_editor_recovery_contract().format_json(),
        "editor-jobs-audit.json": lambda: run_editor_jobs_contract().format_json(),
        "project-bundle-audit.json": lambda: run_project_bundle_contract().format_json(),
        "desktop-launcher-audit.json": lambda: run_desktop_launcher_contract().format_json(),
        "native-distribution-audit.json": lambda: run_native_distribution_contract().format_json(),
        "desktop-packages-audit.json": lambda: run_desktop_packages_contract().format_json(),
        "audit-performance-audit.json": lambda: run_audit_performance_contract().format_json(),
        "audit-dependency-audit.json": lambda: run_audit_dependency_contract().format_json(),
        "release-artifact-audit.json": lambda: run_release_artifact_audit().format_json(),
        "release-reproducibility-audit.json": lambda: run_release_reproducibility_audit().format_json(),
    }


def report_refresh_order() -> tuple[str, ...]:
    """Return the dependency-safe checked-in report regeneration order."""
    return tuple(_default_renderers())


def compare_report_payloads(
    report_directory: Path,
    renderers: Mapping[str, Callable[[], str]],
) -> ReportFreshness:
    fresh: list[str] = []
    stale: list[str] = []
    missing: list[str] = []
    invalid: list[str] = []

    for name, renderer in sorted(renderers.items()):
        path = report_directory / name
        if not path.is_file():
            missing.append(name)
            continue
        try:
            checked_in = json.loads(path.read_text(encoding="utf-8"))
            current = json.loads(renderer())
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            invalid.append(name)
            continue
        if checked_in == current:
            fresh.append(name)
        else:
            stale.append(name)

    return ReportFreshness(
        checked_reports=len(renderers),
        fresh_reports=tuple(fresh),
        stale_reports=tuple(stale),
        missing_reports=tuple(missing),
        invalid_reports=tuple(invalid),
    )


def run_report_freshness_guard(
    report_directory: Path = DEFAULT_REPORT_DIRECTORY,
) -> ReportFreshness:
    return compare_report_payloads(report_directory, _default_renderers())
