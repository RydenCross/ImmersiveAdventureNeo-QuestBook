from __future__ import annotations

from pathlib import Path

from content import create_project
from generator.config import OUTPUT
from generator.log import Level, log
from generator.validator import ProjectValidator
from generator.version import VERSION
from generator.writer import FTBQuestWriter


def build(output: Path | None = None) -> Path:
    log(Level.INFO, f"Immersive Adventure Neo Quest Builder {VERSION}")
    project = create_project()
    report = ProjectValidator().validate(project)

    for issue in report.issues:
        log(Level.WARNING if issue.severity.value == "warning" else Level.ERROR, issue.format())
    if not report.is_valid:
        raise ValueError(f"Quest project contains {len(report.errors)} validation error(s).")

    destination = output or OUTPUT / "config" / "ftbquests"
    quests_root = FTBQuestWriter().write(project, destination)
    log(
        Level.SUCCESS,
        f"Generated {len(project.chapters)} chapter(s) and {len(project.quests)} quest(s).",
    )
    log(Level.SUCCESS, f"Wrote FTB Quests files to {quests_root}")
    return quests_root


if __name__ == "__main__":
    build()
