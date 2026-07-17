from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import re

from content import create_project
from model import Project
from model.enums import RewardType

_RESOURCE_LOCATION = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")


@dataclass(frozen=True, slots=True)
class RewardAudit:
    reward_count: int
    rewarded_quests: int
    reward_types: Counter[str]
    duplicate_reward_ids: tuple[str, ...]
    invalid_rewards: tuple[str, ...]
    rewardless_terminal_quests: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.duplicate_reward_ids and not self.invalid_rewards

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "reward_count": self.reward_count,
            "rewarded_quests": self.rewarded_quests,
            "reward_types": dict(sorted(self.reward_types.items())),
            "duplicate_reward_ids": list(self.duplicate_reward_ids),
            "invalid_rewards": list(self.invalid_rewards),
            "rewardless_terminal_quests": list(self.rewardless_terminal_quests),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        reward_summary = ", ".join(
            f"{name}={count}" for name, count in sorted(self.reward_types.items())
        ) or "none"
        lines = [
            f"Reward integrity audit: {'PASS' if self.is_clean else 'FAIL'}",
            f"Rewards: {self.reward_count} across {self.rewarded_quests} quest(s).",
            f"Reward types: {reward_summary}.",
            f"Duplicate reward IDs: {len(self.duplicate_reward_ids)}.",
            f"Invalid reward definitions: {len(self.invalid_rewards)}.",
            f"Rewardless terminal quests: {len(self.rewardless_terminal_quests)} (informational).",
        ]
        lines.extend(f"Duplicate reward ID: {value}" for value in self.duplicate_reward_ids)
        lines.extend(f"Invalid reward: {value}" for value in self.invalid_rewards)
        return "\n".join(lines)


def _item_reward_error(quest_id: str, reward: object) -> str | None:
    item = reward.data.get("item")
    if not isinstance(item, dict):
        return f"{quest_id}/{reward.id}: item reward is missing an item object"
    item_id = item.get("id")
    if not isinstance(item_id, str) or not _RESOURCE_LOCATION.fullmatch(item_id):
        return f"{quest_id}/{reward.id}: invalid item id {item_id!r}"
    count = reward.data.get("count", item.get("count", 1))
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        return f"{quest_id}/{reward.id}: item count must be a positive integer"
    return None


def audit_rewards(project: Project) -> RewardAudit:
    reward_ids: defaultdict[str, list[str]] = defaultdict(list)
    invalid: list[str] = []
    reward_types: Counter[str] = Counter()
    rewarded_quests = 0

    dependants: Counter[str] = Counter(
        dependency.quest_id
        for quest in project.quests
        for dependency in quest.dependencies
    )

    for quest in project.quests:
        if quest.rewards:
            rewarded_quests += 1
        for reward in quest.rewards:
            reward_ids[reward.id].append(quest.id)
            reward_types[reward.type.value] += 1
            if reward.type is RewardType.ITEM:
                error = _item_reward_error(quest.id, reward)
                if error:
                    invalid.append(error)
            elif not reward.data:
                invalid.append(f"{quest.id}/{reward.id}: {reward.type.value} reward has no data")

    duplicates = tuple(
        sorted(
            f"{reward_id} ({', '.join(sorted(quest_ids))})"
            for reward_id, quest_ids in reward_ids.items()
            if len(quest_ids) > 1
        )
    )
    rewardless_terminal = tuple(
        sorted(
            quest.id
            for quest in project.quests
            if dependants[quest.id] == 0 and not quest.rewards
        )
    )

    return RewardAudit(
        reward_count=sum(reward_types.values()),
        rewarded_quests=rewarded_quests,
        reward_types=reward_types,
        duplicate_reward_ids=duplicates,
        invalid_rewards=tuple(sorted(invalid)),
        rewardless_terminal_quests=rewardless_terminal,
    )


def run_reward_audit() -> RewardAudit:
    return audit_rewards(create_project())
