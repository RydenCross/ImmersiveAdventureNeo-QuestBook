from pathlib import Path

from generator.parser import FTBQuestParser
from generator.snbt import loads
from generator.writer import FTBQuestWriter, dumps

FIXTURE = Path(__file__).parent / "fixtures" / "ftbquests"


def test_dumps_produces_parseable_snbt() -> None:
    value = {
        "enabled": True,
        "name": "Welcome",
        "position": [0, 1, 2],
        "nested": {"scale": 0.5},
    }
    assert loads(dumps(value)) == value


def test_writer_creates_ftb_quest_tree(tmp_path: Path) -> None:
    project = FTBQuestParser().load(FIXTURE)
    output = FTBQuestWriter().write(project, tmp_path / "ftbquests")

    assert (output / "data.snbt").is_file()
    assert (output / "chapters" / "welcome.snbt").is_file()
    assert (output / "lang" / "en_us.snbt").is_file()


def test_parser_writer_parser_round_trip(tmp_path: Path) -> None:
    parser = FTBQuestParser()
    original = parser.load(FIXTURE)
    output = FTBQuestWriter().write(original, tmp_path / "ftbquests")
    restored = parser.load(output.parent)

    assert restored.version == original.version
    assert len(restored.chapters) == len(original.chapters)
    assert len(restored.quests) == len(original.quests)

    original_chapter = original.chapters[0]
    restored_chapter = restored.chapters[0]
    assert restored_chapter.ftb_id == original_chapter.ftb_id
    assert restored_chapter.title == original_chapter.title

    for before, after in zip(original_chapter.quests, restored_chapter.quests, strict=True):
        assert after.ftb_id == before.ftb_id
        assert after.position == before.position
        assert [task.type for task in after.tasks] == [task.type for task in before.tasks]
        assert [reward.type for reward in after.rewards] == [
            reward.type for reward in before.rewards
        ]
        assert after.dependencies == before.dependencies
