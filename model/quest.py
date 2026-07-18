from dataclasses import dataclass, field
from typing import Any
from uuid import UUID
from model.dependency import Dependency
from model.enums import Difficulty
from model.position import Position
from model.reward import Reward
from model.task import Task


@dataclass(slots=True)
class Quest:
    id: str
    uuid: UUID
    title: str
    description: str
    icon: str
    tasks: list[Task] = field(default_factory=list)
    rewards: list[Reward] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    position: Position = field(default_factory=Position)
    difficulty: Difficulty = Difficulty.NORMAL
    tags: list[str] = field(default_factory=list)
    hidden: bool = False
    repeatable: bool = False
    optional: bool = False
    ftb_id: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Quest id cannot be empty.")
        if not self.title.strip():
            raise ValueError("Quest title cannot be empty.")
        if not self.icon.strip():
            raise ValueError("Quest icon cannot be empty.")
        if not isinstance(self.difficulty, Difficulty):
            self.difficulty = Difficulty(self.difficulty)

    def depends_on(self, quest_id: str) -> bool:
        return any(dep.quest_id == quest_id for dep in self.dependencies)
