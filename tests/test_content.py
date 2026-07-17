from content import create_project
from generator.validator import ProjectValidator


def test_generated_project_is_valid() -> None:
    project = create_project()
    report = ProjectValidator().validate(project)

    assert report.is_valid
    assert len(project.chapters) == 6
    assert len(project.quests) == 186


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


def test_exploration_chapter_depends_on_survival_completion() -> None:
    project = create_project()
    survival = project.get_chapter("01_survival")
    exploration = project.get_chapter("03_exploration")

    assert survival is not None
    assert exploration is not None
    assert exploration.quests[0].dependencies[0].quest_id == survival.quests[-1].ftb_id


def test_create_chapter_depends_on_mining_completion() -> None:
    project = create_project()
    mining = project.get_chapter("02_mining")
    create = project.get_chapter("04_create")

    assert mining is not None
    assert create is not None
    assert create.quests[0].dependencies[0].quest_id == mining.quests[-1].ftb_id
    assert len(create.quests) == 74


def test_create_processing_follows_foundations() -> None:
    project = create_project()
    create = project.get_chapter("04_create")

    assert create is not None
    foundations = next(q for q in create.quests if q.title == "Ready for Mechanical Processing")
    millstone = next(q for q in create.quests if q.title == "Grinding Gears")
    processing = next(q for q in create.quests if q.title == "A Working Processing Line")

    assert millstone.dependencies[0].quest_id == foundations.ftb_id
    assert create.quests.index(processing) < len(create.quests) - 1


def test_create_automation_follows_processing() -> None:
    project = create_project()
    create = project.get_chapter("04_create")

    assert create is not None
    processing = next(q for q in create.quests if q.title == "A Working Processing Line")
    belt = next(q for q in create.quests if q.title == "Keep Things Moving")
    complete = next(q for q in create.quests if q.title == "The Factory Runs Itself")

    assert belt.dependencies[0].quest_id == processing.ftb_id
    assert create.quests.index(complete) < len(create.quests) - 1
    assert len(create.quests) == 74


def test_create_logistics_and_trains_follow_automation() -> None:
    project = create_project()
    create = project.get_chapter("04_create")

    assert create is not None
    automation = next(q for q in create.quests if q.title == "The Factory Runs Itself")
    redstone_link = next(q for q in create.quests if q.title == "Signals Without Wires")
    railway = next(q for q in create.quests if q.title == "Master of Moving Parts")

    assert redstone_link.dependencies[0].quest_id == automation.ftb_id
    assert railway.ftb_id == create.quests[-1].ftb_id
    assert len(create.quests) == 74


def test_actually_additions_depends_on_create_completion() -> None:
    project = create_project()
    create = project.get_chapter("04_create")
    actually = project.get_chapter("05_actually_additions")

    assert create is not None
    assert actually is not None
    assert actually.quests[0].dependencies[0].quest_id == create.quests[-1].ftb_id
    assert len(actually.quests) == 21
    assert actually.quests[-1].title == "A Reconstructed Workshop"
