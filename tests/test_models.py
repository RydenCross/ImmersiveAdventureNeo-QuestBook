from uuid import uuid4
import pytest
from generator.ids import UUIDService
from model import Chapter, Dependency, Difficulty, Position, Project, Quest, Reward, RewardType, Task, TaskType

def make_quest(quest_id: str = "W001") -> Quest:
    return Quest(
        id=quest_id,
        uuid=uuid4(),
        title="Welcome",
        description="Begin your adventure.",
        icon="minecraft:book",
        tasks=[Task(id="task_1", type=TaskType.CHECKMARK)],
        rewards=[Reward(id="reward_1", type=RewardType.ITEM, data={"item": "minecraft:bread", "count": 16})],
        position=Position(0, 0),
        difficulty=Difficulty.TRIVIAL,
    )

def test_project_can_find_quest() -> None:
    chapter = Chapter(id="welcome", uuid=uuid4(), title="Welcome", icon="minecraft:book")
    chapter.add_quest(make_quest())
    project = Project(name="Immersive Adventure Neo", version="0.1.0")
    project.add_chapter(chapter)
    assert project.get_quest("W001") is not None
    assert len(project.quests) == 1

def test_duplicate_chapter_is_rejected() -> None:
    project = Project(name="Test", version="0.1.0")
    chapter = Chapter("welcome", uuid4(), "Welcome", "minecraft:book")
    project.add_chapter(chapter)
    with pytest.raises(ValueError, match="Duplicate chapter id"):
        project.add_chapter(chapter)

def test_duplicate_quest_is_rejected() -> None:
    chapter = Chapter("welcome", uuid4(), "Welcome", "minecraft:book")
    chapter.add_quest(make_quest())
    with pytest.raises(ValueError, match="Duplicate quest id"):
        chapter.add_quest(make_quest())

def test_dependency_lookup() -> None:
    quest = make_quest("W002")
    quest.dependencies.append(Dependency("W001"))
    assert quest.depends_on("W001")
    assert not quest.depends_on("W999")

def test_uuid_service_is_deterministic() -> None:
    service = UUIDService()
    assert service.quest("W001") == service.quest("W001")
    assert service.quest("W001") != service.quest("W002")

def test_position_moved_returns_new_position() -> None:
    original = Position(1, 2)
    moved = original.moved(dx=3, dy=-1)
    assert original == Position(1, 2)
    assert moved == Position(4, 1)
