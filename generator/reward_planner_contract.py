from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.ftb_blueprint_exporter import blueprint_to_project
from generator.modpack_content_scanner_contract import _synthetic_pack
from generator.progression_planner import generate_quest_blueprint
from generator.questbook_review import review_quest_blueprint
from generator.reward_audit import audit_rewards
from generator.reward_planner import plan_quest_rewards


@dataclass(frozen=True, slots=True)
class RewardPlannerContract:
    decisions_complete: bool
    conservative_sparse: bool
    policy_scaling: bool
    low_confidence_protected: bool
    review_decisions_resolved: bool
    export_round_trip_valid: bool
    deterministic_output: bool
    invalid_policy_rejected: bool

    @property
    def is_clean(self) -> bool:
        return all((
            self.decisions_complete,
            self.conservative_sparse,
            self.policy_scaling,
            self.low_confidence_protected,
            self.review_decisions_resolved,
            self.export_round_trip_valid,
            self.deterministic_output,
            self.invalid_policy_rejected,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "decisions_complete": self.decisions_complete,
            "conservative_sparse": self.conservative_sparse,
            "policy_scaling": self.policy_scaling,
            "low_confidence_protected": self.low_confidence_protected,
            "review_decisions_resolved": self.review_decisions_resolved,
            "export_round_trip_valid": self.export_round_trip_valid,
            "deterministic_output": self.deterministic_output,
            "invalid_policy_rejected": self.invalid_policy_rejected,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Reward planner contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Decisions complete: {'yes' if self.decisions_complete else 'no'}.",
            f"Conservative policy sparse: {'yes' if self.conservative_sparse else 'no'}.",
            f"Policy scaling valid: {'yes' if self.policy_scaling else 'no'}.",
            f"Low-confidence quests protected: {'yes' if self.low_confidence_protected else 'no'}.",
            f"Review decisions resolved: {'yes' if self.review_decisions_resolved else 'no'}.",
            f"Export round trip valid: {'yes' if self.export_round_trip_valid else 'no'}.",
            f"Deterministic output: {'yes' if self.deterministic_output else 'no'}.",
            f"Invalid policy rejected: {'yes' if self.invalid_policy_rejected else 'no'}.",
        ))


def run_reward_planner_contract() -> RewardPlannerContract:
    with TemporaryDirectory(prefix="reward-planner-contract-") as temporary:
        pack = Path(temporary) / "reward-plan.mrpack"
        _synthetic_pack(pack)
        blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
        conservative = plan_quest_rewards(blueprint, policy="conservative")
        conservative_repeat = plan_quest_rewards(blueprint, policy="conservative")
        balanced = plan_quest_rewards(blueprint, policy="balanced")
        generous = plan_quest_rewards(blueprint, policy="generous")
        invalid = plan_quest_rewards(blueprint, policy="unknown")

        chapter = blueprint.chapters[0]
        low_confidence_quest = replace(
            chapter.quests[0], confidence=0.5, review_required=True
        )
        low_confidence_blueprint = replace(
            blueprint,
            chapters=(replace(
                chapter,
                quests=(low_confidence_quest, *chapter.quests[1:]),
            ),),
        )
        protected = plan_quest_rewards(low_confidence_blueprint, policy="generous")
        protected_first = protected.blueprint.chapters[0].quests[0]

        project = blueprint_to_project(conservative.blueprint)
        reward_audit = audit_rewards(project)
        review = review_quest_blueprint(conservative.blueprint)
        exported_rewards = sum(len(quest.rewards) for quest in project.quests)

        return RewardPlannerContract(
            decisions_complete=conservative.decisions_complete
            and conservative.rewarded_quests + conservative.explicit_no_reward_quests
            == blueprint.quest_count,
            conservative_sparse=0 < conservative.rewarded_quests < blueprint.quest_count,
            policy_scaling=(
                conservative.rewarded_quests <= balanced.rewarded_quests
                <= generous.rewarded_quests
                and generous.rewarded_quests > conservative.rewarded_quests
            ),
            low_confidence_protected=(
                protected_first.reward_decision == "none"
                and not protected_first.rewards
            ),
            review_decisions_resolved=review.missing_reward_decisions == 0,
            export_round_trip_valid=(
                reward_audit.is_clean
                and exported_rewards == conservative.reward_count
            ),
            deterministic_output=(
                conservative.format_json() == conservative_repeat.format_json()
            ),
            invalid_policy_rejected=not invalid.is_clean and bool(invalid.errors),
        )
