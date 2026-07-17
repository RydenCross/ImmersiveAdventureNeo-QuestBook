from __future__ import annotations

import argparse
from pathlib import Path

from content import create_project
from generator.audit import audit_project
from generator.build import build
from generator.parser import FTBQuestParser
from generator.registry_audit import audit_registry, format_reference_manifest
from generator.release_check import run_release_check
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
    if args.command == "release-check":
        report = run_release_check(args.output)
        print(report.format())
        return 0 if report.is_clean else 1

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
