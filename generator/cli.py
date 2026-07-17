from __future__ import annotations

import argparse
from pathlib import Path

from content import create_project
from generator.audit import audit_project
from generator.build import build
from generator.dependency_audit import audit_dependencies
from generator.dependency_graph import build_dependency_graph
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
from generator.parser import FTBQuestParser
from generator.progression_guard import DEFAULT_BUDGET_PATH, run_progression_guard
from generator.progression_metrics import analyze_progression
from generator.registry_audit import audit_registry, format_reference_manifest
from generator.reward_audit import run_reward_audit
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
    audit = subparsers.add_parser("audit", help="Summarize authored quest content quality and coverage.")
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
        "--format", choices=("text", "json"), default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    dependency.add_argument(
        "--output", type=Path, help="Write the report to a file instead of standard output."
    )
    dependency.add_argument(
        "--strict", action="store_true",
        help="Return a non-zero exit code when progression defects are detected.",
    )
    graph = subparsers.add_parser(
        "dependency-graph",
        help="Export the authored quest progression graph as Graphviz DOT or JSON.",
    )
    graph.add_argument(
        "--format", choices=("dot", "json"), default="dot",
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
        "--format", choices=("text", "json"), default="text",
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
        "--format", choices=("text", "json"), default="text",
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
        "--format", choices=("text", "json"), default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    reward_audit.add_argument(
        "--output", type=Path, help="Write the reward audit report to a file.",
    )
    reward_audit.add_argument(
        "--strict", action="store_true",
        help="Return a non-zero exit code when structural reward defects are detected.",
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
        "--format", choices=("text", "json"), default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    guard.add_argument(
        "--output", type=Path,
        help="Write the guard report to a file instead of standard output.",
    )
    guard.add_argument(
        "--build-output", type=Path,
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
        "--build-output", type=Path,
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
        "baseline", nargs="?", type=Path, default=DEFAULT_CONTRACT_BASELINE_PATH,
        help="Contract baseline (default: reports/quest-contract-baseline.json).",
    )
    contract_guard.add_argument(
        "--format", choices=("text", "json"), default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    contract_guard.add_argument(
        "--output", type=Path, help="Write the guard report to a file.",
    )
    contract_baseline = subparsers.add_parser(
        "contract-baseline",
        help="Refresh the checked-in quest contract baseline.",
    )
    contract_baseline.add_argument(
        "destination", nargs="?", type=Path, default=DEFAULT_CONTRACT_BASELINE_PATH,
        help="Baseline destination (default: reports/quest-contract-baseline.json).",
    )
    identity_guard = subparsers.add_parser(
        "identity-guard",
        help="Protect checked-in chapter and quest identities against accidental changes.",
    )
    identity_guard.add_argument(
        "baseline", nargs="?", type=Path, default=DEFAULT_IDENTITY_BASELINE_PATH,
        help="Identity baseline (default: reports/quest-identity-baseline.json).",
    )
    identity_guard.add_argument(
        "--format", choices=("text", "json"), default="text",
        help="Select human-readable text or machine-readable JSON output.",
    )
    identity_guard.add_argument(
        "--output", type=Path, help="Write the guard report to a file.",
    )
    identity_baseline = subparsers.add_parser(
        "identity-baseline",
        help="Refresh the checked-in chapter and quest identity baseline.",
    )
    identity_baseline.add_argument(
        "destination", nargs="?", type=Path, default=DEFAULT_IDENTITY_BASELINE_PATH,
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
    if args.command == "contract-guard":
        try:
            result = run_contract_guard(args.baseline)
        except ValueError as exc:
            print(exc)
            return 2
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
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
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
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
            args.report_output.parent.mkdir(parents=True, exist_ok=True)
            args.report_output.write_text(rendered + "\n", encoding="utf-8")
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
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
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
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 0 if comparison.is_clean or not args.strict else 1

    if args.command == "dependency-audit":
        report = audit_dependencies(create_project())
        rendered = report.format_json() if args.format == "json" else report.format()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 0 if report.is_clean or not args.strict else 1

    if args.command == "dependency-graph":
        graph = build_dependency_graph(create_project())
        rendered = graph.format_json() if args.format == "json" else graph.format_dot()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
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
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
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
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 0 if result.is_clean else 1

    if args.command == "reward-audit":
        result = run_reward_audit()
        rendered = result.format_json() if args.format == "json" else result.format()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 0 if result.is_clean or not args.strict else 1

    if args.command == "registry-audit":
        audit = audit_registry(create_project(), args.sources)
        report = audit.format_json() if args.format == "json" else audit.format()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(report + "\n", encoding="utf-8")
        else:
            print(report)
        return 0 if audit.is_clean or not args.strict else 1

    if args.command == "registry-manifest":
        manifest = format_reference_manifest(create_project())
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(manifest + "\n", encoding="utf-8")
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
