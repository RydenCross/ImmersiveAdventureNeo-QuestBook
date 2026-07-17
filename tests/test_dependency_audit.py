import json
from uuid import uuid4

from content import create_project
from generator.cli import main
from generator.dependency_audit import audit_dependencies
from model.chapter import Chapter
from model.dependency import Dependency
from model.project import Project
from model.quest import Quest


def quest(quest_id: str, *dependencies: str) -> Quest:
    return Quest(
        id=quest_id,
        uuid=uuid4(),
        title=quest_id,
        description="Test quest.",
        icon="minecraft:stone",
        dependencies=[Dependency(value) for value in dependencies],
    )


def project_with(*quests: Quest) -> Project:
    chapter = Chapter("chapter", uuid4(), "Chapter", "minecraft:book", list(quests))
    return Project("Test", "1", [chapter])


def test_authored_project_dependency_graph_is_clean() -> None:
    report = audit_dependencies(create_project())
    assert report.is_clean
    assert report.quests == 656
    assert report.dependencies == 867
    assert not report.cycles
    assert not report.unreachable_quests


def test_detects_cycle_and_unreachable_quests() -> None:
    report = audit_dependencies(project_with(quest("a", "b"), quest("b", "a")))
    assert report.cycles == (("a", "b", "a"),)
    assert report.unreachable_quests == ("a", "b")
    assert not report.is_clean


def test_detects_duplicate_dependency() -> None:
    report = audit_dependencies(project_with(quest("root"), quest("child", "root", "root")))
    assert report.duplicate_dependencies == ("child -> root",)
    assert not report.is_clean


def test_cli_writes_json_report(tmp_path) -> None:
    output = tmp_path / "dependency-audit.json"
    assert main(["dependency-audit", "--format", "json", "--output", str(output), "--strict"]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert payload["quests"] == 656
