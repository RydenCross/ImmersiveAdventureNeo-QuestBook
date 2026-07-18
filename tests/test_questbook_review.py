from dataclasses import replace
from pathlib import Path

from generator.modpack_content_scanner_contract import _synthetic_pack
from generator.progression_planner import generate_quest_blueprint
from generator.questbook_review import review_modpack_questbook, review_quest_blueprint


def test_reviews_generated_blueprint_and_flags_editorial_work(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)

    result = review_modpack_questbook(pack, target_quests=4, chapter_size=10)

    assert result.is_clean
    assert not result.publish_ready
    assert result.quests == 4
    assert result.missing_reward_decisions == 4
    assert result.weak_descriptions == 0
    assert {finding.code for finding in result.findings} >= {
        "MISSING_REWARD_DECISIONS",
    }


def test_review_detects_dangling_dependency_and_duplicate_objective(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
    chapter = blueprint.chapters[0]
    quests = list(chapter.quests)
    quests[0] = replace(quests[0], prerequisite_quests=("missing__quest",))
    quests[1] = replace(quests[1], objective=quests[0].objective)
    broken = replace(blueprint, chapters=(replace(chapter, quests=tuple(quests)),))

    result = review_quest_blueprint(broken)

    assert not result.is_clean
    assert result.duplicate_objectives == 1
    assert {finding.code for finding in result.findings} >= {
        "DANGLING_DEPENDENCY",
        "DUPLICATE_OBJECTIVE",
    }


def test_review_detects_chapter_size_and_bottleneck(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
    chapter = blueprint.chapters[0]
    quests = list(chapter.quests)
    root = quests[0].quest_id
    quests = [quests[0], *(replace(quest, prerequisite_quests=(root,)) for quest in quests[1:])]
    changed = replace(blueprint, chapters=(replace(chapter, quests=tuple(quests)),))

    result = review_quest_blueprint(
        changed,
        max_chapter_quests=3,
        bottleneck_dependents=2,
    )

    assert result.oversized_chapters == 1
    assert result.bottleneck_quests == 1
    assert result.maximum_depth == 1


def test_review_is_deterministic_and_rejects_invalid_limits(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)

    first = review_quest_blueprint(blueprint)
    second = review_quest_blueprint(blueprint)
    invalid = review_quest_blueprint(
        blueprint,
        low_confidence_threshold=2.0,
        min_description_words=0,
        max_chapter_quests=0,
        bottleneck_dependents=0,
    )

    assert first.format_json() == second.format_json()
    assert not invalid.is_clean
    assert len(invalid.errors) == 4
