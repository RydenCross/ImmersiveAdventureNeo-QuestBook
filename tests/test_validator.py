from uuid import uuid4

from generator.validator import ProjectValidator, Severity
from model import Chapter, Dependency, Position, Project, Quest, Task, TaskType


def quest(quest_id: str, dependencies: list[str] | None = None) -> Quest:
    return Quest(
        id=quest_id,
        uuid=uuid4(),
        title=quest_id,
        description="",
        icon="minecraft:book",
        tasks=[Task(id=f"{quest_id}-task", type=TaskType.CHECKMARK)],
        dependencies=[Dependency(value) for value in dependencies or []],
        position=Position(0, 0),
    )


def project_with(*quests: Quest) -> Project:
    chapter = Chapter("test", uuid4(), "Test", "minecraft:book")
    for item in quests:
        chapter.add_quest(item)
    project = Project("Test", "13")
    project.add_chapter(chapter)
    return project


def codes(project: Project) -> set[str]:
    return {issue.code for issue in ProjectValidator().validate(project).issues}


def test_valid_project_has_no_errors() -> None:
    report = ProjectValidator().validate(project_with(quest("A"), quest("B", ["A"])))
    assert report.is_valid
    assert report.errors == ()


def test_missing_dependency_is_error() -> None:
    assert "MISSING_DEPENDENCY" in codes(project_with(quest("A", ["MISSING"])))


def test_dependency_cycle_is_error() -> None:
    assert "DEPENDENCY_CYCLE" in codes(project_with(quest("A", ["B"]), quest("B", ["A"])))


def test_empty_quest_is_warning() -> None:
    item = quest("A")
    item.tasks.clear()
    report = ProjectValidator().validate(project_with(item))
    assert any(
        issue.code == "EMPTY_QUEST" and issue.severity is Severity.WARNING
        for issue in report.issues
    )


def test_duplicate_quest_ids_across_chapters_are_rejected() -> None:
    first = Chapter("first", uuid4(), "First", "minecraft:book", quests=[quest("A")])
    second = Chapter("second", uuid4(), "Second", "minecraft:book", quests=[quest("A")])
    project = Project("Test", "13", chapters=[first, second])
    assert "DUPLICATE_QUEST_ID" in codes(project)
