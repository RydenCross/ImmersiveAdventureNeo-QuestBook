from __future__ import annotations

import argparse
from pathlib import Path

from generator.build import build
from generator.parser import FTBQuestParser
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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
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
