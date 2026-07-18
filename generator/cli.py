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
from generator.release_package_verification_contract import run_release_package_verification_contract
from generator.release_manifest_contract import run_release_manifest_contract
from generator.release_archive_metadata_contract import run_release_archive_metadata_contract
from generator.release_archive_extraction_safety_contract import run_release_archive_extraction_safety_contract
from generator.release_archive_unicode_path_contract import run_release_archive_unicode_path_contract
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
    release_archive_extraction_safety.add_argument("--format", choices=("text", "json"), default="text")
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
    modpack_scan.add_argument("path", type=Path, help="Modpack ZIP/MRPACK, instance folder, or mods directory.")
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
    modpack_content_scan.add_argument("--output", type=Path, help="Write the content profile to a file.")
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
        "--target-quests", type=int, help="Desired quest count (default: pack-profile recommendation)."
    )
    quest_description_plan.add_argument(
        "--chapter-size", type=int, default=40, help="Maximum quests per generated chapter (default: 40)."
    )
    quest_description_plan.add_argument(
        "--style", choices=DESCRIPTION_STYLES, default="guided",
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
        "--target-quests", type=int, help="Desired quest count (default: pack-profile recommendation)."
    )
    quest_reward_plan.add_argument(
        "--chapter-size", type=int, default=40, help="Maximum quests per generated chapter (default: 40)."
    )
    quest_reward_plan.add_argument(
        "--policy", choices=REWARD_POLICIES, default="conservative",
        help="Reward density policy (default: conservative).",
    )
    quest_reward_plan.add_argument(
        "--description-style", choices=DESCRIPTION_STYLES, default="guided",
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
        "--target-quests", type=int, help="Desired quest count (default: pack-profile recommendation)."
    )
    quest_editor_model.add_argument(
        "--chapter-size", type=int, default=40, help="Maximum quests per generated chapter (default: 40)."
    )
    quest_editor_model.add_argument(
        "--description-style", choices=DESCRIPTION_STYLES, default="guided",
        help="Description detail level applied before editor conversion (default: guided).",
    )
    quest_editor_model.add_argument(
        "--reward-policy", choices=("unassigned", *REWARD_POLICIES), default="unassigned",
        help="Optional generated reward policy stored in the editor document (default: unassigned).",
    )
    quest_editor_model.add_argument("--format", choices=("text", "json"), default="text")
    quest_editor_model.add_argument(
        "--output", type=Path, help="Write the editor document to a file."
    )
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
        "--target-quests", type=int, help="Desired quest count (default: pack-profile recommendation)."
    )
    ftb_quest_export.add_argument(
        "--chapter-size", type=int, default=40, help="Maximum quests per generated chapter (default: 40)."
    )
    ftb_quest_export.add_argument(
        "--description-style", choices=DESCRIPTION_STYLES, default="guided",
        help="Description detail level applied before export (default: guided).",
    )
    ftb_quest_export.add_argument(
        "--reward-policy", choices=("unassigned", *REWARD_POLICIES), default="unassigned",
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
        "--target-quests", type=int, help="Desired quest count (default: pack-profile recommendation)."
    )
    questbook_review.add_argument(
        "--chapter-size", type=int, default=40, help="Planner chapter size (default: 40)."
    )
    questbook_review.add_argument(
        "--low-confidence-threshold", type=float, default=0.75,
        help="Flag quests below this confidence score (default: 0.75).",
    )
    questbook_review.add_argument(
        "--min-description-words", type=int, default=6,
        help="Minimum recommended description length (default: 6 words).",
    )
    questbook_review.add_argument(
        "--max-chapter-quests", type=int, default=50,
        help="Flag chapters above this size (default: 50).",
    )
    questbook_review.add_argument(
        "--bottleneck-dependents", type=int, default=8,
        help="Flag quests directly gating at least this many quests (default: 8).",
    )
    questbook_review.add_argument(
        "--description-style", choices=DESCRIPTION_STYLES, default="guided",
        help="Description detail level applied before review (default: guided).",
    )
    questbook_review.add_argument(
        "--reward-policy", choices=("unassigned", *REWARD_POLICIES), default="unassigned",
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

    if args.command == "audit-performance-audit":
        result = run_audit_performance_contract()
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
