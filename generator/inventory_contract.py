from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from generator.audit_registry_contract import AUDIT_REGISTRY

DEFAULT_TEST_DIRECTORY = Path("tests")

SPECIAL_TEST_FILES = {
    "release guard": "test_release_guard.py",
    "dependency audit": "test_dependency_audit.py",
    "progression guard": "test_progression_guard.py",
    "identity guard": "test_identity_guard.py",
    "contract guard": "test_contract_guard.py",
    "reward audit": "test_reward_audit.py",
    "task audit": "test_task_audit.py",
    "chapter audit": "test_chapter_audit.py",
    "text audit": "test_text_audit.py",
    "determinism audit": "test_determinism_audit.py",
    "output manifest guard": "test_output_manifest.py",
    "report freshness guard": "test_report_freshness.py",
    "packaging audit": "test_packaging_audit.py",
    "CLI contract audit": "test_cli_audit.py",
    "documentation contract audit": "test_documentation_audit.py",
    "repository hygiene audit": "test_repository_hygiene.py",
    "release artifact audit": "test_release_artifact_audit.py",
    "release reproducibility audit": "test_release_reproducibility_audit.py",
    "audit registry contract": "test_audit_registry_contract.py",
    "test inventory contract": "test_test_inventory_contract.py",
    "report schema contract": "test_report_schema_contract.py",
    "report consistency contract": "test_report_consistency_contract.py",
    "report provenance contract": "test_report_provenance_contract.py",
    "report determinism contract": "test_report_determinism_contract.py",
    "CLI output contract": "test_cli_output_contract.py",
    "CLI exit-code contract": "test_cli_exit_code_contract.py",
    "report write-safety contract": "test_report_write_safety_contract.py",
    "report refresh order contract": "test_report_refresh_order_contract.py",
    "report refresh contract": "test_report_refresh_contract.py",
    "report refresh convergence contract": "test_report_refresh_convergence_contract.py",
    "report refresh idempotence contract": "test_report_refresh_idempotence_contract.py",
    "report refresh cache contract": "test_report_refresh_cache_contract.py",
    "release report finalization contract": "test_release_report_finalization_contract.py",
    "release package verification contract": "test_release_package_verification_contract.py",
    "release manifest contract": "test_release_manifest_contract.py",
    "release archive metadata contract": "test_release_archive_metadata_contract.py",
    "release archive extraction safety contract": "test_release_archive_extraction_safety_contract.py",
    "release archive Unicode path contract": "test_release_archive_unicode_path_contract.py",
    "release archive compression contract": "test_release_archive_compression_contract.py",
    "mod compatibility contract": "test_mod_compatibility_contract.py",
    "modpack scanner contract": "test_modpack_scanner_contract.py",
    "modpack content scanner contract": "test_modpack_content_scanner_contract.py",
    "audit performance contract": "test_audit_performance_contract.py",
    "audit dependency contract": "test_audit_dependency_contract.py",
}


@dataclass(frozen=True, slots=True)
class TestInventoryContract:
    registered_audits: int
    expected_test_files: tuple[str, ...]
    missing_test_files: tuple[str, ...]
    files_without_tests: tuple[str, ...]
    unregistered_mappings: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any(
            (self.missing_test_files, self.files_without_tests, self.unregistered_mappings)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "registered_audits": self.registered_audits,
            "expected_test_files": list(self.expected_test_files),
            "missing_test_files": list(self.missing_test_files),
            "files_without_tests": list(self.files_without_tests),
            "unregistered_mappings": list(self.unregistered_mappings),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Test inventory contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Registered audits: {self.registered_audits}.",
            f"Expected test files: {len(self.expected_test_files)}.",
            f"Missing test files: {len(self.missing_test_files)}.",
            f"Files without tests: {len(self.files_without_tests)}.",
            f"Unregistered mappings: {len(self.unregistered_mappings)}.",
        ]
        lines.extend(f"Missing: {name}" for name in self.missing_test_files)
        lines.extend(f"No tests: {name}" for name in self.files_without_tests)
        lines.extend(f"Unregistered: {name}" for name in self.unregistered_mappings)
        return "\n".join(lines)


def run_test_inventory_contract(
    test_directory: Path = DEFAULT_TEST_DIRECTORY,
) -> TestInventoryContract:
    gate_names = tuple(item.gate_name for item in AUDIT_REGISTRY)
    expected = tuple(
        sorted(SPECIAL_TEST_FILES[name] for name in gate_names if name in SPECIAL_TEST_FILES)
    )
    unregistered = tuple(sorted(set(gate_names) - set(SPECIAL_TEST_FILES)))
    missing: list[str] = []
    empty: list[str] = []
    for name in expected:
        path = test_directory / name
        if not path.is_file():
            missing.append(name)
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            missing.append(name)
            continue
        if "def test_" not in source:
            empty.append(name)
    return TestInventoryContract(
        registered_audits=len(gate_names),
        expected_test_files=expected,
        missing_test_files=tuple(missing),
        files_without_tests=tuple(empty),
        unregistered_mappings=unregistered,
    )
