from dataclasses import replace
from pathlib import Path

from generator.modpack_content_scanner_contract import _synthetic_pack
from generator.progression_planner import generate_quest_blueprint
from generator.quest_description_generator import plan_quest_descriptions
from generator.questbook_review import review_quest_blueprint


def test_guided_descriptions_resolve_weak_generated_copy(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)

    result = plan_quest_descriptions(blueprint, style="guided")
    assert result.is_clean
    assert result.generated_descriptions == 4
    assert result.minimum_words >= 24
    assert review_quest_blueprint(result.blueprint).weak_descriptions == 0


def test_recipe_descriptions_include_known_prerequisites(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)

    result = plan_quest_descriptions(blueprint, style="guided")
    machine = next(
        quest
        for chapter in result.blueprint.chapters
        for quest in chapter.quests
        if quest.objective.identifier == "scanner_demo:assembly_machine"
    )
    assert "Copper Gear" in machine.description
    assert "#c:ingots/iron" in machine.description
    assert "modpack" in machine.description.casefold()


def test_detailed_registry_description_requires_review(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
    chapter = blueprint.chapters[0]
    changed = replace(
        chapter.quests[0],
        source_kind="registry",
        confidence=0.55,
        review_required=True,
    )
    blueprint = replace(
        blueprint,
        chapters=(replace(chapter, quests=(changed, *chapter.quests[1:])),),
    )

    result = plan_quest_descriptions(blueprint, style="detailed")
    assert "human reviewer" in result.blueprint.chapters[0].quests[0].description.casefold()


def test_description_styles_scale_and_are_deterministic(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)

    concise = plan_quest_descriptions(blueprint, style="concise")
    guided = plan_quest_descriptions(blueprint, style="guided")
    detailed = plan_quest_descriptions(blueprint, style="detailed")
    repeat = plan_quest_descriptions(blueprint, style="guided")

    assert concise.minimum_words < guided.minimum_words < detailed.minimum_words
    assert guided.format_json() == repeat.format_json()


def test_invalid_description_style_fails_cleanly(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)

    result = plan_quest_descriptions(blueprint, style="invalid")
    assert not result.is_clean
    assert result.errors
