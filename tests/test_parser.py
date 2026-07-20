from pathlib import Path
from generator.parser import FTBQuestParser
from model.enums import RewardType, TaskType

FIXTURE = Path(__file__).parent / "fixtures" / "ftbquests"


def test_loads_uploaded_ftbquests_v13_scaffold() -> None:
    project = FTBQuestParser().load(FIXTURE)
    assert project.version == "13"
    assert len(project.chapters) == 1
    chapter = project.chapters[0]
    assert chapter.id == "welcome"
    assert chapter.title == "Welcome"
    assert chapter.ftb_id == "1B973F7802646735"
    assert len(chapter.quests) == 5


def test_parses_all_sample_task_types_and_reward() -> None:
    project = FTBQuestParser().load(FIXTURE)
    task_types = {task.type for quest in project.quests for task in quest.tasks}
    reward_types = {reward.type for quest in project.quests for reward in quest.rewards}
    assert {
        TaskType.CHECKMARK,
        TaskType.KILL,
        TaskType.ITEM,
        TaskType.LOCATION,
        TaskType.ADVANCEMENT,
    } <= task_types
    assert RewardType.ITEM in reward_types


def test_preserves_unknown_task_payload() -> None:
    project = FTBQuestParser().load(FIXTURE)
    checkmark = next(
        task for quest in project.quests for task in quest.tasks if task.type is TaskType.CHECKMARK
    )
    assert "Reskillable" in checkmark.data
    assert checkmark.raw_data["type"] == "checkmark"
