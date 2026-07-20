from __future__ import annotations

import argparse
from pathlib import Path

from content import create_project
from generator.audit import audit_project
from generator.audit_registry_contract import run_audit_registry_contract
from generator.audit_performance_contract import run_audit_performance_contract
from generator.audit_dependency_contract import run_audit_dependency_contract
from generator.build import build
from generator.chapter_audit import run_chapter_audit
from generator.cli_audit import run_cli_audit
from generator.dependency_audit import audit_dependencies
from generator.dependency_graph import build_dependency_graph
from generator.determinism_audit import run_determinism_audit
from generator.documentation_audit import run_documentation_audit
from generator.contract_guard import (
    DEFAULT_CONTRACT_BASELINE_PATH,
    refresh_contract_baseline,
    run_contract_guard,
)
from generator.identity_guard import (
    DEFAULT_IDENTITY_BASELINE_PATH,
    refresh_identity_baseline,
    run_identity_guard,
)
from generator.report_freshness import run_report_freshness_guard
from generator.repository_hygiene import run_repository_hygiene_audit
from generator.release_artifact_audit import run_release_artifact_audit
from generator.release_reproducibility_audit import run_release_reproducibility_audit
from generator.packaging_audit import run_packaging_audit
from generator.output_manifest import (
    DEFAULT_OUTPUT_MANIFEST_PATH,
    refresh_output_manifest,
    run_output_manifest_guard,
)
from generator.parser import FTBQuestParser
from generator.progression_guard import DEFAULT_BUDGET_PATH, run_progression_guard
from generator.progression_metrics import analyze_progression
from generator.quality_gate import run_quality_gate
from generator.registry_audit import audit_registry, format_reference_manifest
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
from generator.release_package_verification_contract import (
    run_release_package_verification_contract,
)
from generator.release_manifest_contract import run_release_manifest_contract
from generator.release_archive_metadata_contract import run_release_archive_metadata_contract
from generator.release_archive_extraction_safety_contract import (
    run_release_archive_extraction_safety_contract,
)
from generator.release_archive_unicode_path_contract import (
    run_release_archive_unicode_path_contract,
)
from generator.release_archive_compression_contract import run_release_archive_compression_contract
from generator.mod_compatibility_contract import run_mod_compatibility_contract
from generator.modpack_scanner import scan_modpack
from generator.modpack_scanner_contract import run_modpack_scanner_contract
from generator.modpack_content_scanner import scan_modpack_content
from generator.modpack_content_scanner_contract import run_modpack_content_scanner_contract
from generator.progression_planner import generate_quest_blueprint
from generator.progression_planner_contract import run_progression_planner_contract
from generator.ftb_blueprint_exporter import export_modpack_questbook
from generator.ftb_blueprint_exporter_contract import run_ftb_blueprint_exporter_contract
from generator.questbook_review import review_modpack_questbook
from generator.questbook_review_contract import run_questbook_review_contract
from generator.reward_planner import REWARD_POLICIES, generate_quest_reward_plan
from generator.quest_description_generator import (
    DESCRIPTION_STYLES,
    generate_quest_description_plan,
)
from generator.quest_description_contract import run_quest_description_contract
from generator.reward_planner_contract import run_reward_planner_contract
from generator.editor_model import generate_editor_model
from generator.editor_model_contract import run_editor_model_contract
from generator.editor_service import (
    DEFAULT_EDITOR_HOST,
    DEFAULT_EDITOR_PORT,
    DEFAULT_EDITOR_WORKSPACE,
    serve_editor,
)
from generator.editor_service_contract import run_editor_service_contract
from generator.editor_ui_contract import run_editor_ui_contract
from generator.editor_workspace_contract import run_editor_workspace_contract
from generator.editor_recovery_contract import run_editor_recovery_contract
from generator.editor_jobs_contract import run_editor_jobs_contract
from generator.project_bundle import (
    BUNDLE_EXTENSION,
    create_project_bundle,
    inspect_project_bundle,
    install_project_bundle,
)
from generator.project_bundle_contract import run_project_bundle_contract
from generator.instance_discovery import InstanceSearchRoot, discover_modpack_instances
from generator.desktop_launcher import launch_desktop
from generator.desktop_launcher_contract import run_desktop_launcher_contract
from generator.desktop_setup import (
    DEFAULT_APPLICATION_ROOT,
    DEFAULT_PREFERENCES_PATH,
    complete_first_run_setup,
)
from generator.native_distribution import (
    DEFAULT_DISTRIBUTION_DIRECTORY,
    build_native_distribution,
)
from generator.native_distribution_contract import run_native_distribution_contract
from generator.desktop_packages import (
    DEFAULT_NATIVE_DIRECTORY as DEFAULT_PACKAGE_NATIVE_DIRECTORY,
    DEFAULT_PACKAGE_DIRECTORY,
    DEFAULT_UPDATE_METADATA_PATH,
    SUPPORTED_UPDATE_CHANNELS,
    build_desktop_package,
    create_update_metadata,
    parse_artifact_specs,
    verify_update_metadata,
    write_update_metadata,
)
from generator.desktop_packages_contract import run_desktop_packages_contract
from generator.application_updates import (
    DEFAULT_ARTIFACT_LIMIT_BYTES,
    DEFAULT_METADATA_LIMIT_BYTES,
    DEFAULT_UPDATE_STAGE_DIRECTORY,
    DEFAULT_UPDATE_TIMEOUT_SECONDS,
    check_for_application_update,
    stage_application_update,
)
from generator.application_updates_contract import run_application_updates_contract
from generator.update_application import apply_staged_update, rollback_applied_update
from generator.update_application_contract import run_update_application_contract
from generator.github_release import create_github_release_plan, publish_github_release
from generator.github_release_contract import run_github_release_contract
from generator.release_attestation import create_cyclonedx_sbom, create_slsa_provenance, write_json_document
from generator.release_attestation_contract import run_release_attestation_contract
from generator.report_refresh import refresh_reports
from generator.output_writer import atomic_write_text
from generator.release_check import run_release_check
from generator.release_compare import compare_release_reports, load_release_report
from generator.release_guard import (
    DEFAULT_BASELINE_PATH,
    refresh_release_baseline,
    run_release_guard,
)
from generator.validator import ProjectValidator


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m generator")
    subparsers = parser.add_subparsers(dest="command")

    lint = subparsers.add_parser("lint", help="Validate an FTB Quests project.")
    lint.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("config/ftbquests/quests"),
        help="Path to config/ftbquests, its quests directory, or a test fixture.",
    )
    audit = subparsers.add_parser(
        "audit", help="Summarize authored quest content quality and coverage."
    )
    audit.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when empty descriptions or taskless quests are found.",
    )
    dependency = subparsers.add_parser(
        "dependency-audit",
        help="Analyze quest progression dependencies and detect structural defects.",
    )
    dependency.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    dependency.add_argument(
        "--output", type=Path, help="Write the report to a file instead of standard output."
    )
    dependency.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when progression defects are detected.",
    )
    graph = subparsers.add_parser(
        "dependency-graph",
        help="Export the authored quest progression graph as Graphviz DOT or JSON.",
    )
    graph.add_argument(
        "--format",
        choices=("dot", "json"),
        default="dot",
        help="Select Graphviz DOT or machine-readable JSON output.",
    )
    graph.add_argument(
        "--output", type=Path, help="Write the graph to a file instead of standard output."
    )
    metrics = subparsers.add_parser(
        "progression-metrics",
        help="Measure critical-path depth, bottlenecks, and cross-chapter progression routes.",
    )
    metrics.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    metrics.add_argument(
        "--output", type=Path, help="Write the report to a file instead of standard output."
    )
    progression_guard = subparsers.add_parser(
        "progression-guard",
        help="Enforce checked-in progression complexity limits.",
    )
    progression_guard.add_argument(
        "budget",
        nargs="?",
        type=Path,
        default=DEFAULT_BUDGET_PATH,
        help="Progression budget (default: reports/progression-budget.json).",
    )
    progression_guard.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    progression_guard.add_argument(
        "--output", type=Path, help="Write the guard report to a file instead of standard output."
    )
    reward_audit = subparsers.add_parser(
        "reward-audit",
        help="Validate reward identifiers, item data, counts, and terminal reward coverage.",
    )
    reward_audit.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    reward_audit.add_argument(
        "--output",
        type=Path,
        help="Write the reward audit report to a file.",
    )
    reward_audit.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when structural reward defects are detected.",
    )
    task_audit = subparsers.add_parser(
        "task-audit",
        help="Validate task identifiers, required data, and quest completion coverage.",
    )
    task_audit.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    task_audit.add_argument(
        "--output",
        type=Path,
        help="Write the task audit report to a file.",
    )
    task_audit.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when structural task defects are detected.",
    )
    chapter_audit = subparsers.add_parser(
        "chapter-audit",
        help="Validate chapter identities, metadata, ordering, and quest coverage.",
    )
    chapter_audit.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    chapter_audit.add_argument(
        "--output",
        type=Path,
        help="Write the chapter audit report to a file.",
    )
    chapter_audit.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when structural chapter defects are detected.",
    )
    text_audit = subparsers.add_parser(
        "text-audit",
        help="Validate quest and chapter copy for placeholders, malformed formatting, and duplication.",
    )
    text_audit.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    text_audit.add_argument(
        "--output",
        type=Path,
        help="Write the text audit report to a file.",
    )
    text_audit.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when blocking text defects are detected.",
    )
    determinism_audit = subparsers.add_parser(
        "determinism-audit",
        help="Build twice and verify byte-for-byte reproducible generated output.",
    )
    determinism_audit.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    determinism_audit.add_argument(
        "--output",
        type=Path,
        help="Write the determinism audit report to a file.",
    )
    determinism_audit.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when generated builds differ.",
    )
    packaging_audit = subparsers.add_parser(
        "packaging-audit",
        help="Validate installable package discovery and the console entry point.",
    )
    packaging_audit.add_argument("--format", choices=("text", "json"), default="text")
    packaging_audit.add_argument("--output", type=Path)
    cli_audit = subparsers.add_parser(
        "cli-audit",
        help="Validate the documented CLI command surface and console entry point.",
    )
    cli_audit.add_argument("--format", choices=("text", "json"), default="text")
    cli_audit.add_argument("--output", type=Path)
    documentation_audit = subparsers.add_parser(
        "documentation-audit", help="Validate CLI documentation coverage and local Markdown links."
    )
    documentation_audit.add_argument("--format", choices=("text", "json"), default="text")
    documentation_audit.add_argument("--output", type=Path)
    repository_hygiene = subparsers.add_parser(
        "repository-hygiene-audit",
        help="Detect release-tree caches, build artifacts, secrets, and oversized files.",
    )
    repository_hygiene.add_argument("--format", choices=("text", "json"), default="text")
    repository_hygiene.add_argument("--output", type=Path)
    release_artifact = subparsers.add_parser(
        "release-artifact-audit",
        help="Validate the final repository release archive contents and integrity.",
    )
    release_artifact.add_argument("--format", choices=("text", "json"), default="text")
    release_artifact.add_argument("--output", type=Path)
    release_reproducibility = subparsers.add_parser(
        "release-reproducibility-audit",
        help="Verify independently created release archives contain identical files.",
    )
    release_reproducibility.add_argument("--format", choices=("text", "json"), default="text")
    release_reproducibility.add_argument("--output", type=Path)
    audit_registry = subparsers.add_parser(
        "audit-registry-audit",
        help="Verify every audit is consistently registered across release surfaces.",
    )
    audit_registry.add_argument("--format", choices=("text", "json"), default="text")
    audit_registry.add_argument("--output", type=Path)
    test_inventory = subparsers.add_parser(
        "test-inventory-audit",
        help="Verify every registered audit has a dedicated regression test module.",
    )
    test_inventory.add_argument("--format", choices=("text", "json"), default="text")
    test_inventory.add_argument("--output", type=Path)
    report_schema = subparsers.add_parser(
        "report-schema-audit",
        help="Validate the common JSON structure of every registered audit report.",
    )
    report_schema.add_argument("--format", choices=("text", "json"), default="text")
    report_schema.add_argument("--output", type=Path)
    report_consistency = subparsers.add_parser(
        "report-consistency-audit",
        help="Validate status and summary consistency across registered audit reports.",
    )
    report_consistency.add_argument("--format", choices=("text", "json"), default="text")
    report_consistency.add_argument("--output", type=Path)
    report_provenance = subparsers.add_parser(
        "report-provenance-audit",
        help="Trace every tracked audit report to its registered generator command.",
    )
    report_provenance.add_argument("--format", choices=("text", "json"), default="text")
    report_provenance.add_argument("--output", type=Path)
    report_determinism = subparsers.add_parser(
        "report-determinism-audit",
        help="Verify repeated audit report renders produce identical JSON payloads.",
    )
    report_determinism.add_argument("--format", choices=("text", "json"), default="text")
    report_determinism.add_argument("--output", type=Path)
    cli_output = subparsers.add_parser(
        "cli-output-audit",
        help="Validate JSON output, exit codes, and --output parity for audit commands.",
    )
    cli_output.add_argument("--format", choices=("text", "json"), default="text")
    cli_output.add_argument("--output", type=Path)
    report_write_safety = subparsers.add_parser(
        "report-write-safety-audit",
        help="Validate atomic and failure-safe report output writes.",
    )
    report_write_safety.add_argument("--format", choices=("text", "json"), default="text")
    report_write_safety.add_argument("--output", type=Path)
    report_refresh_order = subparsers.add_parser(
        "report-refresh-order-audit",
        help="Validate dependency-safe report regeneration order.",
    )
    report_refresh_order.add_argument("--format", choices=("text", "json"), default="text")
    report_refresh_order.add_argument("--output", type=Path)
    report_refresh = subparsers.add_parser(
        "report-refresh",
        help="Regenerate all checked-in audit reports in dependency-safe order.",
    )
    report_refresh.add_argument("--directory", type=Path, default=Path("reports"))
    report_refresh.add_argument("--format", choices=("text", "json"), default="text")
    report_refresh.add_argument(
        "--incremental",
        action="store_true",
        help="Skip report renderers whose inputs and checked-in outputs match the refresh cache.",
    )
    report_refresh.add_argument(
        "--cache",
        type=Path,
        help="Incremental cache path (default: <directory>/.report-refresh-cache.json).",
    )
    report_refresh_audit = subparsers.add_parser(
        "report-refresh-audit",
        help="Validate the dependency-safe report refresh command.",
    )
    report_refresh_audit.add_argument("--format", choices=("text", "json"), default="text")
    report_refresh_audit.add_argument("--output", type=Path)
    report_refresh_convergence = subparsers.add_parser(
        "report-refresh-convergence-audit",
        help="Validate fixed-point convergence of checked-in report regeneration.",
    )
    report_refresh_convergence.add_argument("--format", choices=("text", "json"), default="text")
    report_refresh_convergence.add_argument("--output", type=Path)
    report_refresh_idempotence = subparsers.add_parser(
        "report-refresh-idempotence-audit",
        help="Validate that a converged report refresh performs no further writes.",
    )
    report_refresh_idempotence.add_argument("--format", choices=("text", "json"), default="text")
    report_refresh_idempotence.add_argument("--output", type=Path)
    report_refresh_cache = subparsers.add_parser(
        "report-refresh-cache-audit",
        help="Validate incremental report refresh cache hits, invalidation, and recovery.",
    )
    report_refresh_cache.add_argument("--format", choices=("text", "json"), default="text")
    report_refresh_cache.add_argument("--output", type=Path)
    release_report_finalization = subparsers.add_parser(
        "release-report-finalization-audit",
        help="Validate final placement and stability of archive-derived release reports.",
    )
    release_report_finalization.add_argument("--format", choices=("text", "json"), default="text")
    release_report_finalization.add_argument("--output", type=Path)
    release_package_verification = subparsers.add_parser(
        "release-package-verification-audit",
        help="Verify the final release ZIP against artifact, reproducibility, and hygiene contracts.",
    )
    release_package_verification.add_argument("--format", choices=("text", "json"), default="text")
    release_package_verification.add_argument("--output", type=Path)
    release_manifest = subparsers.add_parser(
        "release-manifest-audit",
        help="Record and verify every packaged file path, size, and SHA-256 digest.",
    )
    release_manifest.add_argument("--format", choices=("text", "json"), default="text")
    release_manifest.add_argument("--output", type=Path)
    release_archive_metadata = subparsers.add_parser(
        "release-archive-metadata-audit",
        help="Validate deterministic ZIP timestamps, permissions, compression, paths, and ordering.",
    )
    release_archive_metadata.add_argument("--format", choices=("text", "json"), default="text")
    release_archive_metadata.add_argument("--output", type=Path)
    release_archive_extraction_safety = subparsers.add_parser(
        "release-archive-extraction-safety-audit",
        help="Validate ZIP extraction paths, collisions, links, and special-file safety.",
    )
    release_archive_extraction_safety.add_argument(
        "--format", choices=("text", "json"), default="text"
    )
    release_archive_extraction_safety.add_argument("--output", type=Path)
    release_archive_unicode_path = subparsers.add_parser(
        "release-archive-unicode-path-audit",
        help="Validate Unicode normalization, confusable collisions, controls, and portable ZIP paths.",
    )
    release_archive_unicode_path.add_argument("--format", choices=("text", "json"), default="text")
    release_archive_unicode_path.add_argument("--output", type=Path)
    release_archive_compression = subparsers.add_parser(
        "release-archive-compression-audit",
        help="Validate release ZIP compression methods, savings, and size budgets.",
    )
    release_archive_compression.add_argument("--format", choices=("text", "json"), default="text")
    release_archive_compression.add_argument("--output", type=Path)
    modpack_scan = subparsers.add_parser(
        "modpack-scan",
        help="Inspect a modpack archive, instance, or mods directory and generate a normalized pack profile.",
    )
    modpack_scan.add_argument(
        "path", type=Path, help="Modpack ZIP/MRPACK, instance folder, or mods directory."
    )
    modpack_scan.add_argument("--format", choices=("text", "json"), default="text")
    modpack_scan.add_argument("--output", type=Path, help="Write the generated profile to a file.")
    modpack_content_scan = subparsers.add_parser(
        "modpack-content-scan",
        help="Scan recipes, advancements, registries, and tags into progression-ready quest candidates.",
    )
    modpack_content_scan.add_argument(
        "path", type=Path, help="Modpack ZIP/MRPACK, instance folder, mods directory, or mod JAR."
    )
    modpack_content_scan.add_argument(
        "--candidate-limit",
        type=int,
        help="Maximum generated quest candidates (default: pack-profile recommendation).",
    )
    modpack_content_scan.add_argument("--format", choices=("text", "json"), default="text")
    modpack_content_scan.add_argument(
        "--output", type=Path, help="Write the content profile to a file."
    )
    quest_blueprint = subparsers.add_parser(
        "quest-blueprint",
        help="Plan scanned quest candidates into ordered mod chapters and a reviewable questbook blueprint.",
    )
    quest_blueprint.add_argument(
        "path", type=Path, help="Modpack ZIP/MRPACK, instance folder, mods directory, or mod JAR."
    )
    quest_blueprint.add_argument(
        "--target-quests",
        type=int,
        help="Desired quest count (default: pack-profile recommendation).",
    )
    quest_blueprint.add_argument(
        "--chapter-size",
        type=int,
        default=40,
        help="Maximum quests per generated chapter (default: 40).",
    )
    quest_blueprint.add_argument("--format", choices=("text", "json"), default="text")
    quest_blueprint.add_argument("--output", type=Path, help="Write the quest blueprint to a file.")
    quest_description_plan = subparsers.add_parser(
        "quest-description-plan",
        help="Generate grounded player-facing instructions for every planned quest.",
    )
    quest_description_plan.add_argument(
        "path", type=Path, help="Modpack ZIP/MRPACK, instance folder, mods directory, or mod JAR."
    )
    quest_description_plan.add_argument(
        "--target-quests",
        type=int,
        help="Desired quest count (default: pack-profile recommendation).",
    )
    quest_description_plan.add_argument(
        "--chapter-size",
        type=int,
        default=40,
        help="Maximum quests per generated chapter (default: 40).",
    )
    quest_description_plan.add_argument(
        "--style",
        choices=DESCRIPTION_STYLES,
        default="guided",
        help="Description detail level (default: guided).",
    )
    quest_description_plan.add_argument("--format", choices=("text", "json"), default="text")
    quest_description_plan.add_argument(
        "--output", type=Path, help="Write the description plan to a file."
    )
    quest_reward_plan = subparsers.add_parser(
        "quest-reward-plan",
        help="Assign deterministic reward or explicit no-reward decisions to a generated blueprint.",
    )
    quest_reward_plan.add_argument(
        "path", type=Path, help="Modpack ZIP/MRPACK, instance folder, mods directory, or mod JAR."
    )
    quest_reward_plan.add_argument(
        "--target-quests",
        type=int,
        help="Desired quest count (default: pack-profile recommendation).",
    )
    quest_reward_plan.add_argument(
        "--chapter-size",
        type=int,
        default=40,
        help="Maximum quests per generated chapter (default: 40).",
    )
    quest_reward_plan.add_argument(
        "--policy",
        choices=REWARD_POLICIES,
        default="conservative",
        help="Reward density policy (default: conservative).",
    )
    quest_reward_plan.add_argument(
        "--description-style",
        choices=DESCRIPTION_STYLES,
        default="guided",
        help="Description detail level applied before reward planning (default: guided).",
    )
    quest_reward_plan.add_argument("--format", choices=("text", "json"), default="text")
    quest_reward_plan.add_argument("--output", type=Path, help="Write the reward plan to a file.")
    quest_editor_model = subparsers.add_parser(
        "quest-editor-model",
        help="Generate a versioned visual-editor document with nodes, edges, and change tracking.",
    )
    quest_editor_model.add_argument(
        "path", type=Path, help="Modpack ZIP/MRPACK, instance folder, mods directory, or mod JAR."
    )
    quest_editor_model.add_argument(
        "--target-quests",
        type=int,
        help="Desired quest count (default: pack-profile recommendation).",
    )
    quest_editor_model.add_argument(
        "--chapter-size",
        type=int,
        default=40,
        help="Maximum quests per generated chapter (default: 40).",
    )
    quest_editor_model.add_argument(
        "--description-style",
        choices=DESCRIPTION_STYLES,
        default="guided",
        help="Description detail level applied before editor conversion (default: guided).",
    )
    quest_editor_model.add_argument(
        "--reward-policy",
        choices=("unassigned", *REWARD_POLICIES),
        default="unassigned",
        help="Optional generated reward policy stored in the editor document (default: unassigned).",
    )
    quest_editor_model.add_argument("--format", choices=("text", "json"), default="text")
    quest_editor_model.add_argument(
        "--output", type=Path, help="Write the editor document to a file."
    )
    quest_project_bundle = subparsers.add_parser(
        "quest-project-bundle",
        help="Generate a portable editor document and FTB Quests export bundle.",
    )
    quest_project_bundle.add_argument(
        "path", type=Path, help="Modpack ZIP/MRPACK, instance folder, mods directory, or mod JAR."
    )
    quest_project_bundle.add_argument(
        "--destination",
        type=Path,
        default=Path(f"project{BUNDLE_EXTENSION}"),
        help=f"Portable project destination (default: project{BUNDLE_EXTENSION}).",
    )
    quest_project_bundle.add_argument("--target-quests", type=int)
    quest_project_bundle.add_argument("--chapter-size", type=int, default=40)
    quest_project_bundle.add_argument(
        "--description-style", choices=DESCRIPTION_STYLES, default="guided"
    )
    quest_project_bundle.add_argument(
        "--reward-policy", choices=("unassigned", *REWARD_POLICIES), default="unassigned"
    )
    quest_project_bundle.add_argument("--format", choices=("text", "json"), default="text")
    quest_project_bundle.add_argument("--output", type=Path)
    quest_project_inspect = subparsers.add_parser(
        "quest-project-inspect", help="Verify a portable FTB Quest Maker project bundle."
    )
    quest_project_inspect.add_argument("bundle", type=Path)
    quest_project_inspect.add_argument("--format", choices=("text", "json"), default="text")
    quest_project_inspect.add_argument("--output", type=Path)
    quest_project_install = subparsers.add_parser(
        "quest-project-install", help="Install a verified project bundle into a Minecraft instance."
    )
    quest_project_install.add_argument("bundle", type=Path)
    quest_project_install.add_argument("instance", type=Path)
    quest_project_install.add_argument("--no-backup", action="store_true")
    quest_project_install.add_argument("--dry-run", action="store_true")
    quest_project_install.add_argument("--force", action="store_true")
    quest_project_install.add_argument("--format", choices=("text", "json"), default="text")
    quest_project_install.add_argument("--output", type=Path)
    quest_instance_discover = subparsers.add_parser(
        "quest-instance-discover",
        help="Discover supported local Minecraft and modpack launcher instances.",
    )
    quest_instance_discover.add_argument(
        "--root",
        action="append",
        type=Path,
        default=[],
        help="Search a custom launcher or instance directory; may be repeated.",
    )
    quest_instance_discover.add_argument(
        "--max-instances",
        type=int,
        default=500,
        help="Maximum discovered instances to return (default: 500).",
    )
    quest_instance_discover.add_argument("--format", choices=("text", "json"), default="text")
    quest_instance_discover.add_argument("--output", type=Path)
    quest_maker_launch = subparsers.add_parser(
        "quest-maker-launch",
        help="Open the desktop launcher and automatically discover modpack instances.",
    )
    quest_maker_launch.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Override the saved root directory for per-instance editor workspaces.",
    )
    quest_maker_launch.add_argument(
        "--preferences",
        type=Path,
        default=DEFAULT_PREFERENCES_PATH,
        help="Desktop preferences file used by first-run setup.",
    )
    quest_maker_launch.add_argument(
        "--root",
        action="append",
        type=Path,
        default=[],
        help="Search a custom launcher or instance directory; may be repeated.",
    )
    quest_maker_launch.add_argument(
        "--no-browser",
        action="store_true",
        help="Start selected editor services without opening a browser automatically.",
    )
    quest_maker_launch.add_argument(
        "--reset-setup",
        action="store_true",
        help="Show the first-run setup dialog again before discovery.",
    )
    quest_maker_setup = subparsers.add_parser(
        "quest-maker-setup",
        help="Complete first-run desktop setup and persist launcher preferences.",
    )
    quest_maker_setup.add_argument("--preferences", type=Path, default=DEFAULT_PREFERENCES_PATH)
    quest_maker_setup.add_argument("--workspace", type=Path, default=DEFAULT_APPLICATION_ROOT)
    quest_maker_setup.add_argument("--root", action="append", type=Path, default=[])
    quest_maker_setup.add_argument("--no-browser", action="store_true")
    quest_maker_setup.add_argument("--max-instances", type=int, default=500)
    quest_maker_setup.add_argument("--format", choices=("text", "json"), default="text")
    quest_maker_setup.add_argument("--output", type=Path)
    native_build = subparsers.add_parser(
        "quest-maker-native-build",
        help="Build or inspect the standalone Windows/Linux desktop distribution plan.",
    )
    native_build.add_argument("--platform", choices=("auto", "windows", "linux"), default="auto")
    native_build.add_argument("--destination", type=Path, default=DEFAULT_DISTRIBUTION_DIRECTORY)
    native_build.add_argument("--dry-run", action="store_true")
    native_build.add_argument("--format", choices=("text", "json"), default="text")
    native_build.add_argument("--output", type=Path)
    package_build = subparsers.add_parser(
        "quest-maker-package-build",
        help="Build or inspect a Windows installer or Linux AppImage package plan.",
    )
    package_build.add_argument("--platform", choices=("windows", "linux"), required=True)
    package_build.add_argument("--version", required=True)
    package_build.add_argument(
        "--native-directory", type=Path, default=DEFAULT_PACKAGE_NATIVE_DIRECTORY
    )
    package_build.add_argument("--destination", type=Path, default=DEFAULT_PACKAGE_DIRECTORY)
    package_build.add_argument("--dry-run", action="store_true")
    package_build.add_argument("--format", choices=("text", "json"), default="text")
    package_build.add_argument("--output", type=Path)
    update_metadata = subparsers.add_parser(
        "quest-maker-update-metadata",
        help="Generate deterministic application update metadata for desktop packages.",
    )
    update_metadata.add_argument("--version", required=True)
    update_metadata.add_argument("--channel", choices=SUPPORTED_UPDATE_CHANNELS, default="stable")
    update_metadata.add_argument(
        "--artifact",
        action="append",
        required=True,
        help="Package artifact as platform=path, or a .exe/.AppImage path.",
    )
    update_metadata.add_argument("--base-url", default="")
    update_metadata.add_argument("--destination", type=Path, default=DEFAULT_UPDATE_METADATA_PATH)
    update_metadata.add_argument("--signing-key", type=Path)
    update_metadata.add_argument("--key-id", default="local")
    update_metadata.add_argument("--format", choices=("text", "json"), default="text")
    update_metadata.add_argument("--output", type=Path)
    update_verify = subparsers.add_parser(
        "quest-maker-update-verify",
        help="Verify desktop update metadata, signatures, and local package checksums.",
    )
    update_verify.add_argument("metadata", type=Path)
    update_verify.add_argument("--artifact-directory", type=Path)
    update_verify.add_argument("--signing-key", type=Path)
    update_verify.add_argument("--format", choices=("text", "json"), default="text")
    update_verify.add_argument("--output", type=Path)
    update_check = subparsers.add_parser(
        "quest-maker-update-check",
        help="Check local or HTTPS metadata for a newer verified desktop release.",
    )
    update_check.add_argument("source", help="Local metadata path or HTTPS metadata URL.")
    update_check.add_argument("--current-version", required=True)
    update_check.add_argument("--channel", choices=SUPPORTED_UPDATE_CHANNELS, default="stable")
    update_check.add_argument("--platform", choices=("auto", "windows", "linux"), default="auto")
    update_check.add_argument("--signing-key", type=Path)
    update_check.add_argument("--require-signature", action="store_true")
    update_check.add_argument(
        "--max-metadata-bytes", type=int, default=DEFAULT_METADATA_LIMIT_BYTES
    )
    update_check.add_argument("--timeout", type=float, default=DEFAULT_UPDATE_TIMEOUT_SECONDS)
    update_check.add_argument("--format", choices=("text", "json"), default="text")
    update_check.add_argument("--output", type=Path)
    update_stage = subparsers.add_parser(
        "quest-maker-update-stage",
        help="Check, download, checksum, and atomically stage a desktop update.",
    )
    update_stage.add_argument("source", help="Local metadata path or HTTPS metadata URL.")
    update_stage.add_argument("--current-version", required=True)
    update_stage.add_argument("--channel", choices=SUPPORTED_UPDATE_CHANNELS, default="stable")
    update_stage.add_argument("--platform", choices=("auto", "windows", "linux"), default="auto")
    update_stage.add_argument("--signing-key", type=Path)
    update_stage.add_argument("--require-signature", action="store_true")
    update_stage.add_argument("--destination", type=Path, default=DEFAULT_UPDATE_STAGE_DIRECTORY)
    update_stage.add_argument(
        "--max-metadata-bytes", type=int, default=DEFAULT_METADATA_LIMIT_BYTES
    )
    update_stage.add_argument(
        "--max-artifact-bytes", type=int, default=DEFAULT_ARTIFACT_LIMIT_BYTES
    )
    update_stage.add_argument("--timeout", type=float, default=DEFAULT_UPDATE_TIMEOUT_SECONDS)
    update_stage.add_argument("--format", choices=("text", "json"), default="text")
    update_stage.add_argument("--output", type=Path)
    update_apply = subparsers.add_parser(
        "quest-maker-update-apply",
        help="Verify and apply a staged desktop update, or print a safe dry-run plan.",
    )
    update_apply.add_argument("manifest", type=Path)
    update_apply.add_argument("--current-executable", type=Path)
    update_apply.add_argument("--execute", action="store_true")
    update_apply.add_argument("--format", choices=("text", "json"), default="text")
    update_apply.add_argument("--output", type=Path)
    update_rollback = subparsers.add_parser(
        "quest-maker-update-rollback",
        help="Restore a Linux AppImage from a verified rollback manifest.",
    )
    update_rollback.add_argument("manifest", type=Path)
    update_rollback.add_argument("--execute", action="store_true")
    update_rollback.add_argument("--format", choices=("text", "json"), default="text")
    update_rollback.add_argument("--output", type=Path)
    github_release_plan = subparsers.add_parser(
        "quest-maker-github-release-plan",
        help="Create a deterministic, checksum-backed GitHub Release publishing plan.",
    )
    github_release_plan.add_argument("--repository", required=True)
    github_release_plan.add_argument("--tag", required=True)
    github_release_plan.add_argument("--title")
    github_release_plan.add_argument("--notes", type=Path, required=True)
    github_release_plan.add_argument("--asset", action="append", type=Path, required=True)
    github_release_plan.add_argument("--prerelease", action="store_true")
    github_release_plan.add_argument("--draft", action="store_true")
    github_release_plan.add_argument("--output", type=Path)
    github_release_publish = subparsers.add_parser(
        "quest-maker-github-release-publish",
        help="Publish a verified GitHub Release plan through the authenticated gh CLI.",
    )
    github_release_publish.add_argument("--repository", required=True)
    github_release_publish.add_argument("--tag", required=True)
    github_release_publish.add_argument("--title")
    github_release_publish.add_argument("--notes", type=Path, required=True)
    github_release_publish.add_argument("--asset", action="append", type=Path, required=True)
    github_release_publish.add_argument("--prerelease", action="store_true")
    github_release_publish.add_argument("--draft", action="store_true")
    github_release_publish.add_argument("--execute", action="store_true")
    github_release_publish.add_argument("--output", type=Path)
    release_sbom = subparsers.add_parser(
        "quest-maker-release-sbom",
        help="Generate a deterministic CycloneDX SBOM for release artifacts.",
    )
    release_sbom.add_argument("--version", required=True)
    release_sbom.add_argument("--artifact", action="append", type=Path, required=True)
    release_sbom.add_argument("--component", action="append", default=[])
    release_sbom.add_argument("--output", type=Path, required=True)
    release_provenance = subparsers.add_parser(
        "quest-maker-release-provenance",
        help="Generate deterministic SLSA provenance for release artifacts.",
    )
    release_provenance.add_argument("--repository", required=True)
    release_provenance.add_argument("--revision", required=True)
    release_provenance.add_argument("--workflow", default=".github/workflows/publish-release.yml")
    release_provenance.add_argument("--artifact", action="append", type=Path, required=True)
    release_provenance.add_argument("--output", type=Path, required=True)
    quest_editor_serve = subparsers.add_parser(
        "quest-editor-serve",
        help="Launch the local FTB Quest Maker visual editor service and JSON API.",
    )
    quest_editor_serve.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="Optional modpack archive/folder or editor-model JSON; omit to start with the drop zone.",
    )
    quest_editor_serve.add_argument(
        "--workspace",
        type=Path,
        default=DEFAULT_EDITOR_WORKSPACE,
        help="Workspace for saved models and exports (default: .quest-editor).",
    )
    quest_editor_serve.add_argument(
        "--host",
        default=DEFAULT_EDITOR_HOST,
        help="Loopback host to bind (default: 127.0.0.1).",
    )
    quest_editor_serve.add_argument(
        "--port",
        type=int,
        default=DEFAULT_EDITOR_PORT,
        help="Local HTTP port (default: 8765; use 0 for an automatic port).",
    )
    quest_editor_serve.add_argument(
        "--target-quests",
        type=int,
        help="Desired quest count when generating from a modpack.",
    )
    quest_editor_serve.add_argument(
        "--chapter-size",
        type=int,
        default=40,
        help="Maximum quests per generated chapter (default: 40).",
    )
    quest_editor_serve.add_argument(
        "--description-style",
        choices=DESCRIPTION_STYLES,
        default="guided",
        help="Description detail level used when generating the initial model.",
    )
    quest_editor_serve.add_argument(
        "--reward-policy",
        choices=("unassigned", *REWARD_POLICIES),
        default="unassigned",
        help="Optional reward policy used when generating the initial model.",
    )
    quest_editor_serve.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the editor URL in the default browser.",
    )
    ftb_quest_export = subparsers.add_parser(
        "ftb-quest-export",
        help="Generate and export a modpack quest blueprint as an installable FTB Quests SNBT tree.",
    )
    ftb_quest_export.add_argument(
        "path", type=Path, help="Modpack ZIP/MRPACK, instance folder, mods directory, or mod JAR."
    )
    ftb_quest_export.add_argument(
        "--destination",
        type=Path,
        default=Path("generated/ftbquests"),
        help="Destination config/ftbquests directory (default: generated/ftbquests).",
    )
    ftb_quest_export.add_argument(
        "--target-quests",
        type=int,
        help="Desired quest count (default: pack-profile recommendation).",
    )
    ftb_quest_export.add_argument(
        "--chapter-size",
        type=int,
        default=40,
        help="Maximum quests per generated chapter (default: 40).",
    )
    ftb_quest_export.add_argument(
        "--description-style",
        choices=DESCRIPTION_STYLES,
        default="guided",
        help="Description detail level applied before export (default: guided).",
    )
    ftb_quest_export.add_argument(
        "--reward-policy",
        choices=("unassigned", *REWARD_POLICIES),
        default="unassigned",
        help="Apply generated reward decisions before export (default: unassigned).",
    )
    ftb_quest_export.add_argument("--format", choices=("text", "json"), default="text")
    ftb_quest_export.add_argument("--output", type=Path, help="Write the export summary to a file.")
    questbook_review = subparsers.add_parser(
        "questbook-review",
        help="Generate an editorial and structural review report for a generated questbook.",
    )
    questbook_review.add_argument(
        "path", type=Path, help="Modpack ZIP/MRPACK, instance folder, mods directory, or mod JAR."
    )
    questbook_review.add_argument(
        "--target-quests",
        type=int,
        help="Desired quest count (default: pack-profile recommendation).",
    )
    questbook_review.add_argument(
        "--chapter-size", type=int, default=40, help="Planner chapter size (default: 40)."
    )
    questbook_review.add_argument(
        "--low-confidence-threshold",
        type=float,
        default=0.75,
        help="Flag quests below this confidence score (default: 0.75).",
    )
    questbook_review.add_argument(
        "--min-description-words",
        type=int,
        default=6,
        help="Minimum recommended description length (default: 6 words).",
    )
    questbook_review.add_argument(
        "--max-chapter-quests",
        type=int,
        default=50,
        help="Flag chapters above this size (default: 50).",
    )
    questbook_review.add_argument(
        "--bottleneck-dependents",
        type=int,
        default=8,
        help="Flag quests directly gating at least this many quests (default: 8).",
    )
    questbook_review.add_argument(
        "--description-style",
        choices=DESCRIPTION_STYLES,
        default="guided",
        help="Description detail level applied before review (default: guided).",
    )
    questbook_review.add_argument(
        "--reward-policy",
        choices=("unassigned", *REWARD_POLICIES),
        default="unassigned",
        help="Review an automatically rewarded blueprint (default: unassigned).",
    )
    questbook_review.add_argument("--format", choices=("text", "json"), default="text")
    questbook_review.add_argument("--output", type=Path, help="Write the review report to a file.")
    mod_compatibility = subparsers.add_parser(
        "mod-compatibility-audit",
        help="Validate the supported Minecraft, NeoForge, and authored mod compatibility matrix.",
    )
    mod_compatibility.add_argument("--format", choices=("text", "json"), default="text")
    mod_compatibility.add_argument("--output", type=Path)
    modpack_scanner = subparsers.add_parser(
        "modpack-scanner-audit",
        help="Validate supported modpack formats, JAR metadata inspection, and profile generation.",
    )
    modpack_scanner.add_argument("--format", choices=("text", "json"), default="text")
    modpack_scanner.add_argument("--output", type=Path)
    modpack_content_scanner = subparsers.add_parser(
        "modpack-content-scanner-audit",
        help="Validate recipe, advancement, registry, tag, and quest-candidate extraction.",
    )
    modpack_content_scanner.add_argument("--format", choices=("text", "json"), default="text")
    modpack_content_scanner.add_argument("--output", type=Path)
    progression_planner = subparsers.add_parser(
        "progression-planner-audit",
        help="Validate deterministic chapter planning, dependency closure, limits, and blueprint layout.",
    )
    progression_planner.add_argument("--format", choices=("text", "json"), default="text")
    progression_planner.add_argument("--output", type=Path)
    ftb_blueprint_exporter = subparsers.add_parser(
        "ftb-blueprint-exporter-audit",
        help="Validate deterministic FTB Quests SNBT export, task conversion, and dependency preservation.",
    )
    ftb_blueprint_exporter.add_argument("--format", choices=("text", "json"), default="text")
    ftb_blueprint_exporter.add_argument("--output", type=Path)
    questbook_review_audit = subparsers.add_parser(
        "questbook-review-audit",
        help="Validate generated questbook editorial, reward, chapter-size, and graph review checks.",
    )
    questbook_review_audit.add_argument("--format", choices=("text", "json"), default="text")
    questbook_review_audit.add_argument("--output", type=Path)
    reward_planner = subparsers.add_parser(
        "reward-planner-audit",
        help="Validate reward decisions, policy scaling, review resolution, and FTB export.",
    )
    reward_planner.add_argument("--format", choices=("text", "json"), default="text")
    reward_planner.add_argument("--output", type=Path)
    quest_description = subparsers.add_parser(
        "quest-description-audit",
        help="Validate grounded quest instructions, prerequisites, review notes, and export compatibility.",
    )
    quest_description.add_argument("--format", choices=("text", "json"), default="text")
    quest_description.add_argument("--output", type=Path)
    editor_model = subparsers.add_parser(
        "editor-model-audit",
        help="Validate editor JSON round trips, reversible edits, graph safety, and export compatibility.",
    )
    editor_model.add_argument("--format", choices=("text", "json"), default="text")
    editor_model.add_argument("--output", type=Path)
    editor_service = subparsers.add_parser(
        "editor-service-audit",
        help="Validate local editor sessions, API routes, history, file safety, and FTB export.",
    )
    editor_service.add_argument("--format", choices=("text", "json"), default="text")
    editor_service.add_argument("--output", type=Path)
    editor_ui = subparsers.add_parser(
        "editor-ui-audit",
        help="Validate drag-and-drop modpack import and the interactive quest graph canvas.",
    )
    editor_ui.add_argument("--format", choices=("text", "json"), default="text")
    editor_ui.add_argument("--output", type=Path)
    editor_workspace = subparsers.add_parser(
        "editor-workspace-audit",
        help="Validate deterministic graph auto-layout and atomic bulk editor operations.",
    )
    editor_workspace.add_argument("--format", choices=("text", "json"), default="text")
    editor_workspace.add_argument("--output", type=Path)
    editor_recovery = subparsers.add_parser(
        "editor-recovery-audit",
        help="Validate atomic autosave, bounded project snapshots, and crash recovery.",
    )
    editor_recovery.add_argument("--format", choices=("text", "json"), default="text")
    editor_recovery.add_argument("--output", type=Path)
    editor_jobs = subparsers.add_parser(
        "editor-jobs-audit",
        help="Validate staged background generation, progress reporting, cancellation, and failure isolation.",
    )
    editor_jobs.add_argument("--format", choices=("text", "json"), default="text")
    editor_jobs.add_argument("--output", type=Path)
    project_bundle = subparsers.add_parser(
        "project-bundle-audit",
        help="Validate portable project bundles, tamper detection, and safe instance installation.",
    )
    project_bundle.add_argument("--format", choices=("text", "json"), default="text")
    project_bundle.add_argument("--output", type=Path)
    desktop_launcher = subparsers.add_parser(
        "desktop-launcher-audit",
        help="Validate launcher discovery, metadata parsing, editor launch plans, and instance selection.",
    )
    desktop_launcher.add_argument("--format", choices=("text", "json"), default="text")
    desktop_launcher.add_argument("--output", type=Path)
    native_distribution = subparsers.add_parser(
        "native-distribution-audit",
        help="Validate first-run preferences and standalone Windows/Linux build recipes.",
    )
    native_distribution.add_argument("--format", choices=("text", "json"), default="text")
    native_distribution.add_argument("--output", type=Path)
    desktop_packages = subparsers.add_parser(
        "desktop-packages-audit",
        help="Validate installer/AppImage plans and application update metadata.",
    )
    desktop_packages.add_argument("--format", choices=("text", "json"), default="text")
    desktop_packages.add_argument("--output", type=Path)
    application_updates = subparsers.add_parser(
        "application-update-client-audit",
        help="Validate secure update checks, downloads, checksums, and staging.",
    )
    application_updates.add_argument("--format", choices=("text", "json"), default="text")
    application_updates.add_argument("--output", type=Path)
    update_application = subparsers.add_parser(
        "update-application-audit",
        help="Validate verified update apply, rollback, and recovery behavior.",
    )
    update_application.add_argument("--format", choices=("text", "json"), default="text")
    update_application.add_argument("--output", type=Path)
    github_release = subparsers.add_parser(
        "github-release-publishing-audit",
        help="Validate deterministic GitHub release plans, asset checksums, and workflow automation.",
    )
    github_release.add_argument("--format", choices=("text", "json"), default="text")
    github_release.add_argument("--output", type=Path)
    release_attestation = subparsers.add_parser(
        "release-attestation-audit",
        help="Validate deterministic release SBOMs, provenance, and artifact bindings.",
    )
    release_attestation.add_argument("--format", choices=("text", "json"), default="text")
    release_attestation.add_argument("--output", type=Path)
    audit_performance = subparsers.add_parser(
        "audit-performance-audit",
        help="Validate audit timing instrumentation, execution uniqueness, and runtime budget.",
    )
    audit_performance.add_argument("--format", choices=("text", "json"), default="text")
    audit_performance.add_argument("--output", type=Path)
    audit_dependency = subparsers.add_parser(
        "audit-dependency-audit",
        help="Validate the audit dependency graph and execution ordering.",
    )
    audit_dependency.add_argument("--format", choices=("text", "json"), default="text")
    audit_dependency.add_argument("--output", type=Path)
    cli_exit_code = subparsers.add_parser(
        "cli-exit-code-audit",
        help="Validate audit command exit codes against JSON pass/fail status.",
    )
    cli_exit_code.add_argument("--format", choices=("text", "json"), default="text")
    cli_exit_code.add_argument("--output", type=Path)
    quality_gate = subparsers.add_parser(
        "quality-gate",
        help="Run every repository-safe release safeguard in one command.",
    )
    quality_gate.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    quality_gate.add_argument(
        "--output",
        type=Path,
        help="Write the combined quality report to a file.",
    )
    report_freshness = subparsers.add_parser(
        "report-freshness-guard",
        help="Verify checked-in audit reports match current repository results.",
    )
    report_freshness.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    report_freshness.add_argument(
        "--output",
        type=Path,
        help="Write the freshness report to a file.",
    )
    output_guard = subparsers.add_parser(
        "output-manifest-guard",
        help="Compare generated output with the checked-in file manifest.",
    )
    output_guard.add_argument(
        "baseline",
        nargs="?",
        type=Path,
        default=DEFAULT_OUTPUT_MANIFEST_PATH,
        help="Output manifest (default: reports/generated-output-manifest.json).",
    )
    output_guard.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    output_guard.add_argument(
        "--output",
        type=Path,
        help="Write the guard report to a file.",
    )
    output_baseline = subparsers.add_parser(
        "output-manifest",
        help="Safely refresh the checked-in generated output manifest.",
    )
    output_baseline.add_argument(
        "destination",
        nargs="?",
        type=Path,
        default=DEFAULT_OUTPUT_MANIFEST_PATH,
        help="Manifest destination (default: reports/generated-output-manifest.json).",
    )
    registry = subparsers.add_parser(
        "registry-audit",
        help="Verify quest item references against mod JARs or JSON registry exports.",
    )
    registry.add_argument(
        "sources",
        nargs="+",
        type=Path,
        help="JAR, ZIP, JSON file, or directory containing registry sources.",
    )
    registry.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when a covered item id is missing.",
    )
    registry.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    registry.add_argument(
        "--output",
        type=Path,
        help="Write the report to a file instead of standard output.",
    )
    release = subparsers.add_parser(
        "release-check",
        help="Build and run all repository-safe release validations in one command.",
    )
    release.add_argument(
        "--output",
        type=Path,
        help="Keep generated FTB Quests files at this destination instead of using a temporary directory.",
    )
    release.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    release.add_argument(
        "--report-output",
        type=Path,
        help="Write the release report to a file instead of standard output.",
    )
    guard = subparsers.add_parser(
        "release-guard",
        help="Run release-check and compare it with the protected release baseline.",
    )
    guard.add_argument(
        "baseline",
        nargs="?",
        type=Path,
        default=DEFAULT_BASELINE_PATH,
        help="Baseline release report (default: reports/release-baseline.json).",
    )
    guard.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    guard.add_argument(
        "--output",
        type=Path,
        help="Write the guard report to a file instead of standard output.",
    )
    guard.add_argument(
        "--build-output",
        type=Path,
        help="Keep generated FTB Quests files at this destination.",
    )
    baseline = subparsers.add_parser(
        "release-baseline",
        help="Safely refresh the checked-in release baseline after a clean release-check.",
    )
    baseline.add_argument(
        "destination",
        nargs="?",
        type=Path,
        default=DEFAULT_BASELINE_PATH,
        help="Baseline destination (default: reports/release-baseline.json).",
    )
    baseline.add_argument(
        "--build-output",
        type=Path,
        help="Keep generated FTB Quests files at this destination.",
    )
    compare = subparsers.add_parser(
        "release-compare",
        help="Compare two machine-readable release reports and detect regressions.",
    )
    compare.add_argument("baseline", type=Path, help="Earlier release-check JSON report.")
    compare.add_argument("current", type=Path, help="Current release-check JSON report.")
    compare.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    compare.add_argument(
        "--output",
        type=Path,
        help="Write the comparison report to a file instead of standard output.",
    )
    compare.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when regressions are detected.",
    )
    contract_guard = subparsers.add_parser(
        "contract-guard",
        help="Protect quest task, reward, icon, flag, and difficulty contracts.",
    )
    contract_guard.add_argument(
        "baseline",
        nargs="?",
        type=Path,
        default=DEFAULT_CONTRACT_BASELINE_PATH,
        help="Contract baseline (default: reports/quest-contract-baseline.json).",
    )
    contract_guard.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    contract_guard.add_argument(
        "--output",
        type=Path,
        help="Write the guard report to a file.",
    )
    contract_baseline = subparsers.add_parser(
        "contract-baseline",
        help="Refresh the checked-in quest contract baseline.",
    )
    contract_baseline.add_argument(
        "destination",
        nargs="?",
        type=Path,
        default=DEFAULT_CONTRACT_BASELINE_PATH,
        help="Baseline destination (default: reports/quest-contract-baseline.json).",
    )
    identity_guard = subparsers.add_parser(
        "identity-guard",
        help="Protect checked-in chapter and quest identities against accidental changes.",
    )
    identity_guard.add_argument(
        "baseline",
        nargs="?",
        type=Path,
        default=DEFAULT_IDENTITY_BASELINE_PATH,
        help="Identity baseline (default: reports/quest-identity-baseline.json).",
    )
    identity_guard.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    identity_guard.add_argument(
        "--output",
        type=Path,
        help="Write the guard report to a file.",
    )
    identity_baseline = subparsers.add_parser(
        "identity-baseline",
        help="Refresh the checked-in chapter and quest identity baseline.",
    )
    identity_baseline.add_argument(
        "destination",
        nargs="?",
        type=Path,
        default=DEFAULT_IDENTITY_BASELINE_PATH,
        help="Baseline destination (default: reports/quest-identity-baseline.json).",
    )
    manifest = subparsers.add_parser(
        "registry-manifest",
        help="Export every authored item reference grouped by namespace and usage.",
    )
    manifest.add_argument(
        "--output",
        type=Path,
        help="Write the JSON manifest to a file instead of standard output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    if args.command == "report-refresh":
        result = refresh_reports(
            args.directory,
            incremental=args.incremental,
            cache_path=args.cache,
        )
        rendered = result.format_json() if args.format == "json" else result.format()
        print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "audit-dependency-audit":
        result = run_audit_dependency_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "editor-model-audit":
        result = run_editor_model_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "editor-service-audit":
        result = run_editor_service_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "editor-ui-audit":
        result = run_editor_ui_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "editor-workspace-audit":
        result = run_editor_workspace_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "editor-recovery-audit":
        result = run_editor_recovery_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "editor-jobs-audit":
        result = run_editor_jobs_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "project-bundle-audit":
        result = run_project_bundle_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "desktop-launcher-audit":
        result = run_desktop_launcher_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "native-distribution-audit":
        result = run_native_distribution_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "desktop-packages-audit":
        result = run_desktop_packages_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "update-application-audit":
        result = run_update_application_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "release-attestation-audit":
        result = run_release_attestation_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "github-release-publishing-audit":
        result = run_github_release_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "application-update-client-audit":
        result = run_application_updates_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "audit-performance-audit":
        result = run_audit_performance_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-instance-discover":
        roots = (
            tuple(InstanceSearchRoot("Custom", path) for path in args.root) if args.root else None
        )
        result = discover_modpack_instances(roots, max_instances=args.max_instances)
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0

    if args.command == "quest-maker-launch":
        roots = (
            tuple(InstanceSearchRoot("Custom", path) for path in args.root) if args.root else None
        )
        try:
            return launch_desktop(
                workspace_root=args.workspace,
                search_roots=roots,
                open_browser=False if args.no_browser else None,
                preferences_path=args.preferences,
                force_first_run=args.reset_setup,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"Desktop launcher failed: {exc}")
            return 1

    if args.command == "quest-maker-setup":
        try:
            result = complete_first_run_setup(
                preferences_path=args.preferences,
                workspace_root=args.workspace,
                search_roots=args.root,
                open_browser=not args.no_browser,
                max_instances=args.max_instances,
            )
        except (OSError, TypeError, ValueError) as exc:
            print(f"Desktop setup failed: {exc}")
            return 1
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-maker-native-build":
        result = build_native_distribution(
            args.platform,
            destination=args.destination,
            dry_run=args.dry_run,
        )
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-maker-package-build":
        try:
            result = build_desktop_package(
                args.platform,
                args.version,
                native_directory=args.native_directory,
                destination=args.destination,
                dry_run=args.dry_run,
            )
        except (OSError, TypeError, ValueError) as exc:
            print(f"Desktop package build failed: {exc}")
            return 1
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-maker-update-metadata":
        try:
            artifacts = parse_artifact_specs(args.artifact)
            signing_key = args.signing_key.read_bytes() if args.signing_key else None
            metadata = create_update_metadata(
                args.version,
                args.channel,
                artifacts,
                base_url=args.base_url,
                signing_key=signing_key,
                key_id=args.key_id,
            )
            result = write_update_metadata(metadata, args.destination)
        except (OSError, TypeError, ValueError) as exc:
            print(f"Update metadata generation failed: {exc}")
            return 1
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-maker-update-verify":
        try:
            signing_key = args.signing_key.read_bytes() if args.signing_key else None
            result = verify_update_metadata(
                args.metadata,
                artifact_directory=args.artifact_directory,
                signing_key=signing_key,
            )
        except (OSError, TypeError, ValueError) as exc:
            print(f"Update metadata verification failed: {exc}")
            return 1
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-maker-update-check":
        try:
            signing_key = args.signing_key.read_bytes() if args.signing_key else None
            result = check_for_application_update(
                args.source,
                args.current_version,
                channel=args.channel,
                platform=args.platform,
                signing_key=signing_key,
                require_signature=args.require_signature,
                max_metadata_bytes=args.max_metadata_bytes,
                timeout=args.timeout,
            )
        except (OSError, TypeError, ValueError) as exc:
            print(f"Application update check failed: {exc}")
            return 1
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-maker-update-apply":
        result = apply_staged_update(
            args.manifest, current_executable=args.current_executable, execute=args.execute
        )
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-maker-update-rollback":
        result = rollback_applied_update(args.manifest, execute=args.execute)
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command in ("quest-maker-github-release-plan", "quest-maker-github-release-publish"):
        try:
            plan = create_github_release_plan(
                args.repository, args.tag, args.asset, notes_file=args.notes,
                title=args.title, prerelease=args.prerelease, draft=args.draft,
            )
            result = (
                publish_github_release(plan, execute=args.execute)
                if args.command == "quest-maker-github-release-publish"
                else plan
            )
        except (OSError, TypeError, ValueError) as exc:
            print(f"GitHub release publishing failed: {exc}")
            return 1
        rendered = result.format_json()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-maker-release-sbom":
        try:
            components = []
            for item in args.component:
                if "==" not in item:
                    raise ValueError("components must use NAME==VERSION")
                components.append(tuple(item.split("==", 1)))
            payload = create_cyclonedx_sbom(args.artifact, version=args.version, components=components)
            output = write_json_document(args.output, payload)
        except (OSError, TypeError, ValueError) as exc:
            print(f"Release SBOM generation failed: {exc}")
            return 1
        print(output)
        return 0

    if args.command == "quest-maker-release-provenance":
        try:
            payload = create_slsa_provenance(
                args.artifact, repository=args.repository, revision=args.revision, workflow=args.workflow
            )
            output = write_json_document(args.output, payload)
        except (OSError, TypeError, ValueError) as exc:
            print(f"Release provenance generation failed: {exc}")
            return 1
        print(output)
        return 0

    if args.command == "quest-maker-update-stage":
        try:
            signing_key = args.signing_key.read_bytes() if args.signing_key else None
            check = check_for_application_update(
                args.source,
                args.current_version,
                channel=args.channel,
                platform=args.platform,
                signing_key=signing_key,
                require_signature=args.require_signature,
                max_metadata_bytes=args.max_metadata_bytes,
                timeout=args.timeout,
            )
            result = stage_application_update(
                check,
                destination=args.destination,
                max_artifact_bytes=args.max_artifact_bytes,
                timeout=args.timeout,
            )
        except (OSError, TypeError, ValueError) as exc:
            print(f"Application update staging failed: {exc}")
            return 1
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "modpack-scan":
        result = scan_modpack(args.path)
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "modpack-content-scan":
        result = scan_modpack_content(args.path, candidate_limit=args.candidate_limit)
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-blueprint":
        result = generate_quest_blueprint(
            args.path,
            target_quests=args.target_quests,
            chapter_size=args.chapter_size,
        )
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-description-plan":
        result = generate_quest_description_plan(
            args.path,
            target_quests=args.target_quests,
            chapter_size=args.chapter_size,
            style=args.style,
        )
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-reward-plan":
        result = generate_quest_reward_plan(
            args.path,
            target_quests=args.target_quests,
            chapter_size=args.chapter_size,
            policy=args.policy,
            description_style=args.description_style,
        )
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-editor-model":
        result = generate_editor_model(
            args.path,
            target_quests=args.target_quests,
            chapter_size=args.chapter_size,
            description_style=args.description_style,
            reward_policy=args.reward_policy,
        )
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-project-bundle":
        document = generate_editor_model(
            args.path,
            target_quests=args.target_quests,
            chapter_size=args.chapter_size,
            description_style=args.description_style,
            reward_policy=args.reward_policy,
        )
        result = create_project_bundle(
            document,
            args.destination,
            settings={
                "target_quests": args.target_quests,
                "chapter_size": args.chapter_size,
                "description_style": args.description_style,
                "reward_policy": args.reward_policy,
            },
        )
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-project-inspect":
        result = inspect_project_bundle(args.bundle)
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-project-install":
        result = install_project_bundle(
            args.bundle,
            args.instance,
            backup=not args.no_backup,
            dry_run=args.dry_run,
            force=args.force,
        )
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-editor-serve":
        try:
            return serve_editor(
                args.path,
                workspace=args.workspace,
                host=args.host,
                port=args.port,
                target_quests=args.target_quests,
                chapter_size=args.chapter_size,
                description_style=args.description_style,
                reward_policy=args.reward_policy,
                open_browser=not args.no_browser,
            )
        except (OSError, TypeError, ValueError) as exc:
            print(f"Editor service failed: {exc}")
            return 1

    if args.command == "ftb-quest-export":
        result = export_modpack_questbook(
            args.path,
            args.destination,
            target_quests=args.target_quests,
            chapter_size=args.chapter_size,
            description_style=args.description_style,
            reward_policy=args.reward_policy,
        )
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "questbook-review":
        result = review_modpack_questbook(
            args.path,
            target_quests=args.target_quests,
            chapter_size=args.chapter_size,
            low_confidence_threshold=args.low_confidence_threshold,
            min_description_words=args.min_description_words,
            max_chapter_quests=args.max_chapter_quests,
            bottleneck_dependents=args.bottleneck_dependents,
            description_style=args.description_style,
            reward_policy=args.reward_policy,
        )
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "modpack-scanner-audit":
        result = run_modpack_scanner_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "modpack-content-scanner-audit":
        result = run_modpack_content_scanner_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "progression-planner-audit":
        result = run_progression_planner_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "ftb-blueprint-exporter-audit":
        result = run_ftb_blueprint_exporter_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "questbook-review-audit":
        result = run_questbook_review_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "reward-planner-audit":
        result = run_reward_planner_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quest-description-audit":
        result = run_quest_description_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "mod-compatibility-audit":
        result = run_mod_compatibility_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "release-archive-compression-audit":
        result = run_release_archive_compression_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "release-archive-unicode-path-audit":
        result = run_release_archive_unicode_path_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "release-archive-extraction-safety-audit":
        result = run_release_archive_extraction_safety_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "release-archive-metadata-audit":
        result = run_release_archive_metadata_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "release-manifest-audit":
        result = run_release_manifest_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "release-package-verification-audit":
        result = run_release_package_verification_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "release-report-finalization-audit":
        result = run_release_report_finalization_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "report-refresh-cache-audit":
        result = run_report_refresh_cache_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "report-refresh-idempotence-audit":
        result = run_report_refresh_idempotence_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "report-refresh-convergence-audit":
        result = run_report_refresh_convergence_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "report-refresh-audit":
        result = run_report_refresh_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "report-refresh-order-audit":
        result = run_report_refresh_order_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "report-write-safety-audit":
        result = run_report_write_safety_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "cli-exit-code-audit":
        result = run_cli_exit_code_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "cli-output-audit":
        result = run_cli_output_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "report-determinism-audit":
        result = run_report_determinism_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "report-provenance-audit":
        result = run_report_provenance_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "report-consistency-audit":
        result = run_report_consistency_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "report-schema-audit":
        result = run_report_schema_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "test-inventory-audit":
        result = run_test_inventory_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "audit-registry-audit":
        result = run_audit_registry_contract()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "release-reproducibility-audit":
        result = run_release_reproducibility_audit()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "release-artifact-audit":
        result = run_release_artifact_audit()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "repository-hygiene-audit":
        result = run_repository_hygiene_audit()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "documentation-audit":
        result = run_documentation_audit()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "cli-audit":
        result = run_cli_audit()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "packaging-audit":
        result = run_packaging_audit()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "quality-gate":
        result = run_quality_gate()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "report-freshness-guard":
        result = run_report_freshness_guard()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "output-manifest-guard":
        try:
            result = run_output_manifest_guard(args.baseline)
        except ValueError as exc:
            print(exc)
            return 2
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "output-manifest":
        try:
            manifest = refresh_output_manifest(args.destination)
        except ValueError as exc:
            print(exc)
            return 1
        print(
            f"Generated output manifest refreshed: {args.destination} "
            f"({manifest.file_count} files, {manifest.total_bytes} bytes)."
        )
        return 0

    if args.command == "contract-guard":
        try:
            result = run_contract_guard(args.baseline)
        except ValueError as exc:
            print(exc)
            return 2
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "contract-baseline":
        manifest = refresh_contract_baseline(args.destination)
        print(
            f"Quest contract baseline refreshed: {args.destination} "
            f"({manifest.quest_count} quests, {manifest.task_count} tasks, "
            f"{manifest.reward_count} rewards)."
        )
        return 0
    if args.command == "identity-guard":
        try:
            result = run_identity_guard(args.baseline)
        except ValueError as exc:
            print(exc)
            return 2
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "identity-baseline":
        manifest = refresh_identity_baseline(args.destination)
        print(
            f"Quest identity baseline refreshed: {args.destination} "
            f"({manifest.chapter_count} chapters, {manifest.quest_count} quests)."
        )
        return 0

    if args.command == "release-check":
        report = run_release_check(args.output)
        rendered = report.format_json() if args.format == "json" else report.format()
        if args.report_output:
            atomic_write_text(args.report_output, rendered + "\n")
        else:
            print(rendered)
        return 0 if report.is_clean else 1

    if args.command == "release-guard":
        try:
            result = run_release_guard(args.baseline, args.build_output)
        except ValueError as exc:
            print(exc)
            return 2
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "release-baseline":
        try:
            report = refresh_release_baseline(args.destination, args.build_output)
        except ValueError as exc:
            print(exc)
            return 1
        print(
            f"Release baseline refreshed: {args.destination} "
            f"({report.chapters} chapters, {report.quests} quests)."
        )
        return 0

    if args.command == "release-compare":
        try:
            comparison = compare_release_reports(
                load_release_report(args.baseline),
                load_release_report(args.current),
            )
        except ValueError as exc:
            print(exc)
            return 2
        rendered = comparison.format_json() if args.format == "json" else comparison.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if comparison.is_clean or not args.strict else 1

    if args.command == "dependency-audit":
        report = audit_dependencies(create_project())
        rendered = report.format_json() if args.format == "json" else report.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if report.is_clean or not args.strict else 1

    if args.command == "dependency-graph":
        graph = build_dependency_graph(create_project())
        rendered = graph.format_json() if args.format == "json" else graph.format_dot()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0

    if args.command == "progression-metrics":
        try:
            report = analyze_progression(create_project())
        except ValueError as exc:
            print(exc)
            return 2
        rendered = report.format_json() if args.format == "json" else report.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0

    if args.command == "progression-guard":
        try:
            result = run_progression_guard(args.budget)
        except ValueError as exc:
            print(exc)
            return 2
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "reward-audit":
        result = run_reward_audit()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean or not args.strict else 1

    if args.command == "task-audit":
        result = run_task_audit()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean or not args.strict else 1

    if args.command == "chapter-audit":
        result = run_chapter_audit()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean or not args.strict else 1

    if args.command == "text-audit":
        result = run_text_audit()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean or not args.strict else 1

    if args.command == "determinism-audit":
        result = run_determinism_audit()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            atomic_write_text(args.output, rendered + "\n")
        else:
            print(rendered)
        return 0 if result.is_clean or not args.strict else 1

    if args.command == "registry-audit":
        audit = audit_registry(create_project(), args.sources)
        report = audit.format_json() if args.format == "json" else audit.format()
        if args.output:
            atomic_write_text(args.output, report + "\n")
        else:
            print(report)
        return 0 if audit.is_clean or not args.strict else 1

    if args.command == "registry-manifest":
        manifest = format_reference_manifest(create_project())
        if args.output:
            atomic_write_text(args.output, manifest + "\n")
        else:
            print(manifest)
        return 0

    if args.command == "audit":
        audit = audit_project(create_project())
        print(audit.format())
        return 0 if audit.is_clean or not args.strict else 1

    if args.command != "lint":
        build()
        return 0

    project = FTBQuestParser().load(args.path)
    report = ProjectValidator().validate(project)

    for issue in report.issues:
        print(issue.format())

    print(
        f"Checked {len(project.chapters)} chapter(s) and {len(project.quests)} quest(s): "
        f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)."
    )
    return 0 if report.is_valid else 1
