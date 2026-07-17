from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from generator.ids import UUIDService
from model import (
    Chapter,
    Dependency,
    Position,
    Project,
    Quest,
    Reward,
    RewardType,
    Task,
    TaskType,
)


def _ftb_id(value: int) -> str:
    return f"{value & ((1 << 64) - 1):016X}"


@dataclass(slots=True)
class QuestBuilder:
    chapter: Chapter
    slug: str
    title: str
    icon: str
    description: str
    position: Position
    ids: UUIDService
    dependencies: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    rewards: list[Reward] = field(default_factory=list)
    optional: bool = False

    @property
    def quest_id(self) -> str:
        return _ftb_id(self.ids.quest(self.slug).int)

    def depends_on(self, *quest_ids: str) -> "QuestBuilder":
        self.dependencies.extend(quest_ids)
        return self

    def checkmark(self) -> "QuestBuilder":
        self.tasks.append(self._task(TaskType.CHECKMARK))
        return self

    def item(self, item_id: str, count: int = 1) -> "QuestBuilder":
        self.tasks.append(
            self._task(TaskType.ITEM, item={"id": item_id, "count": 1}, count=count)
        )
        return self

    def advancement(self, advancement_id: str) -> "QuestBuilder":
        self.tasks.append(
            self._task(TaskType.ADVANCEMENT, advancement=advancement_id, criterion="")
        )
        return self

    def reward_item(self, item_id: str, count: int = 1) -> "QuestBuilder":
        reward_slug = f"{self.slug}:reward:{len(self.rewards)}"
        reward_id = _ftb_id(self.ids.reward(self.slug, reward_slug).int)
        self.rewards.append(
            Reward(
                id=reward_id,
                type=RewardType.ITEM,
                data={"item": {"id": item_id, "count": 1}, "count": count},
            )
        )
        return self

    def finish(self) -> str:
        quest_uuid = self.ids.quest(self.slug)
        quest = Quest(
            id=self.quest_id,
            uuid=quest_uuid,
            ftb_id=self.quest_id,
            title=self.title,
            description=self.description,
            icon=self.icon,
            tasks=self.tasks,
            rewards=self.rewards,
            dependencies=[Dependency(value) for value in self.dependencies],
            position=self.position,
            optional=self.optional,
        )
        self.chapter.add_quest(quest)
        return self.quest_id

    def _task(self, task_type: TaskType, **data: Any) -> Task:
        task_slug = f"{self.slug}:task:{len(self.tasks)}"
        task_id = _ftb_id(self.ids.task(self.slug, task_slug).int)
        return Task(id=task_id, type=task_type, data=data)


@dataclass(slots=True)
class ChapterBuilder:
    project: Project
    slug: str
    title: str
    icon: str
    description: str = ""
    ids: UUIDService = field(default_factory=UUIDService)
    chapter: Chapter = field(init=False)

    def __post_init__(self) -> None:
        chapter_uuid = self.ids.chapter(self.slug)
        self.chapter = Chapter(
            id=self.slug,
            uuid=chapter_uuid,
            ftb_id=_ftb_id(chapter_uuid.int),
            title=self.title,
            icon=self.icon,
            description=self.description,
            raw_data={"order_index": len(self.project.chapters), "quest_links": []},
        )
        self.project.add_chapter(self.chapter)

    def quest(
        self,
        slug: str,
        title: str,
        icon: str,
        description: str,
        x: float,
        y: float,
        *,
        optional: bool = False,
    ) -> QuestBuilder:
        return QuestBuilder(
            chapter=self.chapter,
            slug=f"{self.slug}/{slug}",
            title=title,
            icon=icon,
            description=description,
            position=Position(x, y),
            ids=self.ids,
            optional=optional,
        )
