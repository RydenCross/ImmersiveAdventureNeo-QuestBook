from content import create_project
from generator.validator import ProjectValidator


def test_generated_project_is_valid() -> None:
    project = create_project()
    report = ProjectValidator().validate(project)

    assert report.is_valid
    assert len(project.chapters) == 3
    assert len(project.quests) == 64


def test_quest_ids_are_stable() -> None:
    first = create_project()
    second = create_project()

    assert [quest.ftb_id for quest in first.quests] == [quest.ftb_id for quest in second.quests]


def test_survival_chapter_depends_on_welcome_completion() -> None:
    project = create_project()
    welcome = project.get_chapter("00_welcome")
    survival = project.get_chapter("01_survival")

    assert welcome is not None
    assert survival is not None
    assert survival.quests[0].dependencies[0].quest_id == welcome.quests[-1].ftb_id


def test_mining_chapter_depends_on_survival_completion() -> None:
    project = create_project()
    survival = project.get_chapter("01_survival")
    mining = project.get_chapter("02_mining")

    assert survival is not None
    assert mining is not None
    assert mining.quests[0].dependencies[0].quest_id == survival.quests[-1].ftb_id
