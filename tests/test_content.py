from content import create_project
from generator.validator import ProjectValidator


def test_welcome_project_is_valid() -> None:
    project = create_project()
    report = ProjectValidator().validate(project)

    assert report.is_valid
    assert len(project.chapters) == 1
    assert len(project.quests) == 9


def test_welcome_quest_ids_are_stable() -> None:
    first = create_project()
    second = create_project()

    assert [quest.ftb_id for quest in first.quests] == [quest.ftb_id for quest in second.quests]
