from dataclasses import dataclass, field
from typing import Any
from uuid import UUID
from model.quest import Quest

@dataclass(slots=True)
class Chapter:
    id: str
    uuid: UUID
    title: str
    icon: str
    quests: list[Quest] = field(default_factory=list)
    group: str | None = None
    background: str | None = None
    color: str | None = None
    description: str = ""
    ftb_id: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not self.id.strip(): raise ValueError("Chapter id cannot be empty.")
        if not self.title.strip(): raise ValueError("Chapter title cannot be empty.")
        if not self.icon.strip(): raise ValueError("Chapter icon cannot be empty.")

    def add_quest(self, quest: Quest) -> None:
        if self.get_quest(quest.id) is not None:
            raise ValueError(f"Duplicate quest id in chapter {self.id}: {quest.id}")
        self.quests.append(quest)

    def get_quest(self, quest_id: str) -> Quest | None:
        return next((q for q in self.quests if q.id == quest_id), None)
