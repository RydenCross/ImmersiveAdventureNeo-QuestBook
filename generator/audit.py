from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from model import Project


@dataclass(frozen=True, slots=True)
class ContentAudit:
    chapters: int
    quests: int
    optional_quests: int
    task_types: Counter[str]
    reward_types: Counter[str]
    empty_descriptions: tuple[str, ...]
    taskless_quests: tuple[str, ...]
    duplicate_titles: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not (self.empty_descriptions or self.taskless_quests)

    def format(self) -> str:
        task_summary = ", ".join(f"{name}={count}" for name, count in sorted(self.task_types.items())) or "none"
        reward_summary = ", ".join(f"{name}={count}" for name, count in sorted(self.reward_types.items())) or "none"
        lines = [
            f"Content audit: {self.chapters} chapter(s), {self.quests} quest(s), {self.optional_quests} optional.",
            f"Tasks: {task_summary}.",
            f"Rewards: {reward_summary}.",
            f"Empty descriptions: {len(self.empty_descriptions)}.",
            f"Taskless quests: {len(self.taskless_quests)}.",
            f"Duplicate titles: {len(self.duplicate_titles)}.",
        ]
        return "\n".join(lines)


def audit_project(project: Project) -> ContentAudit:
    title_counts = Counter(quest.title for quest in project.quests)
    task_types = Counter(task.type.value for quest in project.quests for task in quest.tasks)
    reward_types = Counter(reward.type.value for quest in project.quests for reward in quest.rewards)

    return ContentAudit(
        chapters=len(project.chapters),
        quests=len(project.quests),
        optional_quests=sum(quest.optional for quest in project.quests),
        task_types=task_types,
        reward_types=reward_types,
        empty_descriptions=tuple(quest.title for quest in project.quests if not quest.description.strip()),
        taskless_quests=tuple(quest.title for quest in project.quests if not quest.tasks),
        duplicate_titles=tuple(sorted(title for title, count in title_counts.items() if count > 1)),
    )
