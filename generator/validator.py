from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
import re

from model import Project

_RESOURCE_LOCATION = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    severity: Severity
    code: str
    message: str
    location: str | None = None

    def format(self) -> str:
        where = f" [{self.location}]" if self.location else ""
        return f"{self.severity.value.upper()} {self.code}{where}: {self.message}"


@dataclass(frozen=True, slots=True)
class ValidationReport:
    issues: tuple[ValidationIssue, ...]

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is Severity.ERROR)

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(issue for issue in self.issues if issue.severity is Severity.WARNING)

    @property
    def is_valid(self) -> bool:
        return not self.errors


class ProjectValidator:
    def validate(self, project: Project) -> ValidationReport:
        issues: list[ValidationIssue] = []
        quest_locations: dict[str, str] = {}

        chapter_ids: set[str] = set()
        chapter_ftb_ids: set[str] = set()
        for chapter in project.chapters:
            location = f"chapter:{chapter.id}"
            if chapter.id in chapter_ids:
                issues.append(
                    self._error(
                        "DUPLICATE_CHAPTER_ID", f"Duplicate chapter id '{chapter.id}'.", location
                    )
                )
            chapter_ids.add(chapter.id)

            if chapter.ftb_id:
                if chapter.ftb_id in chapter_ftb_ids:
                    issues.append(
                        self._error(
                            "DUPLICATE_CHAPTER_FTB_ID",
                            f"Duplicate chapter FTB id '{chapter.ftb_id}'.",
                            location,
                        )
                    )
                chapter_ftb_ids.add(chapter.ftb_id)

            self._validate_resource(chapter.icon, "chapter icon", location, issues)

            for quest in chapter.quests:
                quest_location = f"{location}/quest:{quest.id}"
                if quest.id in quest_locations:
                    issues.append(
                        self._error(
                            "DUPLICATE_QUEST_ID",
                            f"Quest id '{quest.id}' also appears at {quest_locations[quest.id]}.",
                            quest_location,
                        )
                    )
                else:
                    quest_locations[quest.id] = quest_location

                self._validate_quest(quest, quest_location, issues)

        known_quests = set(quest_locations)
        for chapter in project.chapters:
            for quest in chapter.quests:
                location = f"chapter:{chapter.id}/quest:{quest.id}"
                for dependency in quest.dependencies:
                    if dependency.quest_id not in known_quests:
                        issues.append(
                            self._error(
                                "MISSING_DEPENDENCY",
                                f"Dependency '{dependency.quest_id}' does not exist.",
                                location,
                            )
                        )
                    if dependency.quest_id == quest.id:
                        issues.append(
                            self._error("SELF_DEPENDENCY", "Quest depends on itself.", location)
                        )

        issues.extend(self._find_cycles(project, known_quests))
        return ValidationReport(tuple(issues))

    def _validate_quest(self, quest, location: str, issues: list[ValidationIssue]) -> None:
        self._validate_resource(quest.icon, "quest icon", location, issues)

        if not isfinite(quest.position.x) or not isfinite(quest.position.y):
            issues.append(
                self._error(
                    "INVALID_POSITION", "Quest coordinates must be finite numbers.", location
                )
            )

        if not quest.tasks:
            issues.append(self._warning("EMPTY_QUEST", "Quest has no tasks.", location))

        self._duplicate_child_ids(quest.tasks, "task", location, issues)
        self._duplicate_child_ids(quest.rewards, "reward", location, issues)

    @staticmethod
    def _duplicate_child_ids(
        children, kind: str, location: str, issues: list[ValidationIssue]
    ) -> None:
        seen: set[str] = set()
        for child in children:
            if child.id in seen:
                issues.append(
                    ValidationIssue(
                        Severity.ERROR,
                        f"DUPLICATE_{kind.upper()}_ID",
                        f"Duplicate {kind} id '{child.id}'.",
                        location,
                    )
                )
            seen.add(child.id)

    @staticmethod
    def _validate_resource(
        value: str, label: str, location: str, issues: list[ValidationIssue]
    ) -> None:
        if not _RESOURCE_LOCATION.fullmatch(value):
            issues.append(
                ValidationIssue(
                    Severity.WARNING,
                    "INVALID_RESOURCE_LOCATION",
                    f"{label.capitalize()} '{value}' is not a standard namespace:path resource location.",
                    location,
                )
            )

    def _find_cycles(self, project: Project, known_quests: set[str]) -> list[ValidationIssue]:
        graph = {
            quest.id: [dep.quest_id for dep in quest.dependencies if dep.quest_id in known_quests]
            for quest in project.quests
        }
        state: dict[str, int] = {}
        stack: list[str] = []
        reported: set[frozenset[str]] = set()
        issues: list[ValidationIssue] = []

        def visit(node: str) -> None:
            state[node] = 1
            stack.append(node)
            for parent in graph.get(node, []):
                if state.get(parent, 0) == 0:
                    visit(parent)
                elif state.get(parent) == 1:
                    start = stack.index(parent)
                    cycle = stack[start:] + [parent]
                    key = frozenset(cycle)
                    if key not in reported:
                        reported.add(key)
                        issues.append(
                            self._error(
                                "DEPENDENCY_CYCLE",
                                "Dependency cycle detected: " + " -> ".join(cycle),
                                f"quest:{node}",
                            )
                        )
            stack.pop()
            state[node] = 2

        for quest_id in graph:
            if state.get(quest_id, 0) == 0:
                visit(quest_id)
        return issues

    @staticmethod
    def _error(code: str, message: str, location: str | None = None) -> ValidationIssue:
        return ValidationIssue(Severity.ERROR, code, message, location)

    @staticmethod
    def _warning(code: str, message: str, location: str | None = None) -> ValidationIssue:
        return ValidationIssue(Severity.WARNING, code, message, location)
