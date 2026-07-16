from dataclasses import dataclass, field
from typing import Any
from model.enums import RewardType

@dataclass(slots=True)
class Reward:
    id: str
    type: RewardType
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Reward id cannot be empty.")
        if not isinstance(self.type, RewardType):
            self.type = RewardType(self.type)
