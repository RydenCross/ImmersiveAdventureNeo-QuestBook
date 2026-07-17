from __future__ import annotations

import argparse
from pathlib import Path

from content import create_project
from generator.audit import audit_project
from generator.build import build
from generator.parser import FTBQuestParser
from generator.registry_audit import audit_registry
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    if args.command == "registry-audit":
        audit = audit_registry(create_project(), args.sources)
        print(audit.format())
        return 0 if audit.is_clean or not args.strict else 1

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
