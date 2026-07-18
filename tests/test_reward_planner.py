from dataclasses import replace
from pathlib import Path

from generator.ftb_blueprint_exporter import blueprint_to_project
from generator.modpack_content_scanner_contract import _synthetic_pack
from generator.progression_planner import generate_quest_blueprint
from generator.questbook_review import review_quest_blueprint
from generator.reward_planner import plan_quest_rewards


def test_conservative_reward_plan_resolves_every_decision(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)

    plan = plan_quest_rewards(blueprint, policy="conservative")
    assert plan.is_clean
    assert plan.decisions_complete
    assert plan.rewarded_quests == 2
    assert plan.explicit_no_reward_quests == 2
    assert review_quest_blueprint(plan.blueprint).missing_reward_decisions == 0


def test_reward_policies_scale_and_are_deterministic(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)

    conservative = plan_quest_rewards(blueprint, policy="conservative")
    balanced = plan_quest_rewards(blueprint, policy="balanced")
    generous = plan_quest_rewards(blueprint, policy="generous")
    repeat = plan_quest_rewards(blueprint, policy="conservative")

    assert conservative.rewarded_quests <= balanced.rewarded_quests <= generous.rewarded_quests
    assert generous.rewarded_quests > conservative.rewarded_quests
    assert conservative.format_json() == repeat.format_json()


def test_low_confidence_quests_are_not_automatically_rewarded(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
    chapter = blueprint.chapters[0]
    changed = replace(chapter.quests[0], confidence=0.5, review_required=True)
    blueprint = replace(
        blueprint,
        chapters=(replace(chapter, quests=(changed, *chapter.quests[1:])),),
    )

    plan = plan_quest_rewards(blueprint, policy="generous")
    first = plan.blueprint.chapters[0].quests[0]
    assert first.reward_decision == "none"
    assert first.rewards == ()


def test_rewarded_blueprint_exports_ftb_item_rewards(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
    plan = plan_quest_rewards(blueprint, policy="conservative")

    project = blueprint_to_project(plan.blueprint)
    rewards = [reward for quest in project.quests for reward in quest.rewards]
    assert len(rewards) == plan.reward_count
    assert all(reward.data["item"]["id"].startswith("minecraft:") for reward in rewards)


def test_invalid_reward_policy_fails_cleanly(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)

    plan = plan_quest_rewards(blueprint, policy="invalid")
    assert not plan.is_clean
    assert plan.errors
