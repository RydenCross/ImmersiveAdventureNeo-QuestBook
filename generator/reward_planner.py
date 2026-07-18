from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path

from generator.quest_description_generator import generate_quest_description_plan
from generator.progression_planner import (
    BlueprintChapter,
    BlueprintQuest,
    BlueprintReward,
    QuestBlueprint,
)

REWARD_POLICIES = ("none", "conservative", "balanced", "generous")

_POLICY_INTERVALS = {
    "none": 0,
    "conservative": 0,
    "balanced": 5,
    "generous": 3,
}

_POLICY_BOTTLENECKS = {
    "none": 10_000,
    "conservative": 4,
    "balanced": 3,
    "generous": 2,
}

_REWARD_PALETTES = {
    "conservative": (
        ("minecraft:experience_bottle", 1),
        ("minecraft:bread", 4),
        ("minecraft:torch", 8),
    ),
    "balanced": (
        ("minecraft:experience_bottle", 2),
        ("minecraft:bread", 6),
        ("minecraft:torch", 16),
    ),
    "generous": (
        ("minecraft:experience_bottle", 4),
        ("minecraft:bread", 8),
        ("minecraft:torch", 24),
    ),
}


@dataclass(frozen=True, slots=True)
class QuestRewardPlan:
    policy: str
    blueprint: QuestBlueprint
    rewarded_quests: int
    explicit_no_reward_quests: int
    reward_count: int
    reward_items: tuple[tuple[str, int], ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def decisions_complete(self) -> bool:
        return all(
            quest.reward_decision in {"rewarded", "none"}
            for chapter in self.blueprint.chapters
            for quest in chapter.quests
        )

    @property
    def is_clean(self) -> bool:
        return self.blueprint.is_clean and not self.errors and self.decisions_complete

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "policy": self.policy,
            "summary": {
                "quests": self.blueprint.quest_count,
                "rewarded_quests": self.rewarded_quests,
                "explicit_no_reward_quests": self.explicit_no_reward_quests,
                "reward_count": self.reward_count,
                "decisions_complete": self.decisions_complete,
            },
            "reward_items": [
                {"item": item_id, "total_count": count}
                for item_id, count in self.reward_items
            ],
            "blueprint": self.blueprint.to_dict(),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Quest reward plan: {'PASS' if self.is_clean else 'FAIL'}",
            f"Policy: {self.policy}.",
            f"Quests: {self.blueprint.quest_count}.",
            f"Rewarded quests: {self.rewarded_quests}.",
            f"Explicit no-reward quests: {self.explicit_no_reward_quests}.",
            f"Rewards: {self.reward_count}.",
            f"Decisions complete: {'yes' if self.decisions_complete else 'no'}.",
        ]
        lines.extend(f"Reward item: {item_id} x{count}." for item_id, count in self.reward_items)
        lines.extend(f"Warning: {warning}" for warning in self.warnings)
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


def _flatten(blueprint: QuestBlueprint) -> tuple[tuple[BlueprintChapter, BlueprintQuest], ...]:
    return tuple(
        (chapter, quest)
        for chapter in blueprint.chapters
        for quest in chapter.quests
    )


def _reward_for(quest: BlueprintQuest, policy: str, reason: str) -> BlueprintReward:
    palette = _REWARD_PALETTES[policy]
    digest = hashlib.sha256(quest.quest_id.encode("utf-8")).digest()
    item_id, count = palette[digest[0] % len(palette)]
    if item_id == quest.objective.identifier:
        item_id, count = palette[(digest[0] + 1) % len(palette)]
    return BlueprintReward(
        reward_type="item",
        identifier=item_id,
        count=count,
        reason=reason,
    )


def _decision_reason(
    *,
    policy: str,
    quest: BlueprintQuest,
    index: int,
    is_root: bool,
    is_terminal: bool,
    dependent_count: int,
) -> str | None:
    if policy == "none":
        return None
    if quest.review_required or quest.confidence < 0.75:
        return None
    if is_terminal:
        return "chapter or progression terminal milestone"
    if dependent_count >= _POLICY_BOTTLENECKS[policy]:
        return f"progression milestone gating {dependent_count} quests"
    if policy == "generous" and is_root:
        return "chapter entry milestone"
    interval = _POLICY_INTERVALS[policy]
    if interval and (index + 1) % interval == 0:
        return f"scheduled {policy} progression milestone"
    return None


def plan_quest_rewards(
    blueprint: QuestBlueprint,
    *,
    policy: str = "conservative",
) -> QuestRewardPlan:
    if policy not in REWARD_POLICIES:
        return QuestRewardPlan(
            policy=policy,
            blueprint=blueprint,
            rewarded_quests=0,
            explicit_no_reward_quests=0,
            reward_count=0,
            reward_items=(),
            warnings=(),
            errors=(
                f"reward policy must be one of: {', '.join(REWARD_POLICIES)}",
            ),
        )

    rows = _flatten(blueprint)
    dependents = {quest.quest_id: 0 for _, quest in rows}
    for _, quest in rows:
        for dependency in quest.prerequisite_quests:
            if dependency in dependents:
                dependents[dependency] += 1

    chapter_quests: dict[str, tuple[str, ...]] = {
        chapter.chapter_id: tuple(quest.quest_id for quest in chapter.quests)
        for chapter in blueprint.chapters
    }
    updated_chapters: list[BlueprintChapter] = []
    reward_totals: dict[str, int] = {}
    rewarded_quests = 0
    explicit_none = 0

    for chapter in blueprint.chapters:
        quest_ids = set(chapter_quests[chapter.chapter_id])
        updated_quests: list[BlueprintQuest] = []
        for index, quest in enumerate(chapter.quests):
            local_dependents = sum(
                1
                for other in chapter.quests
                if quest.quest_id in other.prerequisite_quests
            )
            is_root = not any(
                dependency in quest_ids for dependency in quest.prerequisite_quests
            )
            is_terminal = local_dependents == 0
            reason = _decision_reason(
                policy=policy,
                quest=quest,
                index=index,
                is_root=is_root,
                is_terminal=is_terminal,
                dependent_count=dependents.get(quest.quest_id, 0),
            )
            if reason is None:
                explicit_none += 1
                updated_quests.append(replace(
                    quest,
                    reward_decision="none",
                    rewards=(),
                ))
                continue
            reward = _reward_for(quest, policy, reason)
            rewarded_quests += 1
            reward_totals[reward.identifier] = reward_totals.get(reward.identifier, 0) + reward.count
            updated_quests.append(replace(
                quest,
                reward_decision="rewarded",
                rewards=(reward,),
            ))
        updated_chapters.append(replace(chapter, quests=tuple(updated_quests)))

    rewarded_blueprint = replace(blueprint, chapters=tuple(updated_chapters))
    warnings = list(blueprint.warnings)
    if policy != "none" and rewarded_quests == 0 and rewarded_blueprint.quest_count:
        warnings.append(
            "No quests qualified for automatic rewards; all quests were explicitly marked no-reward."
        )
    return QuestRewardPlan(
        policy=policy,
        blueprint=rewarded_blueprint,
        rewarded_quests=rewarded_quests,
        explicit_no_reward_quests=explicit_none,
        reward_count=rewarded_quests,
        reward_items=tuple(sorted(reward_totals.items())),
        warnings=tuple(sorted(set(warnings))),
        errors=(),
    )


def generate_quest_reward_plan(
    source: Path,
    *,
    target_quests: int | None = None,
    chapter_size: int = 40,
    policy: str = "conservative",
    description_style: str = "guided",
) -> QuestRewardPlan:
    description_plan = generate_quest_description_plan(
        source,
        target_quests=target_quests,
        chapter_size=chapter_size,
        style=description_style,
    )
    if not description_plan.is_clean:
        return QuestRewardPlan(
            policy=policy,
            blueprint=description_plan.blueprint,
            rewarded_quests=0,
            explicit_no_reward_quests=0,
            reward_count=0,
            reward_items=(),
            warnings=description_plan.warnings,
            errors=description_plan.errors,
        )
    return plan_quest_rewards(description_plan.blueprint, policy=policy)
